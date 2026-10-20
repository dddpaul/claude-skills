"""The Codex daemon client fails closed.

``thread/loaded/list``, ``thread/read``, ``thread/name/set`` and ``skills/list``
over ``codex app-server proxy`` are an internal, undocumented API. Anything
unexpected in the handshake, the WebSocket framing or a response raises
``DaemonError`` (exit code 3), so no caller acts on a guess.
"""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

import pytest
from zpc_fakes import THREAD_A, THREAD_B, FakeTransport, frame

from zpc.daemon import _GUID, Daemon, DaemonError, encode_frame, handshake, read_frame

KEY = base64.b64encode(b"0123456789abcdef").decode()
ACCEPT = base64.b64encode(hashlib.sha1((KEY + _GUID).encode()).digest()).decode()


def _answer(rid: int, result: Any = None, **extra: Any) -> bytes:
    body: dict[str, Any] = {"id": rid}
    if result is not None:
        body["result"] = result
    body.update(extra)
    return frame(body)


def _daemon(*frames: bytes) -> Daemon:
    return Daemon(FakeTransport(b"".join(frames)), timeout=1)


def _sent(d: Daemon) -> list[tuple[int, bytes]]:
    """Unmask the frames the client wrote: (opcode, payload) each."""
    raw: bytes = d.t.written  # type: ignore[attr-defined]
    out = []
    while raw:
        n = raw[1] & 0x7F
        head = 2 + (2 if n == 126 else 8 if n == 127 else 0)
        if n >= 126:
            n = int.from_bytes(raw[2:head], "big")
        mask, body = raw[head : head + 4], raw[head + 4 : head + 4 + n]
        out.append((raw[0] & 0x0F, bytes(b ^ mask[i % 4] for i, b in enumerate(body))))
        raw = raw[head + 4 + n :]
    return out


def _thread(**over: Any) -> dict[str, Any]:
    t = {
        "id": THREAD_A,
        "cwd": "/w",
        "status": {"type": "idle"},
        "name": None,
        "createdAt": 1792515028,
        "updatedAt": 1792515307,
    }
    t.update(over)
    return {"thread": t}


def test_handshake_checks_the_accept_header() -> None:
    ok = f"HTTP/1.1 101 Switching Protocols\r\nSec-WebSocket-Accept: {ACCEPT}\r\n\r\n"
    t = FakeTransport(ok.encode())
    handshake(t, KEY, 0)
    assert b"Sec-WebSocket-Key: " + KEY.encode() in t.written
    bad = "HTTP/1.1 101 Switching Protocols\r\nSec-WebSocket-Accept: AAAA\r\n\r\n"
    with pytest.raises(DaemonError, match="Sec-WebSocket-Accept"):
        handshake(FakeTransport(bad.encode()), KEY, 0)
    with pytest.raises(DaemonError, match="handshake refused"):
        handshake(FakeTransport(b"HTTP/1.1 400 Bad Request\r\n\r\n"), KEY, 0)
    with pytest.raises(DaemonError, match="no answer"):
        handshake(FakeTransport(b"HTTP/1.1 101"), KEY, 0)


def test_call_skips_notifications_and_answers_pings() -> None:
    d = _daemon(
        frame({"method": "thread/started", "params": {}}),
        frame(b"hi", opcode=0x9),
        frame(b'{"id": 1, "res', fin=False),
        frame(b'ult": {"data": []}}', opcode=0x0),
    )
    assert d.call("thread/loaded/list", {}) == {"data": []}
    assert [op for op, _ in _sent(d)] == [0x1, 0xA]
    assert _sent(d)[1][1] == b"hi"


@pytest.mark.parametrize(
    ("server", "match"),
    [
        (_answer(1, error={"message": "boom"}), "failed: boom"),
        (_answer(1, result=[1]), "without a result object"),
        (_answer(1), "without a result object"),
        (_answer(7, result={}), "answer to request 7"),
        (
            frame({"id": 9, "method": "item/commandExecution/requestApproval"}),
            "request",
        ),
        (frame([1, 2]), "not a JSON object"),
        (frame(b"{nope"), "not JSON"),
        (frame(b"", opcode=0x8), "closed the connection"),
        (frame(b"x", opcode=0x2), "opcode 2"),
        (frame(b"x", opcode=0x0), "opcode 0"),
        (frame({"id": 1}, first=0xC1), "reserved bits"),
        (frame({"id": 1}, masked=True), "masked frame"),
        (b"\x81\x7f" + (2**40).to_bytes(8, "big"), "frame of"),
        (b"", "no answer"),
    ],
)
def test_unexpected_answers_raise(server: bytes, match: str) -> None:
    with pytest.raises(DaemonError, match=match) as err:
        _daemon(server).call("thread/loaded/list", {})
    assert err.value.code == 3


