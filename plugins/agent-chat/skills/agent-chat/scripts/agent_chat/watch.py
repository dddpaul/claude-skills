"""The Codex watcher: room mail addressed to the Codex account becomes a Codex turn.

Codex has no hook that can block and then hand it a message, so a
long-running process does it: the shared sync loop for the Codex account, and
``codex queue`` for each batch of mail. The thread comes from ``--thread``
(one room, the project of the working directory) or from the zmx session that
zmx-peer-chat's launcher registered for the room's directory; mail goes to
that session's thread only while its TUI footer shows the thread. The watcher
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
from .listen import HUB_SECONDS, SyncLoop, timeline, write_text
from .matrix import AuthError, Client, MatrixError, NetworkError
from .note import CODEX_REPLY, Message, notes
from .room import Rooms, alias_slug, project_alias, read_json, room_alias
from .threads import Budget

CODEX_ENV = "AGENT_CHAT_CODEX"
ZMX_ENV = "AGENT_CHAT_ZMX"
# The most UTF-8 bytes of one `codex queue --message` text; Linux caps one
# argument at 131072 (MAX_ARG_STRLEN).
QUEUE_BYTES = 100_000
# How long the alias lookup of one room may take within a batch.
ALIAS_SECONDS = 10.0
# How often the watcher joins the rooms of newly registered Codex sessions.
SWEEP_SECONDS = 300.0
# The longest pause between attempts after a failed sync.
RETRY_MAX = 60.0
# zmx's own `zmx ls` fields; any other key=value field is a label.
_BUILTIN = {"name", "pid", "clients", "created", "cwd", "cmd"}
ROLE, THREAD, INC = "zpc.role", "zpc.thread", "zpc.inc"
# How many of the last non-empty screen lines may hold the Codex footer; the
# same rule as zmx-peer-chat's router (zpc/common.py), copied because the
# plugins ship separately.
_FOOTER_LINES = 6
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


def zmx_history(name: str) -> str:
    """Return the plain-text scrollback of zmx session ``name``."""
    try:
        done = subprocess.run(
            [*_command(ZMX_ENV, "zmx"), "history", name],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AgentChatError(f"zmx history {name} failed: {exc}") from exc
    if done.returncode != 0:
        why = done.stderr.strip() or f"exit {done.returncode}"
        raise AgentChatError(f"zmx history {name} failed: {why}")
    return done.stdout


def tui_shows(screen: str, name: str) -> bool:
    """Tell whether the Codex footer at the end of ``screen`` names thread ``name``."""
    lines = [line.rstrip() for line in screen.splitlines() if line.strip()]
    return any(line.endswith(f"· {name}") for line in lines[-_FOOTER_LINES:])


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


def find_session(
    alias: str, cfg: Config, sessions: list[Session]
) -> tuple[Session | None, str]:
    """Return the one bound Codex session the room names.

    That is the session labelled ``zpc.role=codex`` whose working directory
    has the name the alias carries. Returns ``(None, why)`` when none or
    several match, or the match has no valid ``zpc.thread`` or no ``zpc.inc``.
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
    session = matches[0]
    if not _UUID.fullmatch(session.labels.get(THREAD, "")):
        return None, f"zmx session {session.name} has no bound Codex thread"
    if not session.labels.get(INC):
        return None, f"zmx session {session.name} has no {INC} label"
    return session, ""


def check_screen(session: Session, history: Callable[[str], str]) -> str:
    """Return why mail must not go to ``session``'s thread now, else ``""``.

    The TUI must show the thread in its footer: ``/new`` or ``/resume`` move
    it to another thread, and a thread no TUI shows runs headless.
    """
    name = f"zpc-{session.labels[INC]}"
    try:
        screen = history(session.name)
    except AgentChatError as exc:
        return str(exc)
    if tui_shows(screen, name):
        return ""
    return (
        f"the Codex TUI in {session.name} does not show thread {name} (moved by "
        "/new or /resume, or a dialog covers the footer)"
    )


