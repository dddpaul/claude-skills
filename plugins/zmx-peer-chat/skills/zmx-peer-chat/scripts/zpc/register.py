"""The launcher's register helper: label a new zmx session as one side of a pair.

The launcher calls it just before it creates the session. ``prepare`` refuses
nothing about an existing session (it leaves its labels alone and the launcher
attaches as usual), takes the per-directory registration lock, and for Codex
notes the time and snapshots the thread ids the daemon has loaded, with the
update time of each one whose cwd is the session directory. ``bind`` then
waits for the session, finds the Codex thread the new TUI opened in that
directory, names it ``zpc-<inc>``, checks that the TUI footer shows that name
and sets every label in one ``zmx set``.

On a freshly booted box no daemon runs until the first Codex TUI starts one,
so the launcher may register a Codex session before any daemon exists. No
daemon means no thread is loaded: ``prepare`` keeps the empty snapshot and
notes it, and ``bind`` keeps trying to open the daemon until its deadline.

The TUI either starts a thread or (the launcher runs ``codex resume --last``
in a directory with history) resumes one. The times only order the threads of
the directory that it may show, tried in this order:

- started: not loaded at the snapshot, created at or after it;
- newly loaded: not loaded at the snapshot, whatever its times. With codex-cli
  0.166.0 a resume of a thread the daemon had unloaded leaves its
  ``updatedAt`` at its last turn, so only being loaded again tells it apart;
- resumed: loaded at the snapshot, ``updatedAt`` moved past it;
- the other idle threads loaded at the snapshot, the most recently updated
  first (the one ``--last`` picks), in case a resume of a thread that is still
  loaded moves no time either. They join only after ``FALLBACK_SECONDS``
  without a candidate shown, so a starting TUI's own thread, which loads a few
  seconds after the session appears, is tried before any older thread is
  renamed.

A turn that ends moves ``updatedAt`` too, so a thread seen running a turn at
the snapshot or while the bind polls is never tried; the polls are 0.3 seconds
apart, shorter than any turn.

The times never prove anything: a starting TUI can load an older thread of the
directory that it does not show, and a TUI killed before its first turn leaves
a thread loaded that the daemon has not persisted, whose ``createdAt`` and
``updatedAt`` read as the time of the read. So each candidate is only named;
it is bound once the session's footer shows the name. A candidate the footer
does not show within ``CONFIRM_SECONDS`` is renamed away from it, so no two
threads ever carry the name, and the next one is tried; candidates take turns
until the deadline.
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

from .common import (
    LABEL_INC,
    LABEL_PAIR,
    LABEL_PROTO,
    LABEL_ROLE,
    LABEL_THREAD,
    PROTO,
    ROLES,
    ZpcError,
    check_token,
    pair_id,
    tui_shows,
)
from .daemon import Daemon, DaemonError, ThreadInfo
from .zmx import Zmx

OpenDaemon = Callable[[], Daemon]

# The default bind window: long enough for a TUI that opens its thread only
# after a startup dialog (an update notice, "Trust this folder?") is answered.
BIND_SECONDS = 60.0
# How long a named candidate may take to show up in the session's footer.
CONFIRM_SECONDS = 5.0
# How long the bind looks only at started, newly loaded and resumed threads
# before it also tries the idle threads that were loaded at the snapshot.
FALLBACK_SECONDS = 20.0


@dataclass
class Registration:
    """A session about to be created, with what bind needs to label it."""

    role: str
    session: str
    directory: str
    pair: str
    inc: str
    # Each thread id loaded at the snapshot: its updatedAt when its cwd is the
    # session directory, None for a thread elsewhere.
    before: dict[str, int | None] = field(default_factory=dict)
    # The snapshot's time, in whole epoch seconds like the daemon's timestamps.
    since: int = 0
    # Threads seen running a turn since the snapshot: a turn that ends also
    # moves updatedAt, so these are never taken for a resume.
    busy: set[str] = field(default_factory=set)
    # False when no Codex daemon could be opened at registration, so the
    # snapshot is empty because nothing was loaded, not because it was read.
    snapshot: bool = True
    lock: IO[str] | None = None


def thread_name(inc: str) -> str:
    """The name a bound Codex thread gets; the TUI footer shows it."""
    return f"zpc-{inc}"


def _unbound_name(inc: str) -> str:
    """The name a tried but unshown candidate gets back when it had none."""
    return f"{thread_name(inc)}-unbound"


def _dir_lock(root: Path, directory: str) -> IO[str]:
    digest = hashlib.sha256(directory.encode()).hexdigest()[:16]
    lock = open(root / f"register-{digest}.lock", "a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise ZpcError(
            f"another registration runs for {directory}; no label set "
            "(start one session at a time)",
            4,
        ) from None
    return lock


def prepare(
    role: str,
    session: str,
    directory: str,
    pair: str | None,
    zmx: Zmx,
    root: Path,
    open_daemon: OpenDaemon,
    wall: Callable[[], float] = time.time,
) -> Registration | None:
    """Get ready to label ``session``; return None when it already exists.

    Raises:
        ZpcError: Bad arguments (2), an unexpected answer from an open daemon
            (3) or a concurrent registration for the same directory (4). A
            daemon that cannot be opened leaves an empty snapshot instead.
    """
    if role not in ROLES:
        raise ZpcError(f"bad role: {role!r}", 2)
    check_token(session, "session name")
    real = os.path.realpath(directory)
    if not os.path.isdir(real):
        raise ZpcError(f"no such directory: {directory}", 2)
    if session in zmx.sessions():
        return None
    reg = Registration(role, session, real, pair_id(real, pair), secrets.token_hex(4))
    reg.lock = _dir_lock(root, real)
    try:
        if role == "codex":
            reg.since = int(wall())
            try:
                d = open_daemon()
            except DaemonError:
                reg.snapshot = False  # no daemon yet: nothing is loaded
            else:
                with d:
                    _snapshot(d, reg)
    except BaseException:
        reg.lock.close()
        raise
    return reg


def _in_dir(info: ThreadInfo, directory: str) -> bool:
    return os.path.realpath(info.cwd) == directory


def _snapshot(d: Daemon, reg: Registration) -> None:
    for t in d.loaded_threads():
        info = d.read_thread(t)
        in_dir = _in_dir(info, reg.directory)
        reg.before[t] = info.updated_at if in_dir else None
        if in_dir and info.status == "active":
            reg.busy.add(t)


def _candidates(d: Daemon, reg: Registration, fallback: bool) -> list[str]:
    """Return the threads in the directory that the new TUI may show.

    In the order they are tried: started, newly loaded, resumed, then, with
    ``fallback``, the other idle threads that were loaded at the snapshot, the
    most recently updated first.
    """
    started, loaded, resumed = [], [], []
    idle: list[tuple[int, str]] = []
    for t in d.loaded_threads():
        if t in reg.before and reg.before[t] is None:
            continue  # loaded before, in another directory
        info = d.read_thread(t)
        if not _in_dir(info, reg.directory):
            continue
        if info.status == "active":
            reg.busy.add(t)
        if t in reg.busy:
            continue  # ran a turn in the window: no TUI has just opened it
        old = reg.before.get(t)
        if old is None:
            (started if info.created_at >= reg.since else loaded).append(t)
        elif info.updated_at >= reg.since and info.updated_at > old:
            resumed.append(t)
        elif fallback and info.status == "idle":
            idle.append((info.updated_at, t))
    return started + loaded + resumed + [t for _, t in sorted(idle, reverse=True)]


def _shown(
    reg: Registration,
    zmx: Zmx,
    deadline: float,
    sleep: Callable[[float], None],
    now: Callable[[], float],
) -> bool:
    """Wait until the session's footer shows the thread name, or give up."""
    until = min(now() + CONFIRM_SECONDS, deadline)
    while not tui_shows(zmx.history(reg.session), thread_name(reg.inc)):
        if now() >= until:
            return False
        sleep(0.3)
    return True


