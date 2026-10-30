"""Fakes shared by the agent-chat tests: a homeserver, a CONNECT proxy, process tables.

Importing this module also puts the plugin's ``scripts`` directory on
``sys.path``, so the tests can import the ``agent_chat`` package. Every name
here is a placeholder: no real host, account or token.
"""

from __future__ import annotations

import io
import json
import os
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

SERVER = "example.test"
HUMAN = f"@human:{SERVER}"
CLAUDE_A = f"@claude-a:{SERVER}"
CODEX_A = f"@codex-a:{SERVER}"
CLAUDE_B = f"@claude-b:{SERVER}"
CODEX_B = f"@codex-b:{SERVER}"
STRANGER = f"@stranger:{SERVER}"
TOKENS = {
    CLAUDE_A: "tok-claude-a-0000",
    CODEX_A: "tok-codex-a-0000",
    CLAUDE_B: "tok-claude-b-0000",
    CODEX_B: "tok-codex-b-0000",
    HUMAN: "tok-human-0000",
    STRANGER: "tok-stranger-0000",
}
from agent_chat import cli  # noqa: E402

PROJECT = "proj"
ALIAS = f"#agents-{PROJECT}:{SERVER}"
ROOM = "!room0001:example.test"


class FakeHomeserver:
    """An in-memory Matrix homeserver with just the endpoints agent-chat uses.

    Sync tokens are ``s<n>``: the number of events posted so far. A long-poll
    sync waits on a condition until an event arrives or its timeout passes.
    """

    def __init__(self) -> None:
        self.cond = threading.Condition()
        self.aliases: dict[str, str] = {}
        self.joined: dict[str, set[str]] = {}
        self.invited: dict[str, set[str]] = {}
        self.events: list[tuple[str, dict[str, Any]]] = []
        self.left: dict[tuple[str, str], int] = {}
        self.joined_at: dict[tuple[str, str], int] = {}
        self.canonical: dict[str, str] = {}
        self.filters: dict[str, Any] = {}
        self.txns: dict[tuple[str, str], str] = {}
        self.requests: list[tuple[str, str, dict[str, list[str]], Any]] = []
        self.drop_next = 0  # close this many connections before handling them
        self.lose_answers = 0  # handle this many requests, then close unanswered
        self.revoked: set[str] = set()
        # A real server may answer a long poll early; this one does after
        # max_poll seconds, so a wait checks its owner often in tests.
        self.max_poll = 0.5
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self) -> None:
        """Stop serving and wake every long poll."""
        with self.cond:
            self.cond.notify_all()
        self.httpd.shutdown()
        self.httpd.server_close()

    def room(
        self, alias: str, room_id: str, joined: set[str], invited: set[str]
    ) -> None:
        """Create a room with ``alias`` (also its canonical alias), its members."""
        self.aliases[alias] = room_id
        self.canonical[room_id] = alias
        self.joined[room_id] = set(joined)
        self.invited[room_id] = set(invited)

    def kick(self, room_id: str, user: str) -> None:
        """Remove ``user`` from ``room_id``; their next sync lists it under leave."""
        with self.cond:
            self.joined[room_id].discard(user)
            self.left[(user, room_id)] = len(self.events)
            self.events.append(
                (
                    room_id,
                    {
                        "type": "m.room.member",
                        "sender": user,
                        "state_key": user,
                        "content": {"membership": "leave"},
                    },
                )
            )
            self.cond.notify_all()

    def post(
        self,
        room_id: str,
        sender: str,
        body: str,
        mentions: list[str] | None = None,
        edit: bool = False,
    ) -> str:
        """Post ``body`` from ``sender``; return the event ID."""
        content: dict[str, Any] = {"msgtype": "m.text", "body": body}
        if mentions is not None:
            content["m.mentions"] = {"user_ids": mentions}
        if edit:
            content["m.relates_to"] = {"rel_type": "m.replace", "event_id": "$x"}
        return self._append(room_id, sender, content)

    def _append(self, room_id: str, sender: str, content: dict[str, Any]) -> str:
        with self.cond:
            event_id = f"$e{len(self.events)}"
            self.events.append(
                (
                    room_id,
                    {
                        "type": "m.room.message",
                        "sender": sender,
                        "event_id": event_id,
                        "content": content,
                    },
                )
            )
            self.cond.notify_all()
        return event_id

    def messages(self, room_id: str) -> list[dict[str, Any]]:
        """Return the message events of ``room_id``."""
        return [
            e for r, e in self.events if r == room_id and e["type"] == "m.room.message"
        ]

    def paths(self, method: str | None = None) -> list[str]:
        """Return the request paths seen, optionally for one method."""
        return [p for m, p, _, _ in self.requests if method in (None, m)]

    def _sync(self, user: str, q: dict[str, list[str]]) -> dict[str, Any]:
        filt = q.get("filter", [""])[0]
        if filt.startswith("{"):
            timeline = json.loads(filt)["room"]["timeline"]
        elif filt in self.filters:
            timeline = self.filters[filt]["room"]["timeline"]
        else:
            raise _Answer(400, "M_INVALID_PARAM", "unknown filter")
        limit = timeline.get("limit", 50)
        types = timeline.get("types")

        def shown(e: dict[str, Any]) -> bool:
            return types is None or e["type"] in types

        since = q.get("since", [None])[0]
        timeout = min(int(q.get("timeout", ["0"])[0]) / 1000, self.max_poll)
        with self.cond:
            if since and not since[1:].isdigit():
                raise _Answer(400, "M_INVALID_PARAM", "bad since token")
            start = int(since[1:]) if since else None
            if start is not None and len(self.events) <= start:
                self.cond.wait(timeout)
            end = len(self.events)
            rooms: dict[str, Any] = {"join": {}, "leave": {}}
            for room_id, members in self.joined.items():
                if user not in members:
                    continue
                first = 0 if start is None else start
                # Like a real server, the first sync after a join carries some
                # of the room's history, the join event last.
                at = self.joined_at.get((user, room_id))
                if start is not None and at is not None and start <= at < end:
                    first = 0
                events = [
                    e for r, e in self.events[first:end] if r == room_id and shown(e)
                ]
                events = events[-limit:] if limit else []
                rooms["join"][room_id] = {"timeline": {"events": events}}
            # Like a real server, a newly left room shows only when the filter
            # lets some of its events (the membership change) through.
            for (who, room_id), at in self.left.items():
                if who == user and start is not None and start <= at < end:
                    events = [e for r, e in self.events[at:end] if r == room_id]
                    if any(shown(e) for e in events):
                        rooms["leave"][room_id] = {
                            "timeline": {"events": [e for e in events if shown(e)]}
                        }
        return {"next_batch": f"s{end}", "rooms": rooms}

    def _route(
        self, method: str, path: str, q: dict[str, Any], body: Any, user: str
    ) -> Any:
        api = "/_matrix/client/v3"
        if method == "GET" and path.startswith(f"{api}/directory/room/"):
            alias = unquote(path.rsplit("/", 1)[1])
            if alias not in self.aliases:
                raise _Answer(404, "M_NOT_FOUND", "Room alias not found")
            return {"room_id": self.aliases[alias], "servers": [SERVER]}
        if method == "GET" and path == f"{api}/joined_rooms":
            return {"joined_rooms": [r for r, m in self.joined.items() if user in m]}
        if method == "POST" and path.startswith(f"{api}/join/"):
            room_id = self.aliases.get(unquote(path.rsplit("/", 1)[1]))
            if (
                room_id is None
                or user not in self.invited[room_id] | self.joined[room_id]
            ):
                raise _Answer(403, "M_FORBIDDEN", "not invited")
            with self.cond:
                self.joined[room_id].add(user)
                self.left.pop((user, room_id), None)
                self.joined_at[(user, room_id)] = len(self.events)
                self.events.append(
                    (
                        room_id,
                        {
                            "type": "m.room.member",
                            "sender": user,
                            "state_key": user,
                            "content": {"membership": "join"},
                        },
                    )
                )
                self.cond.notify_all()
            return {"room_id": room_id}
        if method == "GET" and path.endswith("/state/m.room.canonical_alias"):
            room_id = unquote(path.split("/")[5])
            if user not in self.joined.get(room_id, set()):
                raise _Answer(403, "M_FORBIDDEN", "not in room")
            if room_id not in self.canonical:
                raise _Answer(404, "M_NOT_FOUND", "Event not found")
            return {"alias": self.canonical[room_id]}
        if method == "POST" and path.endswith("/filter"):
            fid = f"f{len(self.filters)}"
            self.filters[fid] = body
            return {"filter_id": fid}
        if method == "GET" and path == f"{api}/sync":
            return self._sync(user, q)
        if method == "PUT" and "/send/m.room.message/" in path:
            parts = path.split("/")
            room_id, txn = unquote(parts[5]), unquote(parts[8])
            if user not in self.joined.get(room_id, set()):
                raise _Answer(403, "M_FORBIDDEN", "not in room")
            if (user, txn) not in self.txns:
                self.txns[(user, txn)] = self._append(room_id, user, body)
            return {"event_id": self.txns[(user, txn)]}
        raise _Answer(404, "M_UNRECOGNIZED", f"{method} {path}")

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        hs = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:
                pass

            def _serve(self, method: str) -> None:
                u = urlsplit(self.path)
                q = parse_qs(u.query)
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n)) if n else None
                hs.requests.append((method, u.path, q, body))
                if hs.drop_next > 0:
                    hs.drop_next -= 1
                    self.close_connection = True
                    self.connection.shutdown(socket.SHUT_RDWR)
                    return
                auth = self.headers.get("Authorization", "")
                token = auth.removeprefix("Bearer ")
                user = next((u for u, t in TOKENS.items() if t == token), None)
                try:
                    if user is None or token in hs.revoked:
                        raise _Answer(401, "M_UNKNOWN_TOKEN", "Invalid access token")
                    status, answer = 200, hs._route(method, u.path, q, body, user)
                except _Answer as a:
                    status, answer = a.status, {"errcode": a.errcode, "error": a.error}
                if hs.lose_answers > 0:
                    hs.lose_answers -= 1
                    self.close_connection = True
                    self.connection.shutdown(socket.SHUT_RDWR)
                    return
                raw = json.dumps(answer).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self) -> None:  # noqa: N802
                self._serve("GET")

            def do_POST(self) -> None:  # noqa: N802
                self._serve("POST")

            def do_PUT(self) -> None:  # noqa: N802
                self._serve("PUT")

        return Handler


