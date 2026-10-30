"""The Codex watcher: room mail addressed to the Codex account becomes a Codex turn.

Codex has no hook that can block and then hand it a message, so a
long-running process does it: the shared sync loop for the Codex account, and
``codex queue`` for each batch of mail. The thread comes from ``--thread``
(one room, the project of the working directory) or from the zmx session that
zmx-peer-chat's launcher registered for the room's directory. The watcher
never starts, registers, types into or kills a session.
"""

from __future__ import annotations

import math
import os
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from .config import AgentChatError, Config
from .listen import SyncLoop, timeline
from .matrix import AuthError, Client, MatrixError
from .note import CODEX_REPLY, Message, render
from .room import Rooms, alias_slug, project_alias, read_json

CODEX_ENV = "AGENT_CHAT_CODEX"
ZMX_ENV = "AGENT_CHAT_ZMX"
# How often the watcher joins the rooms of newly registered Codex sessions.
SWEEP_SECONDS = 300.0
# The longest pause between attempts after a failed sync.
RETRY_MAX = 60.0
# zmx's own `zmx ls` fields; any other key=value field is a label.
_BUILTIN = {"name", "pid", "clients", "created", "cwd", "cmd"}
ROLE, THREAD = "zpc.role", "zpc.thread"
_UUID = re.compile(r"[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}")


class Stopped(BaseException):
    """SIGTERM or SIGINT arrived while the watcher waited on a sync."""


def check_thread(thread: str) -> str:
    """Return ``thread`` if it is a Codex thread UUID."""
    if not _UUID.fullmatch(thread):
        raise AgentChatError(f"bad Codex thread id {thread!r} (a UUID)", 2)
    return thread


@dataclass
class Session:
    """One zmx session as ``zmx ls`` reports it."""

    name: str
    cwd: str | None = None
    labels: dict[str, str] = field(default_factory=dict)


def parse_ls(text: str) -> list[Session]:
    """Parse ``zmx ls``: tab-separated ``key=value`` fields from ``name=`` on.

    ``cwd`` is a ``file://`` URL; it comes back as a path.
    """
    sessions = []
    for line in text.splitlines():
        if not line.strip():
            continue
        start = line.find("name=")
        if start < 0:
            raise AgentChatError(f"unexpected zmx ls line: {line!r}")
        fields = dict(
            part.split("=", 1) for part in line[start:].split("\t") if "=" in part
        )
        cwd = fields.get("cwd") or None
        if cwd and cwd.startswith("file:"):
            cwd = unquote(urlsplit(cwd).path) or None
        labels = {k: v for k, v in fields.items() if k not in _BUILTIN}
        sessions.append(Session(fields["name"], cwd, labels))
    return sessions


def _command(env: str, default: str) -> list[str]:
    return (os.environ.get(env) or default).split()