def _open_until(
    open_daemon: OpenDaemon,
    deadline: float,
    sleep: Callable[[float], None],
    now: Callable[[], float],
) -> Daemon:
    """Open the daemon, retrying until ``deadline`` while none is reachable."""
    while True:
        try:
            return open_daemon()
        except DaemonError as exc:
            if now() >= deadline:
                raise ZpcError(
                    f"no Codex daemon was reachable in time (last error: {exc}); "
                    "no label set",
                    5,
                ) from exc
        sleep(0.4)


def _find_thread(
    reg: Registration,
    zmx: Zmx,
    open_daemon: OpenDaemon,
    deadline: float,
    sleep: Callable[[float], None],
    now: Callable[[], float],
) -> str:
    tried: list[str] = []  # least recently tried first
    name = thread_name(reg.inc)
    fallback_at = now() + FALLBACK_SECONDS
    with _open_until(open_daemon, deadline, sleep, now) as d:
        while True:
            match = _candidates(d, reg, now() >= fallback_at)
            if match:
                t = min(match, key=lambda m: tried.index(m) if m in tried else -1)
                previous = d.read_thread(t).name
                d.set_thread_name(t, name)
                if _shown(reg, zmx, deadline, sleep, now):
                    return t
                d.set_thread_name(t, previous or _unbound_name(reg.inc))
                if t in tried:
                    tried.remove(t)
                tried.append(t)
            if now() >= deadline:
                if tried:
                    raise ZpcError(
                        f"the Codex TUI in {reg.session} never showed {name} in "
                        f"its footer; named but not bound: {', '.join(tried)}; "
                        "no label set",
                        5,
                    )
                raise ZpcError(
                    f"no Codex thread opened in {reg.directory} in time; no label set",
                    5,
                )
            if not match:
                sleep(0.3)


