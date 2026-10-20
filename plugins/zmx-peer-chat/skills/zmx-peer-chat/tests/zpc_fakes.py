"""Fakes shared by the zmx-peer-chat tests: zmx, the Codex daemon, a byte transport.

Importing this module also puts the plugin's ``scripts`` directory on
``sys.path``, so the tests can import the ``zpc`` package.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from zpc.daemon import DaemonError, ThreadInfo  # noqa: E402
from zpc.zmx import Session  # noqa: E402

PAIR = "dpairfortests0001"
THREAD_A = "01a15a38-0000-7000-8000-00000000000a"
THREAD_B = "01a15a38-0000-7000-8000-00000000000b"
THREAD_C = "01a15a38-0000-7000-8000-00000000000c"
THREAD_E = "01a15a38-0000-7000-8000-00000000000e"


def labels(role: str, inc: str, pair: str = PAIR, **extra: str) -> dict[str, str]:
    """Return the labels a registered session of ``role`` carries."""
    out = {"zpc.pair": pair, "zpc.role": role, "zpc.inc": inc, "zpc.proto": "1"}
    out.update({f"zpc.{k}": v for k, v in extra.items()})
    return out


class FakeZmx:
    """In-memory zmx: sessions with labels, scrollback screens, recorded sets."""

    def __init__(
        self,
        sessions: list[Session] | None = None,
        screens: dict[str, str] | None = None,
    ) -> None:
        self.live = {s.name: s for s in sessions or []}
        self.screens = screens or {}
        self.set_calls: list[tuple[str, dict[str, str]]] = []

    def sessions(self) -> dict[str, Session]:
        return {n: Session(s.name, s.pid, dict(s.labels)) for n, s in self.live.items()}

    def set_labels(self, name: str, new: dict[str, str]) -> None:
        self.set_calls.append((name, dict(new)))
        self.live[name].labels.update(new)

    def history(self, name: str) -> str:
        return self.screens.get(name, "")


class FakeDaemon:
    """A scripted daemon.

    ``timeline`` holds one thread table per ``loaded_threads`` call; the last
    table repeats. ``read_thread`` answers from the table of the latest call.
    """

    def __init__(self, timeline: list[dict[str, ThreadInfo]]) -> None:
        self.timeline = timeline
        self.calls = 0
        self.table = timeline[0]
        self.names: dict[str, str] = {}

    def __enter__(self) -> FakeDaemon:
        return self

    def __exit__(self, *exc: object) -> None:
        pass

    def loaded_threads(self) -> list[str]:
        self.table = self.timeline[min(self.calls, len(self.timeline) - 1)]
        self.calls += 1
        return list(self.table)

    def read_thread(self, thread_id: str) -> ThreadInfo:
        return self.table[thread_id]

    def set_thread_name(self, thread_id: str, name: str) -> None:
        self.names[thread_id] = name


def thread(
    tid: str, cwd: str, updated: int, status: str = "idle", created: int = 1
) -> ThreadInfo:
    """Return a ThreadInfo for the fake daemon's tables."""
    return ThreadInfo(tid, cwd, status, None, created, updated)


class Clock:
    """A fake monotonic clock that ``sleep`` advances."""

    def __init__(self) -> None:
        self.t = 0.0

    def now(self) -> float:
        return self.t

    def sleep(self, dt: float) -> None:
        self.t += dt


class FakeTransport:
    """Bytes the server will send, and a record of what the client wrote."""

    def __init__(self, data: bytes = b"") -> None:
        self.data = data
        self.written = b""
        self.closed = False

    def write(self, data: bytes) -> None:
        self.written += data

    def read(self, n: int, deadline: float) -> bytes:
        if len(self.data) < n:
            raise DaemonError("no answer in time")
        out, self.data = self.data[:n], self.data[n:]
        return out

    def close(self) -> None:
        self.closed = True


def frame(
    payload: bytes | dict[str, Any] | list[Any],
    opcode: int = 1,
    fin: bool = True,
    first: int | None = None,
    masked: bool = False,
) -> bytes:
    """Encode one server frame; ``first`` overrides the first header byte."""
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    b1 = first if first is not None else (0x80 if fin else 0) | opcode
    mask = 0x80 if masked else 0
    n = len(body)
    if n < 126:
        head = struct.pack("!BB", b1, mask | n)
    elif n < 65536:
        head = struct.pack("!BBH", b1, mask | 126, n)
    else:
        head = struct.pack("!BBQ", b1, mask | 127, n)
    return head + (b"\0\0\0\0" if masked else b"") + body
