"""A stdlib client for the local Codex app-server daemon, over `codex app-server proxy`.

The proxy passes stdio to the daemon's control socket, which speaks JSON-RPC
over WebSocket. This is an internal, undocumented API of codex-cli (tested with
the version in ``common.TESTED_CODEX_CLI``), so the client fails closed: any
unexpected handshake, frame or response raises ``DaemonError`` and the caller
acts on nothing.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import select
import struct
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Protocol

from .common import ZpcError, is_uuid

_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_MAX_FRAME = 16 * 1024 * 1024
_STATUSES = {"notLoaded", "idle", "systemError", "active"}


class DaemonError(ZpcError):
    """The daemon could not be reached or answered something unexpected."""

    def __init__(self, message: str) -> None:
        super().__init__(f"codex daemon: {message}", 3)


class Transport(Protocol):
    """A byte stream to the daemon."""

    def write(self, data: bytes) -> None: ...

    def read(self, n: int, deadline: float) -> bytes: ...

    def close(self) -> None: ...


class ProcTransport:
    """The stdio of a `codex app-server proxy` child process."""

    def __init__(self, argv: list[str]) -> None:
        try:
            self.proc = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            raise DaemonError(f"cannot start {argv[0]}: {exc}") from exc
        assert self.proc.stdin and self.proc.stdout
        self._in = self.proc.stdin
        self._fd = self.proc.stdout.fileno()
        self._buf = b""

    def write(self, data: bytes) -> None:
        try:
            self._in.write(data)
            self._in.flush()
        except OSError as exc:
            raise DaemonError(f"proxy closed its input: {exc}") from exc

    def read(self, n: int, deadline: float) -> bytes:
        while len(self._buf) < n:
            left = deadline - time.monotonic()
            if left <= 0 or not select.select([self._fd], [], [], left)[0]:
                raise DaemonError("no answer in time")
            chunk = os.read(self._fd, 65536)
            if not chunk:
                raise DaemonError("proxy closed its output")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def close(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def encode_frame(payload: bytes, mask: bytes, opcode: int = 1) -> bytes:
    """Encode one final, masked client frame."""
    n = len(payload)
    if n < 126:
        head = struct.pack("!BB", 0x80 | opcode, 0x80 | n)
    elif n < 65536:
        head = struct.pack("!BBH", 0x80 | opcode, 0x80 | 126, n)
    else:
        head = struct.pack("!BBQ", 0x80 | opcode, 0x80 | 127, n)
    body = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return head + mask + body


def read_frame(t: Transport, deadline: float) -> tuple[bool, int, bytes]:
    """Read one server frame: (fin, opcode, payload). Server frames are unmasked."""
    b1, b2 = t.read(2, deadline)
    if b1 & 0x70:
        raise DaemonError("frame with reserved bits set")
    if b2 & 0x80:
        raise DaemonError("masked frame from the server")
    n = b2 & 0x7F
    if n == 126:
        n = struct.unpack("!H", t.read(2, deadline))[0]
    elif n == 127:
        n = struct.unpack("!Q", t.read(8, deadline))[0]
    if n > _MAX_FRAME:
        raise DaemonError(f"frame of {n} bytes")
    return bool(b1 & 0x80), b1 & 0x0F, t.read(n, deadline) if n else b""


def _read_head(t: Transport, deadline: float) -> list[str]:
    raw = b""
    while not raw.endswith(b"\r\n\r\n"):
        raw += t.read(1, deadline)
        if len(raw) > 8192:
            raise DaemonError("handshake answer too long")
    return raw.decode("latin-1").split("\r\n")[:-2]


def handshake(t: Transport, key: str, deadline: float) -> None:
    """Upgrade the stream to WebSocket and check the server's answer."""
    t.write(
        (
            "GET / HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        ).encode()
    )
    lines = _read_head(t, deadline)
    if not lines or not lines[0].startswith("HTTP/1.1 101"):
        raise DaemonError(f"handshake refused: {lines[0] if lines else 'nothing'!r}")
    headers = {}
    for line in lines[1:]:
        name, _, value = line.partition(":")
        headers[name.strip().lower()] = value.strip()
    expect = base64.b64encode(hashlib.sha1((key + _GUID).encode()).digest()).decode()
    if headers.get("sec-websocket-accept") != expect:
        raise DaemonError("handshake answer has a wrong Sec-WebSocket-Accept")


@dataclass
class ThreadInfo:
    """What the daemon says about one thread."""

    id: str
    cwd: str
    status: str
    name: str | None
    created_at: int
    updated_at: int


class Daemon:
    """JSON-RPC calls to the daemon over an upgraded transport."""

    def __init__(self, transport: Transport, timeout: float = 10.0) -> None:
        self.t = transport
        self.timeout = timeout
        self._id = 0

    @classmethod
    def open(cls, argv: list[str] | None = None, timeout: float = 10.0) -> Daemon:
        """Start the proxy, upgrade it and initialize a client session."""
        cmd = argv or os.environ.get("ZPC_CODEX", "codex").split() + [
            "app-server",
            "proxy",
        ]
        d = cls(ProcTransport(cmd), timeout)
        try:
            key = base64.b64encode(os.urandom(16)).decode()
            handshake(d.t, key, time.monotonic() + timeout)
            d.call(
                "initialize", {"clientInfo": {"name": "zmx-peer-chat", "version": "1"}}
            )
            d._send({"method": "initialized"})
        except BaseException:
            d.close()
            raise
        return d

    def __enter__(self) -> Daemon:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the transport."""
        self.t.close()

    def _send(self, obj: dict[str, Any]) -> None:
        self.t.write(encode_frame(json.dumps(obj).encode(), os.urandom(4)))

    def _message(self, deadline: float) -> dict[str, Any]:
        parts: list[bytes] = []
        while True:
            fin, op, payload = read_frame(self.t, deadline)
            if op == 0x9:
                self.t.write(encode_frame(payload, os.urandom(4), 0xA))
                continue
            if op == 0xA:
                continue
            if op == 0x8:
                raise DaemonError("the daemon closed the connection")
            if op not in (0x0, 0x1) or (op == 0x0) != bool(parts):
                raise DaemonError(f"unexpected frame opcode {op}")
            parts.append(payload)
            if fin:
                break
        try:
            msg = json.loads(b"".join(parts))
        except ValueError as exc:
            raise DaemonError("an answer that is not JSON") from exc
        if not isinstance(msg, dict):
            raise DaemonError("an answer that is not a JSON object")
        return msg

    def call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Call ``method`` and return its ``result`` object."""
        self._id += 1
        rid = self._id
        self._send({"id": rid, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            msg = self._message(deadline)
            if "id" not in msg:
                continue  # a notification
            if "method" in msg:
                raise DaemonError(
                    f"unexpected request {msg['method']!r} from the daemon"
                )
            if msg["id"] != rid:
                raise DaemonError(f"answer to request {msg['id']!r}, expected {rid}")
            if "error" in msg:
                err = msg["error"]
                why = err.get("message") if isinstance(err, dict) else err
                raise DaemonError(f"{method} failed: {why}")
            result = msg.get("result")
            if not isinstance(result, dict):
                raise DaemonError(f"{method} answered without a result object")
            return result

    def loaded_threads(self) -> list[str]:
        """Return the ids of every thread the daemon has loaded."""
        ids: list[str] = []
        cursor: str | None = None
        while True:
            params = {"cursor": cursor} if cursor else {}
            result = self.call("thread/loaded/list", params)
            data, cursor = result.get("data"), result.get("nextCursor")
            if not isinstance(data, list) or not all(
                isinstance(i, str) and is_uuid(i) for i in data
            ):
                raise DaemonError("thread/loaded/list answered an unexpected list")
            if cursor is not None and not isinstance(cursor, str):
                raise DaemonError("thread/loaded/list answered an unexpected cursor")
            ids += data
            if not cursor:
                return ids

    def read_thread(self, thread_id: str) -> ThreadInfo:
        """Return the id, cwd, status, name, creation and update time of ``thread_id``."""
        result = self.call(
            "thread/read", {"threadId": thread_id, "includeTurns": False}
        )
        t = result.get("thread")
        if not isinstance(t, dict):
            raise DaemonError("thread/read answered no thread")
        status = t.get("status")
        stype = status.get("type") if isinstance(status, dict) else None
        name = t.get("name")
        created, updated = t.get("createdAt"), t.get("updatedAt")
        if (
            t.get("id") != thread_id
            or not isinstance(t.get("cwd"), str)
            or stype not in _STATUSES
            or not (name is None or isinstance(name, str))
            or not all(
                isinstance(v, int) and not isinstance(v, bool)
                for v in (created, updated)
            )
        ):
            raise DaemonError("thread/read answered an unexpected thread")
        return ThreadInfo(thread_id, t["cwd"], stype, name, created, updated)

    def set_thread_name(self, thread_id: str, name: str) -> None:
        """Give ``thread_id`` the name ``name`` (shown in the TUI footer)."""
        self.call("thread/name/set", {"threadId": thread_id, "name": name})

    def skills(self, cwd: str) -> list[str]:
        """Return the names of the skills Codex lists for ``cwd``."""
        result = self.call("skills/list", {"cwds": [cwd], "forceReload": True})
        data = result.get("data")
        if not isinstance(data, list):
            raise DaemonError("skills/list answered an unexpected list")
        names: list[str] = []
        for entry in data:
            skills = entry.get("skills") if isinstance(entry, dict) else None
            if not isinstance(skills, list):
                raise DaemonError("skills/list answered an unexpected entry")
            for s in skills:
                if not isinstance(s, dict) or not isinstance(s.get("name"), str):
                    raise DaemonError("skills/list answered an unexpected skill")
                names.append(s["name"])
        return names