def bind(
    reg: Registration,
    zmx: Zmx,
    open_daemon: OpenDaemon,
    timeout: float = BIND_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
) -> dict[str, str]:
    """Wait for the session (and its Codex thread), then label it; return the labels.

    Raises:
        ZpcError: The session, a reachable Codex daemon or a Codex thread the
            TUI footer shows did not appear within ``timeout`` seconds (5). No
            label is set then.
    """
    deadline = now() + timeout
    while reg.session not in zmx.sessions():
        if now() >= deadline:
            raise ZpcError(f"session {reg.session} did not appear; no label set", 5)
        sleep(0.2)
    labels = {
        LABEL_PAIR: reg.pair,
        LABEL_ROLE: reg.role,
        LABEL_INC: reg.inc,
        LABEL_PROTO: PROTO,
    }
    if reg.role == "codex":
        labels[LABEL_THREAD] = _find_thread(reg, zmx, open_daemon, deadline, sleep, now)
    zmx.set_labels(reg.session, labels)
    return labels


def bind_in_background(
    reg: Registration, log: Path, run: Callable[[], dict[str, str]]
) -> None:
    """Run ``run`` (the bind) in a detached grandchild that logs its outcome.

    The grandchild keeps the registration lock until it is done. It lets go of
    the caller's stdin, stdout and stderr, so a launcher that captures the
    helper's output gets end-of-file as soon as the helper returns.
    """
    log = log.resolve()
    child = os.fork()
    if child:
        os.waitpid(child, 0)
        return
    os.setsid()
    if os.fork():
        os._exit(0)
    null = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        os.dup2(null, fd)
    os.close(null)
    os.chdir("/")
    code = 0
    try:
        labels = run()
        line = f"{reg.session}: labelled " + " ".join(
            f"{k}={v}" for k, v in sorted(labels.items())
        )
        if not reg.snapshot:
            line += " (no Codex daemon at registration)"
    except ZpcError as exc:
        code, line = exc.code, f"{reg.session}: {exc}"
    except Exception as exc:  # noqa: BLE001 - the log is the only witness
        code, line = 1, f"{reg.session}: unexpected error: {exc!r}"
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"{stamp} {line}\n")
    os._exit(code)
