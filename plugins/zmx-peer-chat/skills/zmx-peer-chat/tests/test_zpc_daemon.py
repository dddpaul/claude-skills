"""The Codex daemon client fails closed.

``thread/loaded/list``, ``thread/read``, ``thread/name/set``, ``thread/list``,
``config/read``, ``skills/list`` and the ``thread/started`` notification over
``codex app-server proxy`` are an internal, undocumented API. Anything
unexpected in the handshake, the WebSocket framing or a response raises
``DaemonError`` (exit code 3), so no caller acts on a guess.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import signal
import time
from pathlib import Path
from typing import Any

import pytest
from zpc_fakes import THREAD_A, THREAD_B, FakeTransport, frame

from zpc.daemon import (
    _GUID,
    Daemon,
    DaemonError,
    ProcTransport,
    encode_frame,
    handshake,
    latest_params,
    read_frame,
)

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


def test_call_keeps_notifications_and_answers_pings() -> None:
    d = _daemon(
        frame({"method": "thread/started", "params": {}}),
        frame(b"hi", opcode=0x9),
        frame(b'{"id": 1, "res', fin=False),
        frame(b'ult": {"data": []}}', opcode=0x0),
    )
    assert d.call("thread/loaded/list", {}) == {"data": []}
    assert [op for op, _ in _sent(d)] == [0x1, 0xA]
    assert _sent(d)[1][1] == b"hi"
    assert list(d.notifications) == [{"method": "thread/started", "params": {}}]


def _started(tid: str, cwd: str) -> bytes:
    params = {"thread": {"id": tid, "cwd": cwd, "status": {"type": "idle"}}}
    return frame({"method": "thread/started", "params": params})


def test_started_threads_takes_each_thread_started_notification_once() -> None:
    other = frame({"method": "thread/status/changed", "params": {}})
    d = _daemon(_started(THREAD_A, "/w"), other, _started(THREAD_B, "/x"))
    d.notifications.extend(d._message(1) for _ in range(3))
    assert d.started_threads() == [(THREAD_A, "/w"), (THREAD_B, "/x")]
    assert d.started_threads() == []
    assert [n["method"] for n in d.notifications] == ["thread/status/changed"]


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"thread": None},
        {"thread": {"id": "x", "cwd": "/w"}},
        {"thread": {"id": THREAD_A}},
    ],
)
def test_started_threads_refuses_an_unexpected_notification(params: Any) -> None:
    d = _daemon()
    d.notifications.append({"method": "thread/started", "params": params})
    with pytest.raises(DaemonError, match="unexpected thread"):
        d.started_threads()


def test_latest_params_are_the_tuis_resume_last_query() -> None:
    # Pinned to latest_session_lookup_params in codex-rs/tui/src/lib.rs at
    # rust-v0.166.0: limit 1, sortKey updated_at (ThreadSortKey is snake_case),
    # the cwd filter, resume_source_kinds(false) = cli and vscode, archived
    # false, the history model provider, and useStateDbOnly true then false
    # (serde leaves false out).
    assert latest_params("/w", "openai", True) == {
        "limit": 1,
        "sortKey": "updated_at",
        "sourceKinds": ["cli", "vscode"],
        "archived": False,
        "cwd": "/w",
        "modelProviders": ["openai"],
        "useStateDbOnly": True,
    }
    assert latest_params("/w", None, False) == {
        "limit": 1,
        "sortKey": "updated_at",
        "sourceKinds": ["cli", "vscode"],
        "archived": False,
        "cwd": "/w",
    }


def _listed(rid: int, tid: str, path: str | None) -> bytes:
    return _answer(rid, {"data": [{"id": tid, "path": path}], "nextCursor": None})


def test_latest_thread_sends_the_tuis_query(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout.jsonl"
    rollout.write_text("")
    d = _daemon(
        _answer(1, {"config": {"model_provider": None}, "origins": {}}),
        _listed(2, THREAD_B, str(rollout)),
    )
    assert d.latest_thread("/w") == THREAD_B
    sent = [json.loads(p) for _, p in _sent(d)]
    assert [(m["method"], m["params"]) for m in sent] == [
        ("config/read", {"includeLayers": True, "cwd": "/w"}),
        ("thread/list", latest_params("/w", "openai", True)),
    ]


def test_latest_thread_scans_when_the_state_db_misses(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout.jsonl"
    rollout.write_text("")
    d = _daemon(
        _answer(1, error={"code": -32601, "message": "unknown method"}),
        _listed(2, THREAD_A, str(tmp_path / "gone.jsonl")),
        _listed(3, THREAD_B, str(rollout)),
    )
    assert d.latest_thread("/w") == THREAD_B
    sent = [json.loads(p)["params"] for _, p in _sent(d)][1:]
    assert sent == [latest_params("/w", None, True), latest_params("/w", None, False)]


def test_latest_thread_returns_none_without_a_thread() -> None:
    d = _daemon(
        _answer(1, {"config": {"model_provider": "oss"}}),
        _answer(2, error={"message": "no state db"}),
        _answer(3, {"data": [], "nextCursor": None}),
    )
    assert d.latest_thread("/w") is None
    assert json.loads(_sent(d)[2][1])["params"]["modelProviders"] == ["oss"]
    for bad in ({"data": {}}, {"data": [1]}):
        with pytest.raises(DaemonError, match="unexpected list"):
            _daemon(_answer(1, {"config": {}}), _answer(2, bad)).latest_thread("/w")
    with pytest.raises(DaemonError, match="unexpected config"):
        _daemon(_answer(1, {"config": {"model_provider": 3}})).latest_thread("/w")


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


def test_a_forked_bind_stops_the_proxy_it_did_not_start() -> None:
    # register keeps the snapshot's connection for the bind, which runs in a
    # forked grandchild; closing it there must still stop the proxy.
    t = ProcTransport(["sleep", "30"])
    child = os.fork()
    if child == 0:
        if os.fork() == 0:
            t.close()
        os._exit(0)
    os.waitpid(child, 0)
    for _ in range(50):
        if t.proc.poll() is not None:
            break
        time.sleep(0.05)
    assert t.proc.returncode == -signal.SIGTERM