class CodexWatcher(SyncLoop):
    """Delivers mail addressed to the Codex account with ``codex queue``.

    When the config names a hub, the watcher joins it and routes each hub
    message to the session (Codex account, project) it wakes: in all-rooms
    mode to each such project's registered session, with ``--thread`` only
    for the watched project. A failed hub join is logged and tried again at
    the next sweep; it never holds up project-room mail. While a watcher
    that serves the hub runs, ``<lock name>.hub`` in the state directory says
    ``covered`` or ``unavailable: <reason>``.

    Args:
        client: The Codex account's homeserver client.
        cfg: The host's configuration.
        account: The Codex account's full ID.
        state: The account's state directory.
        log: Takes one line per delivery, refusal or failure.
        thread: The one thread to queue to; then only ``alias`` is served,
            and the hub only for its project.
        alias: The room ``thread`` belongs to.
        sessions: Lists the zmx sessions.
        history: Returns the screen of a zmx session.
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
        history: Callable[[str], str] = zmx_history,
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
        self.history = history
        self.queue = queue
        self._now = now
        self._aliases: dict[str, str] = {}
        self.hub_room: str | None = None
        self._hub_down: str | None = None
        project = None if alias is None else room_dir(alias, cfg)
        self.project = None if alias == cfg.hub_alias else project
        serves_hub = cfg.hub_alias is not None and (
            alias is None or self.project is not None
        )
        self.hub_file = state / f"{name}.hub" if serves_hub else None
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

        A room without an alias, or whose alias could not be read, is asked
        again next time, since onboarding may set one later.
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
            except (MatrixError, NetworkError) as exc:
                self.log(
                    f"cannot read the alias of {room}: {exc}; its mail in this "
                    "batch is not delivered"
                )
        if alias is not None:
            self._aliases[room] = alias
        return alias

    def _served(self, room: str, deadline: float) -> str | None:
        """Return the alias of ``room`` when this watcher serves it."""
        if self.alias is not None:
            return self.alias if room == self.room else None
        alias = self._alias_of(room, deadline)
        if alias is None or alias == self.cfg.hub_alias:
            return None
        return alias if room_dir(alias, self.cfg) else None

    def _deliver(self, alias: str, mail: list[Message]) -> None:
        senders = ", ".join(sorted({m.sender for m in mail}))
        where = alias
        if hub := next((m.hub for m in mail if m.hub), None):
            hub_part = f"the hub {self.cfg.hub_alias} for {hub.project}"
            mixed = any(m.hub is None for m in mail)
            where = f"{alias} and {hub_part}" if mixed else hub_part
        what = f"{len(mail)} message(s) from {senders} in {where}"
        thread, why = self.thread, ""
        if thread is None:
            try:
                session, why = find_session(alias, self.cfg, self.sessions())
            except AgentChatError as exc:
                session, why = None, str(exc)
            if session is not None:
                why = check_screen(session, self.history)
                thread = None if why else session.labels[THREAD]
        if thread is None:
            self.log(f"not queued: {what}: {why}")
            return
        texts = notes(mail, self.cfg, self.account, alias, CODEX_REPLY, QUEUE_BYTES)
        n = len(texts)
        for k, text in enumerate(texts, 1):
            try:
                self.queue(thread, text)
            except AgentChatError as exc:
                parts = f" (parts {k}-{n} of {n})" if n > 1 else ""
                self.log(f"not queued: {what} to thread {thread}{parts}: {exc}")
                return
            part = f" (part {k} of {n})" if n > 1 else ""
            self.log(f"queued {what} to thread {thread}{part}")

    def _batch_mail(
        self, rooms: dict[str, Any], deadline: float
    ) -> list[tuple[str, list[Message]]]:
        """Return each served room's alias and mail in one sync's ``rooms``.

        The rooms are checked first and every lookup runs before any delivery,
        so neither an unserved room nor a slow ``codex queue`` spends the
        batch's lookup budget. Each room's alias lookup has its own
        :data:`ALIAS_SECONDS`, so one failing room holds up no other. Hub
        mail joins the mail of the project room it is routed to.
        """
        served = []
        for room in rooms.get("join") or {}:
            if room == self.hub_room:
                continue
            events = timeline(rooms, room)
            if not self.candidates(events):
                continue
            until = min(deadline, self.client.now() + ALIAS_SECONDS)
            if alias := self._served(room, until):
                served.append((room, alias, events))
        budget = self.budget()
        found: dict[str, list[Message]] = {}
        for room, alias, events in served:
            found.setdefault(alias, []).extend(self.mail(room, events, budget))
        for project, m in self._hub_routes(rooms, budget):
            found.setdefault(room_alias(self.cfg, project), []).append(m)
        return [(alias, mail) for alias, mail in found.items() if mail]

    def _hub_routes(
        self, rooms: dict[str, Any], budget: Budget
    ) -> list[tuple[str, Message]]:
        """Return the hub mail of one sync, each message with its project."""
        hub = self.hub_room
        if hub is None:
            return []
        if self._left(hub, rooms):
            self.rooms.forget(str(self.cfg.hub_alias))
            self.hub_room = None
            self._hub_failed("this account left it")
            return []
        if self.alias is not None and self.project is None:
            return []
        projects = None if self.project is None else [self.project]
        return self.hub_routes(hub, timeline(rooms, hub), budget, projects)

    def _report_hub(self, text: str) -> None:
        if self.hub_file is not None:
            write_text(self.hub_file, text)

    def _hub_failed(self, why: str) -> None:
        """Log a hub failure once until the hub is joined again."""
        if why != self._hub_down:
            self.log(
                f"the hub {self.cfg.hub_alias} is unavailable ({why}); hub mail "
                "waits for the next sweep"
            )
        self._hub_down = why
        self._report_hub(f"unavailable: {why}\n")

    def _join_hub(self, deadline: float) -> None:
        """Join the hub within :data:`HUB_SECONDS` unless it is joined already."""
        hub = self.cfg.hub_alias
        if hub is None or self.hub_room is not None:
            return
        until = min(deadline, self.client.now() + HUB_SECONDS)
        try:
            room = self.rooms.room_id(hub, until, verify=True)
        except AuthError:
            raise
        except AgentChatError as exc:
            self._hub_failed(str(exc).splitlines()[0] if str(exc) else repr(exc))
            return
        if room is None:
            self._hub_failed("no such alias")
            return
        self.hub_room, self._hub_down = room, None
        self._report_hub("covered\n")
        self.log(f"serving the hub {hub}")

    def _sweep(self, deadline: float) -> None:
        """Join the hub, and the rooms of registered Codex sessions.

        The session rooms are joined in all-rooms mode only.
        """
        if self._now() < self._next_sweep:
            return
        self._next_sweep = self._now() + SWEEP_SECONDS
        self._join_hub(deadline)
        if self.alias is not None:
            return
        try:
            sessions = self.sessions()
        except AgentChatError as exc:
            self.log(f"cannot list the Codex sessions: {exc}")
            return
        for s in sessions:
            if s.labels.get(ROLE) != "codex" or not s.cwd:
                continue
            alias = project_alias(self.cfg, s.cwd)
            if alias == self.cfg.hub_alias:
                continue  # the hub is never a project's room
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
        try:
            return self._run()
        finally:
            if self.hub_file is not None:
                self.hub_file.unlink(missing_ok=True)

    def _run(self) -> int:
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
                    for alias, mail in self._batch_mail(rooms, deadline):
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
