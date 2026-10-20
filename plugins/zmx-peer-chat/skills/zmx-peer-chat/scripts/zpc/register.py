"""The launcher's register helper: label a new zmx session as one side of a pair.

The launcher calls it just before it creates the session. ``prepare`` refuses
nothing about an existing session (it leaves its labels alone and the launcher
attaches as usual), takes the per-directory registration lock, and for Codex
notes the time and snapshots the thread ids the daemon has loaded, with the
update time of each one whose cwd is the session directory. ``bind`` then
waits for the session, finds the one Codex thread the new TUI opened in that
directory, names it ``zpc-<inc>`` and sets every label in one ``zmx set``.

The TUI either starts a thread or (the launcher runs ``codex resume --last``
in a directory with history) resumes one:

- a started thread is a loaded id that was not there before, created after
  the snapshot;
- resuming a thread moves its ``updatedAt`` to the time of the resume, past the
  snapshot, whether the daemon still had it loaded or loads it again.

Being newly loaded is not enough: a starting TUI can load an older thread of
the directory that it does not show, and that thread keeps its old times.
An exiting TUI moves neither time. A turn that ends moves ``updatedAt`` too, so
a thread seen running a turn at the snapshot or while the bind polls is never
taken; the polls are 0.3 seconds apart, shorter than any turn.
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
)
from .daemon import Daemon, ThreadInfo
from .zmx import Zmx

OpenDaemon = Callable[[], Daemon]


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
    lock: IO[str] | None = None


def thread_name(inc: str) -> str:
    """The name a bound Codex thread gets; the TUI footer shows it."""
    return f"zpc-{inc}"


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
        ZpcError: Bad arguments (2), daemon trouble (3) or a concurrent
            registration for the same directory (4).
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
            with open_daemon() as d:
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


def _candidates(d: Daemon, reg: Registration) -> list[str]:
    """Return the threads in the directory that the new TUI may have opened."""
    found = []
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
        started = t not in reg.before and info.created_at >= reg.since
        old = reg.before.get(t)
        resumed = info.updated_at >= reg.since and (
            old is None or info.updated_at > old
        )
        if started or resumed:
            found.append(t)
    return found


def _find_thread(
    reg: Registration,
    open_daemon: OpenDaemon,
    deadline: float,
    sleep: Callable[[float], None],
    now: Callable[[], float],
) -> str:
    with open_daemon() as d:
        while True:
            match = _candidates(d, reg)
            if len(match) > 1:
                raise ZpcError(
                    f"{len(match)} Codex threads opened in {reg.directory} at once; "
                    "refusing to guess, no label set",
                    4,
                )
            if match:
                d.set_thread_name(match[0], thread_name(reg.inc))
                return match[0]
            if now() >= deadline:
                raise ZpcError(
                    f"no Codex thread opened in {reg.directory} in time; no label set",
                    5,
                )
            sleep(0.3)


def bind(
    reg: Registration,
    zmx: Zmx,
    open_daemon: OpenDaemon,
    timeout: float,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
) -> dict[str, str]:
    """Wait for the session (and its Codex thread), then label it; return the labels.

    Raises:
        ZpcError: Several candidate threads (4), or the session or its thread
            did not appear within ``timeout`` seconds (5). No label is set then.
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
        labels[LABEL_THREAD] = _find_thread(reg, open_daemon, deadline, sleep, now)
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
    except ZpcError as exc:
        code, line = exc.code, f"{reg.session}: {exc}"
    except Exception as exc:  # noqa: BLE001 - the log is the only witness
        code, line = 1, f"{reg.session}: unexpected error: {exc!r}"
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"{stamp} {line}\n")
    os._exit(code)