class _Answer(Exception):
    def __init__(self, status: int, errcode: str, error: str) -> None:
        super().__init__(error)
        self.status, self.errcode, self.error = status, errcode, error


class FakeProxy:
    """A CONNECT proxy that records each request line and resolves names itself.

    ``names`` maps a host name to the local port that answers for it, so a
    name that does not resolve on this machine still reaches the homeserver.
    """

    def __init__(self, names: dict[str, int]) -> None:
        self.names = names
        self.lines: list[str] = []
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(16)
        self.port = self.sock.getsockname()[1]
        threading.Thread(target=self._accept, daemon=True).start()

    def close(self) -> None:
        """Stop accepting connections."""
        self.sock.close()

    def _accept(self) -> None:
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self._serve, args=(conn,), daemon=True).start()

    def _serve(self, conn: socket.socket) -> None:
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = conn.recv(4096)
            if not chunk:
                conn.close()
                return
            head += chunk
        line = head.split(b"\r\n", 1)[0].decode()
        self.lines.append(line)
        verb, target, _ = line.split(" ", 2)
        host, port = target.rsplit(":", 1)
        if verb != "CONNECT" or host not in self.names:
            conn.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            conn.close()
            return
        up = socket.create_connection(("127.0.0.1", self.names[host]))
        conn.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
        for a, b in ((conn, up), (up, conn)):
            threading.Thread(target=_pipe, args=(a, b), daemon=True).start()