def zmx_sessions() -> list[Session]:
    """Return the live zmx sessions (``AGENT_CHAT_ZMX`` overrides the binary)."""
    try:
        done = subprocess.run(
            [*_command(ZMX_ENV, "zmx"), "ls"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AgentChatError(f"zmx ls failed: {exc}") from exc
    if done.returncode != 0:
        why = done.stderr.strip() or f"exit {done.returncode}"
        raise AgentChatError(f"zmx ls failed: {why}")
    return parse_ls(done.stdout)


def codex_queue(thread: str, text: str) -> None:
    """Queue ``text`` as the next turn of Codex thread ``thread``.

    ``AGENT_CHAT_CODEX`` overrides the binary, for a supervisor whose PATH
    lacks it.
    """
    argv = [*_command(CODEX_ENV, "codex"), "queue", "--thread", thread]
    try:
        done = subprocess.run(
            [*argv, "--message", text], capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AgentChatError(f"codex queue failed: {exc}") from exc
    if done.returncode != 0:
        why = done.stderr.strip().splitlines()[-1:] or [f"exit {done.returncode}"]
        raise AgentChatError(f"codex queue failed: {why[0]}")


def room_dir(alias: str, cfg: Config) -> str | None:
    """Return the directory name an agent room's alias names, else None."""
    local, _, server = alias[1:].partition(":")
    if not alias.startswith("#") or server != cfg.server_name:
        return None
    if not local.startswith(cfg.room_prefix) or local == cfg.room_prefix:
        return None
    return local[len(cfg.room_prefix) :]


def find_thread(
    alias: str, cfg: Config, sessions: list[Session]
) -> tuple[str | None, str]:
    """Return the bound thread of the one Codex session the room names.

    That is the session labelled ``zpc.role=codex`` whose working directory
    has the name the alias carries. Returns ``(None, why)`` when none or
    several match, or the match has no valid ``zpc.thread``.
    """
    name = room_dir(alias, cfg)
    matches = [
        s
        for s in sessions
        if s.labels.get(ROLE) == "codex"
        and s.cwd
        and os.path.basename(os.path.realpath(s.cwd)) == name
    ]
    if not matches:
        return None, f"no registered Codex session works in a directory named {name}"
    if len(matches) > 1:
        names = ", ".join(sorted(s.name for s in matches))
        return None, (
            f"several registered Codex sessions work in a directory named {name} "
            f"({names}); refusing to pick one"
        )
    thread = matches[0].labels.get(THREAD, "")
    if not _UUID.fullmatch(thread):
        return None, f"zmx session {matches[0].name} has no bound Codex thread"
    return thread, ""


class CodexWatcher(SyncLoop):
    """Delivers mail addressed to the Codex account with ``codex queue``.

    Args:
        client: The Codex account's homeserver client.
        cfg: The host's configuration.
        account: The Codex account's full ID.
        state: The account's state directory.
        log: Takes one line per delivery, refusal or failure.
        thread: The one thread to queue to; then only ``alias`` is served.
        alias: The room ``thread`` belongs to.
        sessions: Lists the zmx sessions.
        queue: Queues a text to a thread.
    """

    def __init__(
        self,
        client: Client,
        cfg: Config,
        account: str,
        state: Path,
        log: Callable[[str], None],
        thread: str | None = None,
        alias: str | None = None,
        sessions: Callable[[], list[Session]] = zmx_sessions,
        queue: Callable[[str, str], None] = codex_queue,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        if (thread is None) != (alias is None):
            raise ValueError("thread and alias go together")
        name = "watch-codex" if alias is None else f"watch-codex-{alias_slug(alias)}"
        super().__init__(client, cfg, account, state, name)
        self.lock_name = name
        self.log = log
        self.thread = thread
        self.alias = alias
        self.room: str | None = None
        self.rooms = Rooms(client, cfg, state)
        self.sessions = sessions
        self.queue = queue
        self._now = now
        self._aliases: dict[str, str] = {}
        self._next_sweep = 0.0
        self._in_sync = False
        self.stopping = False

    def request_stop(self) -> None:
        """Stop after the current sync or delivery."""
        self.stopping = True

    def on_signal(self, signum: int, frame: Any) -> None:
        """SIGTERM / SIGINT handler: a waiting sync is abandoned, a delivery finishes.

        The cursor is saved only after a sync returns, so abandoning one loses
        nothing; a delivery in progress runs to its end first.
        """
        self.stopping = True
        if self._in_sync:
            raise Stopped

    def _sync(
        self, since: str | None, filt: str, seconds: float, deadline: float
    ) -> dict[str, Any]:
        self._in_sync = True
        try:
            if self.stopping:
                raise Stopped
            return super()._sync(since, filt, seconds, deadline)
        finally:
            self._in_sync = False

    def _alias_of(self, room: str, deadline: float) -> str | None:
        """Return the alias of joined ``room``: from the room cache, else its state.

        A room without an alias is asked again next time, since onboarding
        may set one later.
        """
        if room in self._aliases:
            return self._aliases[room]
        known = {
            v: k for k, v in read_json(self.rooms.cache).items() if isinstance(v, str)
        }
        alias = known.get(room)
        if alias is None:
            try:
                alias = self.client.canonical_alias(room, deadline)
            except AuthError:
                raise
            except MatrixError as exc:
                self.log(f"cannot read the alias of {room}: {exc}")
        if alias is not None:
            self._aliases[room] = alias
        return alias

    def _served(self, room: str, deadline: float) -> str | None:
        """Return the alias of ``room`` when this watcher serves it."""
        if self.alias is not None:
            return self.alias if room == self.room else None
        alias = self._alias_of(room, deadline)
        return alias if alias and room_dir(alias, self.cfg) else None

    def _deliver(self, alias: str, mail: list[Message]) -> None:
        senders = ", ".join(sorted({m.sender for m in mail}))
        what = f"{len(mail)} message(s) from {senders} in {alias}"
        if self.thread is not None:
            thread, why = self.thread, ""
        else:
            try:
                thread, why = find_thread(alias, self.cfg, self.sessions())
            except AgentChatError as exc:
                thread, why = None, str(exc)
        if thread is None:
            self.log(f"not queued: {what}: {why}")
            return
        text = render(mail, self.cfg, self.account, alias, CODEX_REPLY)
        try:
            self.queue(thread, text)
        except AgentChatError as exc:
            self.log(f"not queued: {what} to thread {thread}: {exc}")
            return
        self.log(f"queued {what} to thread {thread}")

    def _sweep(self, deadline: float) -> None:
        """Join the rooms of registered Codex sessions (all-rooms mode only)."""
        if self.alias is not None or self._now() < self._next_sweep:
            return
        self._next_sweep = self._now() + SWEEP_SECONDS
        try:
            sessions = self.sessions()
        except AgentChatError as exc:
            self.log(f"cannot list the Codex sessions: {exc}")
            return
        for s in sessions:
            if s.labels.get(ROLE) != "codex" or not s.cwd:
                continue
            alias = project_alias(self.cfg, s.cwd)
            try:
                if self.rooms.room_id(alias, deadline) is None:
                    continue  # that project is not onboarded
            except AuthError:
                raise
            except AgentChatError as exc:
                self.log(f"cannot join {alias}: {exc}")

    def _rest(self, seconds: float) -> None:
        end = self._now() + seconds
        while not self.stopping and self._now() < end:
            time.sleep(min(0.2, end - self._now()))

    def run(self) -> int:
        """Serve until stopped; return the exit code.

        Raises:
            AuthError: When the token is refused.
            AgentChatError: When the ``--thread`` room does not exist.
        """
        deadline = math.inf
        self.client.keep_going = lambda: not self.stopping
        if self.alias is not None:
            self.room = self.rooms.room_id(self.alias, deadline)
            if self.room is None:
                raise AgentChatError(
                    f"this project has no room {self.alias} (not onboarded)"
                )
        self.log(
            f"watching {self.alias or 'every agent room'} as {self.account}"
            + (f", queueing to thread {self.thread}" if self.thread else "")
        )
        pause = 1.0
        while not self.stopping:
            try:
                self._sweep(deadline)
                for rooms in self.batches(deadline, lambda: not self.stopping):
                    for room in rooms.get("join") or {}:
                        mail = self.mail(timeline(rooms, room))
                        alias = self._served(room, deadline) if mail else None
                        if alias:
                            self._deliver(alias, mail)
                    pause = 1.0
                    if self.stopping:
                        break
                    self._sweep(deadline)
            except Stopped:
                break
            except AuthError:
                raise
            except AgentChatError as exc:
                if self.stopping:
                    break
                self.log(f"sync failed: {exc}; trying again in {pause:.0f} s")
                self._rest(pause)
                pause = min(pause * 2, RETRY_MAX)
        self.log("stopped; the cursor is saved")
        return 0
