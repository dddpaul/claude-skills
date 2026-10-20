"""Claude's mailbox: Codex's messages wait here until Claude's background wait takes them.

Layout under the mail root (private to the login uid)::

    <root>/<pair>/inbox/<ns>-<pid>-<rand>.msg   one JSON message, written atomically
    <root>/<pair>/quarantine/                   mail that was not delivered, kept
    <root>/<pair>/waiter                        heartbeat of the running wait (owner and wait pids)
    <root>/<pair>/waiter.lock                   held by the one running wait
    <root>/<pair>/collect.lock                  held while a collect takes the inbox
    <root>/outbox/<name>                        a message file Codex fills before a send
"""

from __future__ import annotations

import fcntl
import json
import os
import secrets
import stat
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .common import PROTO, ZpcError, check_token
from .procs import pid_alive

ROOT_ENV = "ZPC_MAIL_DIR"
# A wait refreshes its heartbeat every second; an older one belongs to no live wait.
STALE = 5


def _private_dir(path: Path) -> Path:
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        pass
    st = os.lstat(path)
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise ZpcError(f"{path} is not a private directory of this user")
    return path


def mail_root() -> Path:
    """Return the mail root, creating it mode 0700; refuse one that is not private."""
    root = os.environ.get(ROOT_ENV) or f"/tmp/zmx-peer-chat-{os.getuid()}"
    return _private_dir(Path(root))


@dataclass
class Collected:
    """What one collect took from the inbox."""

    messages: list[str] = field(default_factory=list)
    quarantined: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.messages or self.quarantined)

    def render(self) -> str:
        """Messages oldest first, a blank line apart, then one line per quarantine."""
        notes = [f"zmx-peer-chat: quarantined {q}" for q in self.quarantined]
        return "\n\n".join(self.messages + (["\n".join(notes)] if notes else []))


@dataclass
class WaitResult:
    """How a wait ended: mail, timeout, owner-gone or busy (another wait runs)."""

    outcome: str
    collected: Collected | None = None


class Mailbox:
    """The mailbox of one pair's Claude side."""

    def __init__(self, root: Path, pair: str) -> None:
        self.pair = check_token(pair, "pair id")
        self.dir = _private_dir(root / pair)
        self.inbox = _private_dir(self.dir / "inbox")
        self.quarantine = _private_dir(self.dir / "quarantine")

    def deliver(self, text: str, sender: str, to_inc: str) -> Path:
        """Queue ``text`` for the Claude incarnation ``to_inc``; return the file."""
        body = {
            "proto": PROTO,
            "pair": self.pair,
            "from": sender,
            "inc": to_inc,
            "sent": time.time(),
            "text": text,
        }
        name = f"{time.time_ns()}-{os.getpid()}-{secrets.token_hex(2)}.msg"
        tmp = self.inbox / f".tmp-{name}"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(body, f)
        final = self.inbox / name
        os.replace(tmp, final)
        return final

    def _verdict(self, path: Path, inc: str) -> tuple[str | None, str | None]:
        """Return (text, None) for deliverable mail, else (None, why not)."""
        try:
            body = json.loads(path.read_text(encoding="utf-8"))
            proto, pair, to_inc, text = (
                body["proto"],
                body["pair"],
                body["inc"],
                body["text"],
            )
        except (OSError, ValueError, KeyError, TypeError):
            return None, "an unreadable message"
        if proto != PROTO:
            return None, f"protocol version {proto!r}; this side speaks {PROTO!r}"
        if pair != self.pair:
            return None, f"mail for pair {pair!r}"
        if to_inc != inc:
            return None, (
                f"mail for an earlier incarnation {to_inc!r} of this session "
                f"(now {inc!r})"
            )
        if not isinstance(text, str):
            return None, "an unreadable message"
        return text, None

    def collect(self, inc: str) -> Collected:
        """Take every message for incarnation ``inc``, oldest first, under the lock.

        Mail that cannot be delivered (another protocol version, an earlier
        incarnation, unreadable) moves to the quarantine and is reported.
        """
        got = Collected()
        with open(self.dir / "collect.lock", "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            for path in sorted(self.inbox.glob("*.msg")):
                text, why = self._verdict(path, inc)
                if why is None:
                    got.messages.append(text or "")
                    path.unlink()
                else:
                    os.replace(path, self.quarantine / path.name)
                    got.quarantined.append(f"{path.name}: {why}")
        return got

    def _beat(self, owner: int) -> None:
        tmp = self.dir / f".waiter-{os.getpid()}"
        tmp.write_text(f"{owner} {os.getpid()}\n", encoding="utf-8")
        os.replace(tmp, self.dir / "waiter")

    def _unbeat(self, owner: int) -> None:
        beat = self.dir / "waiter"
        try:
            if beat.read_text(encoding="utf-8").split() == [
                str(owner),
                str(os.getpid()),
            ]:
                beat.unlink()
        except OSError:
            pass

    def waiting(self, alive: Callable[[int], bool] = pid_alive) -> bool:
        """Tell whether a wait runs: a fresh heartbeat whose owner and wait both live.

        The wait's own pid catches a wait that was killed before it could
        remove its heartbeat.
        """
        beat = self.dir / "waiter"
        try:
            age = time.time() - beat.stat().st_mtime
            owner, waiter = (int(f) for f in beat.read_text(encoding="utf-8").split())
        except (OSError, ValueError):
            return False
        return age < STALE and alive(owner) and alive(waiter)

    def wait(
        self,
        inc: str,
        owner: int,
        seconds: float,
        alive: Callable[[int], bool] = pid_alive,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], float] = time.monotonic,
    ) -> WaitResult:
        """Wait up to ``seconds`` for mail while ``owner`` lives.

        Only one wait runs per pair: a second one returns ``busy`` at once.
        The mail stays in the inbox when the owner exits first.
        """
        with open(self.dir / "waiter.lock", "a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return WaitResult("busy")
            deadline = now() + seconds
            try:
                while alive(owner):
                    self._beat(owner)
                    got = self.collect(inc)
                    if got:
                        return WaitResult("mail", got)
                    if now() >= deadline:
                        return WaitResult("timeout")
                    sleep(1)
                return WaitResult("owner-gone")
            finally:
                self._unbeat(owner)


def prepare_message(root: Path, name: str) -> Path:
    """Create the empty private message file ``name`` for a file-backed send."""
    check_token(name, "message file name")
    outbox = _private_dir(root / "outbox")
    path = outbox / name
    try:
        os.close(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
    except FileExistsError as exc:
        raise ZpcError(f"message file {name} exists; choose a fresh name", 2) from exc
    return path


def take_message(root: Path, name: str) -> str:
    """Read and remove the prepared message file ``name``."""
    check_token(name, "message file name")
    path = _private_dir(root / "outbox") / name
    try:
        st = os.lstat(path)
    except FileNotFoundError as exc:
        raise ZpcError(f"no prepared message {name}", 2) from exc
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
        raise ZpcError(f"prepared message {name} is not a plain file of this user", 2)
    text = path.read_text(encoding="utf-8")
    path.unlink()
    return text