def _pipe(src: socket.socket, dst: socket.socket) -> None:
    try:
        while data := src.recv(65536):
            dst.sendall(data)
    except OSError:
        pass
    finally:
        for s in (src, dst):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def write_config(home: Path, homeserver: str, accounts: dict[str, str]) -> None:
    """Write ``config.toml`` and the token files the way provisioning would."""
    d = home / ".config" / "agent-chat"
    d.mkdir(parents=True, exist_ok=True)
    agents = [CLAUDE_A, CODEX_A, CLAUDE_B, CODEX_B]
    lines = [
        f'homeserver = "{homeserver}"',
        f'server_name = "{SERVER}"',
        'room_prefix = "agents-"',
        f'human = "{HUMAN}"',
        "agents = [" + ", ".join(f'"{a}"' for a in agents) + "]",
        "",
        "[accounts]",
        *(f'{tool} = "{acct}"' for tool, acct in accounts.items()),
    ]
    (d / "config.toml").write_text("\n".join(lines) + "\n")
    for acct in accounts.values():
        path = d / f"{acct[1:].split(':')[0]}.token"
        path.write_text(TOKENS[acct] + "\n")
        os.chmod(path, 0o600)


def proc_entry(root: Path, pid: int, ppid: int, argv0: str) -> None:
    """Add ``pid`` to a fake ``/proc`` under ``root``."""
    d = root / str(pid)
    d.mkdir(parents=True, exist_ok=True)
    (d / "stat").write_text(f"{pid} (x y) S {ppid} {pid} {pid} 0 -1\n")
    (d / "cmdline").write_bytes(argv0.encode() + b"\0--flag\0")


def ps_table(path: Path, rows: dict[int, tuple[int, str]]) -> None:
    """Write the table the fake ``ps`` script reads: ``pid ppid args``."""
    path.write_text("".join(f"{p} {pp} {a}\n" for p, (pp, a) in rows.items()))


def fake_ps(directory: Path, table: Path) -> Path:
    """Write a ``ps`` that answers ``ps -o ppid= -o args= -p PID`` from ``table``."""
    script = directory / "ps"
    script.write_text(
        "#!/bin/sh\n"
        f'line=$(grep "^$6 " "{table}") || exit 1\n'
        'echo "$line" | cut -d" " -f2-\n'
    )
    script.chmod(0o755)
    return script


def run(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    *argv: str,
    stdin: str = '{"hook_event_name": "Stop"}',
) -> tuple[int, str, str, io.StringIO]:
    """Run ``agent-chat argv`` in-process; return (code, stdout, stderr, stdin)."""
    src = io.StringIO(stdin)
    monkeypatch.setattr(sys, "stdin", src)
    code = cli.main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err, src
