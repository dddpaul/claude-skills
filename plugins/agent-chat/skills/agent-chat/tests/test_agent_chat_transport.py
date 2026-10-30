"""The wire: the token stays off argv, stdin bodies, the proxy, 401s and retries."""

from __future__ import annotations

import http.client
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import ac_fakes as f
import pytest
from conftest import Host, Owner, PsOwner

from agent_chat import cli
from agent_chat.matrix import Client

BIN = Path(__file__).resolve().parents[3] / "bin" / "agent-chat"


@pytest.fixture
def children(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Record the argv of every child process this test starts."""
    seen: list[list[str]] = []
    real = subprocess.Popen

    class Recording(real):  # type: ignore[misc, valid-type]
        def __init__(self, args: Any, *a: Any, **kw: Any) -> None:
            seen.append([str(x) for x in ([args] if isinstance(args, str) else args)])
            super().__init__(args, *a, **kw)

    def refuse(name: str):
        def spawn(*args: Any, **kwargs: Any) -> None:
            seen.append([name, *map(str, args)])
            raise AssertionError(f"unexpected {name}")

        return spawn

    monkeypatch.setattr(subprocess, "Popen", Recording)
    for name in ("system", "execv", "execve", "execvp", "posix_spawn", "posix_spawnp"):
        monkeypatch.setattr(os, name, refuse(name))
    return seen


def test_the_token_never_reaches_a_command_line(
    host: Host, ps_owner: PsOwner, children: list[list[str]], capsys, monkeypatch
) -> None:
    token = f.TOKENS[f.CLAUDE_A]
    assert f.run(capsys, monkeypatch, "send", "--to", "codex-a", stdin="hi")[0] == 0
    f.run(capsys, monkeypatch, "hook-wait", "--seconds", "0.1")
    host.hs.post(f.ROOM, f.HUMAN, "@claude-a: ping")
    assert f.run(capsys, monkeypatch, "hook-wait", "--seconds", "5")[0] == 2
    assert children, "the ps form must have started ps; nothing was checked"
    assert all(argv[0].endswith("/ps") for argv in children)
    assert not [argv for argv in children if any(token in a for a in argv)]


def test_send_reads_its_body_from_stdin_intact(host: Host) -> None:
    body = 'it\'s "quoted" $(not run) `nor this`\n\n  indented line\nend'
    out = subprocess.run(
        [sys.executable, str(BIN), "send", "--to", "@codex-a", "--to", f.CLAUDE_B],
        input=body,
        capture_output=True,
        text=True,
        cwd=host.project,
        timeout=30,
        check=False,
    )
    assert out.returncode == 0, out.stderr
    assert f.TOKENS[f.CLAUDE_A] not in out.stdout + out.stderr
    [msg] = host.hs.messages(f.ROOM)
    assert msg["content"]["body"] == f"{f.CODEX_A} {f.CLAUDE_B}: {body}"
    assert msg["content"]["m.mentions"] == {"user_ids": [f.CODEX_A, f.CLAUDE_B]}


def test_send_without_to_mentions_nobody(host: Host, capsys, monkeypatch) -> None:
    assert f.run(capsys, monkeypatch, "send", stdin="for the human\n")[0] == 0
    [msg] = host.hs.messages(f.ROOM)
    assert msg["content"] == {
        "msgtype": "m.text",
        "body": "for the human",
        "m.mentions": {"user_ids": []},
    }


def test_send_refuses_an_unknown_account_and_an_empty_body(
    host: Host, capsys, monkeypatch
) -> None:
    code, _, err, _ = f.run(capsys, monkeypatch, "send", "--to", "nobody", stdin="x")
    assert code == 2 and err.count("\n") == 1
    code, _, err, _ = f.run(capsys, monkeypatch, "send", stdin=" \n")
    assert code == 2 and "nothing was sent" in err
    assert host.hs.messages(f.ROOM) == []


def test_the_proxy_is_reached_by_host_name(host: Host, capsys, monkeypatch) -> None:
    name = "matrix.example.test"
    proxy = f.FakeProxy({name: host.hs.port})
    try:
        cfg = host.config / "config.toml"
        cfg.write_text(cfg.read_text().replace("127.0.0.1", name))
        monkeypatch.setenv("HTTPS_PROXY", f"http://127.0.0.1:{proxy.port}")
        real = socket.getaddrinfo

        def no_local_lookup(host_: Any, *a: Any, **kw: Any) -> Any:
            assert host_ != name, "the homeserver name was resolved locally"
            return real(host_, *a, **kw)

        monkeypatch.setattr(socket, "getaddrinfo", no_local_lookup)
        code, _, err, _ = f.run(capsys, monkeypatch, "send", stdin="via the proxy")
        assert code == 0, err
    finally:
        proxy.close()
    assert proxy.lines
    assert set(proxy.lines) == {f"CONNECT {name}:{host.hs.port} HTTP/1.1"}
    assert host.hs.messages(f.ROOM)[0]["content"]["body"] == "via the proxy"


@pytest.mark.parametrize("var", ["HTTPS_PROXY", "https_proxy"])
def test_an_https_homeserver_is_tunnelled_to_port_443(var: str) -> None:
    client = Client(
        "https://matrix.example.test",
        "unused",
        env={var: "http://user:pw@proxy.example.test:3128"},
    )
    conn = client._connection(5)
    assert isinstance(conn, http.client.HTTPSConnection)
    assert (conn.host, conn.port) == ("proxy.example.test", 3128)
    assert (conn._tunnel_host, conn._tunnel_port) == ("matrix.example.test", 443)
    assert conn._tunnel_headers["Proxy-Authorization"].startswith("Basic ")


def test_a_401_makes_hook_wait_log_once_and_exit_0(
    host: Host, owner: Owner, capsys, monkeypatch
) -> None:
    host.hs.revoked.add(f.TOKENS[f.CLAUDE_A])
    for _ in range(3):
        assert f.run(capsys, monkeypatch, "hook-wait", "--seconds", "5")[:3] == (
            0,
            "",
            "",
        )
    lines = (host.state() / "log").read_text().splitlines()
    assert len(lines) == 1 and "M_UNKNOWN_TOKEN" in lines[0]
    assert f.TOKENS[f.CLAUDE_A] not in lines[0]


def test_a_401_makes_send_fail_with_one_line(host: Host, capsys, monkeypatch) -> None:
    host.hs.revoked.add(f.TOKENS[f.CLAUDE_A])
    code, out, err, _ = f.run(capsys, monkeypatch, "send", stdin="x")
    assert code == 1 and out == ""
    assert err.count("\n") == 1 and "401 M_UNKNOWN_TOKEN" in err


def test_an_unknown_room_is_resolved_again_by_the_wait(
    host: Host, owner: Owner, capsys, monkeypatch
) -> None:
    f.run(capsys, monkeypatch, "hook-wait", "--seconds", "0.1")
    codes: list[int] = []
    wait = threading.Thread(
        target=lambda: codes.append(cli.main(["hook-wait", "--seconds", "10"]))
    )
    wait.start()
    time.sleep(0.3)
    # The room was rebuilt: the alias points at a new room this account is invited to.
    new_room = "!room0002:example.test"
    host.hs.room(f.ALIAS, new_room, joined={f.HUMAN}, invited={f.CLAUDE_A})
    host.hs.kick(f.ROOM, f.CLAUDE_A)
    join = f"/_matrix/client/v3/join/%23agents-{f.PROJECT}%3A{f.SERVER}"
    end = time.monotonic() + 5
    while join not in host.hs.paths("POST"):
        assert time.monotonic() < end
        time.sleep(0.02)
    host.hs.post(new_room, f.HUMAN, "@claude-a: in the new room")
    wait.join(15)
    assert codes == [2]
    assert "in the new room" in capsys.readouterr().err


def test_a_network_failure_is_retried_and_the_send_is_not_doubled(
    host: Host, capsys, monkeypatch
) -> None:
    host.hs.drop_next = 2
    assert f.run(capsys, monkeypatch, "send", stdin="one")[0] == 0
    host.hs.lose_answers = 2  # the server posts it, the answer is lost twice
    assert f.run(capsys, monkeypatch, "send", stdin="two")[0] == 0
    assert [m["content"]["body"] for m in host.hs.messages(f.ROOM)] == ["one", "two"]
    puts = host.hs.paths("PUT")
    assert len(puts) == 4 and len(set(puts[1:])) == 1  # the same txnId each time


def test_a_network_failure_is_retried_by_the_wait(
    host: Host, owner: Owner, capsys, monkeypatch
) -> None:
    f.run(capsys, monkeypatch, "hook-wait", "--seconds", "0.1")
    host.hs.post(f.ROOM, f.HUMAN, "@claude-a: through the flaky link")
    host.hs.drop_next = 3
    code, _, err, _ = f.run(capsys, monkeypatch, "hook-wait", "--seconds", "10")
    assert code == 2 and "through the flaky link" in err


def test_retries_stop_at_the_deadline(
    host: Host, owner: Owner, capsys, monkeypatch
) -> None:
    host.hs.drop_next = 10**6
    monkeypatch.setattr(cli, "SEND_SECONDS", 0.3)
    code, out, err, _ = f.run(capsys, monkeypatch, "send", stdin="x")
    assert code == 1 and out == "" and err.count("\n") == 1
    assert "homeserver unreachable" in err
    assert f.run(capsys, monkeypatch, "hook-wait", "--seconds", "0.3")[:3] == (
        0,
        "",
        "",
    )
    assert "homeserver unreachable" in (host.state() / "log").read_text()


def test_an_outage_does_not_keep_an_orphaned_wait_alive(
    host: Host, owner: Owner, capsys, monkeypatch
) -> None:
    f.run(capsys, monkeypatch, "hook-wait", "--seconds", "0.1")
    host.hs.drop_next = 10**6
    codes: list[int] = []
    wait = threading.Thread(
        target=lambda: codes.append(cli.main(["hook-wait", "--seconds", "600"]))
    )
    wait.start()
    time.sleep(0.3)
    owner.exits()
    wait.join(5)
    assert codes == [0], "the wait kept retrying after its Claude was gone"


def test_status_shows_the_account_room_and_wait(
    host: Host, capsys, monkeypatch
) -> None:
    code, out, _, _ = f.run(capsys, monkeypatch, "status")
    assert code == 0
    assert f"account: {f.CLAUDE_A} (claude)" in out
    assert f"room: {f.ALIAS} -> {f.ROOM}" in out
    assert "waiting: no" in out
    assert f.TOKENS[f.CLAUDE_A] not in out


def test_a_room_lost_while_no_wait_ran_is_resolved_again_at_the_start(
    host: Host, owner: Owner, capsys, monkeypatch
) -> None:
    f.run(capsys, monkeypatch, "hook-wait", "--seconds", "0.1")
    new_room = "!room0003:example.test"
    host.hs.kick(f.ROOM, f.CLAUDE_A)
    host.hs.room(f.ALIAS, new_room, joined={f.HUMAN}, invited={f.CLAUDE_A})
    # The cursor is already past the kick: no sync will show it.
    cursor = host.state() / f"agents-{f.PROJECT}.cursor"
    cursor.write_text(json.dumps({"next_batch": f"s{len(host.hs.events)}"}))
    codes: list[int] = []
    wait = threading.Thread(
        target=lambda: codes.append(cli.main(["hook-wait", "--seconds", "10"]))
    )
    wait.start()
    join = f"/_matrix/client/v3/join/%23agents-{f.PROJECT}%3A{f.SERVER}"
    end = time.monotonic() + 5
    while join not in host.hs.paths("POST"):
        assert time.monotonic() < end
        time.sleep(0.02)
    host.hs.post(new_room, f.HUMAN, "@claude-a: found you")
    wait.join(15)
    assert codes == [2]
    assert "found you" in capsys.readouterr().err


def test_the_sync_filter_lets_membership_through(host: Host) -> None:
    from agent_chat.listen import filter_definition

    timeline = filter_definition()["room"]["timeline"]
    assert timeline["types"] == ["m.room.message", "m.room.member"]


def test_a_rejected_cursor_restarts_from_now(
    host: Host, owner: Owner, capsys, monkeypatch
) -> None:
    host.state().mkdir(parents=True)
    cursor = host.state() / f"agents-{f.PROJECT}.cursor"
    cursor.write_text('{"next_batch": "garbage"}')
    assert f.run(capsys, monkeypatch, "hook-wait", "--seconds", "1")[:3] == (0, "", "")
    assert host.cursor() != '{"next_batch": "garbage"}'
    host.hs.post(f.ROOM, f.HUMAN, "@claude-a: back on track")
    code, _, err, _ = f.run(capsys, monkeypatch, "hook-wait", "--seconds", "5")
    assert code == 2 and "back on track" in err


def test_hook_wait_exits_0_when_its_state_cannot_be_written(
    host: Host, owner: Owner, tmp_path: Path, capsys, monkeypatch
) -> None:
    if os.geteuid() == 0:
        pytest.skip("root writes anywhere")
    ro = tmp_path / "ro"
    ro.mkdir(mode=0o500)
    monkeypatch.setenv("XDG_STATE_HOME", str(ro))
    host.hs.post(f.ROOM, f.HUMAN, "@claude-a: x")
    assert f.run(capsys, monkeypatch, "hook-wait", "--seconds", "1")[:3] == (0, "", "")


@pytest.mark.parametrize(
    ("argv", "code", "err"),
    [
        (["hook-wait"], 0, ""),
        (["send"], 1, "agent-chat: needs Python 3.11 or later\n"),
    ],
)
def test_an_old_python_keeps_the_hook_silent(
    capsys, monkeypatch, argv: list[str], code: int, err: str
) -> None:
    import io
    import runpy

    src = io.StringIO('{"hook_event_name": "Stop"}')
    monkeypatch.setattr(sys, "stdin", src)
    monkeypatch.setattr(sys, "version_info", (3, 9, 6))
    monkeypatch.setattr(sys, "argv", [str(BIN), *argv])
    with pytest.raises(SystemExit) as done:
        runpy.run_path(str(BIN), run_name="__main__")
    assert done.value.code == code
    assert capsys.readouterr() == ("", err)
    if argv == ["hook-wait"]:
        assert src.read() == ""