def test_loaded_threads_pages_and_checks_ids() -> None:
    d = _daemon(
        _answer(1, {"data": [THREAD_A], "nextCursor": "c2"}),
        _answer(2, {"data": [THREAD_B], "nextCursor": None}),
    )
    assert d.loaded_threads() == [THREAD_A, THREAD_B]
    assert [json.loads(p)["params"] for _, p in _sent(d)] == [{}, {"cursor": "c2"}]
    for result in (
        {"data": ["not-a-uuid"]},
        {"data": "x"},
        {"data": [], "nextCursor": 3},
    ):
        with pytest.raises(DaemonError):
            _daemon(_answer(1, result)).loaded_threads()


def test_read_thread_returns_its_fields() -> None:
    info = _daemon(_answer(1, _thread(name="zpc-1"))).read_thread(THREAD_A)
    assert (info.cwd, info.status, info.name, info.created_at, info.updated_at) == (
        "/w",
        "idle",
        "zpc-1",
        1792515028,
        1792515307,
    )


@pytest.mark.parametrize(
    "over",
    [
        {"id": THREAD_B},
        {"cwd": None},
        {"status": {"type": "sleeping"}},
        {"status": "idle"},
        {"name": 5},
        {"updatedAt": None},
        {"updatedAt": "1792515307"},
        {"updatedAt": True},
        {"createdAt": None},
        {"createdAt": 1.5},
    ],
)
def test_read_thread_refuses_an_unexpected_thread(over: dict[str, Any]) -> None:
    with pytest.raises(DaemonError, match="unexpected thread"):
        _daemon(_answer(1, _thread(**over))).read_thread(THREAD_A)
    with pytest.raises(DaemonError, match="no thread"):
        _daemon(_answer(1, {})).read_thread(THREAD_A)


def test_skills_lists_names_or_fails_closed() -> None:
    ok = {"data": [{"cwd": "/w", "skills": [{"name": "zmx-peer-chat:zmx-peer-chat"}]}]}
    assert _daemon(_answer(1, ok)).skills("/w") == ["zmx-peer-chat:zmx-peer-chat"]
    for bad in (
        {"data": {}},
        {"data": [{"skills": "x"}]},
        {"data": [{"skills": [{}]}]},
    ):
        with pytest.raises(DaemonError):
            _daemon(_answer(1, bad)).skills("/w")


def test_set_thread_name_sends_the_request() -> None:
    d = _daemon(_answer(1, {}))
    d.set_thread_name(THREAD_A, "zpc-c0dec0de")
    ((op, body),) = _sent(d)
    assert op == 0x1
    assert json.loads(body) == {
        "id": 1,
        "method": "thread/name/set",
        "params": {"threadId": THREAD_A, "name": "zpc-c0dec0de"},
    }


@pytest.mark.parametrize("n", [0, 125, 126, 65535, 65536])
def test_encoded_frames_read_back(n: int) -> None:
    raw = encode_frame(b"x" * n, b"\x01\x02\x03\x04")
    # Unmask it the way a server would, then parse it as a server frame.
    b2 = raw[1] & 0x7F
    head = 2 + (2 if b2 == 126 else 8 if b2 == 127 else 0)
    mask, body = raw[head : head + 4], raw[head + 4 :]
    plain = bytes(b ^ mask[i % 4] for i, b in enumerate(body))
    server = raw[:1] + bytes([raw[1] & 0x7F]) + raw[2:head] + plain
    assert read_frame(FakeTransport(server), 0) == (True, 1, b"x" * n)


def test_a_missing_codex_binary_is_a_daemon_error() -> None:
    with pytest.raises(DaemonError, match="cannot start"):
        Daemon.open(["/nonexistent/codex", "app-server", "proxy"], timeout=1)
