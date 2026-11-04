"""The wire: the token stays off argv, stdin bodies, the proxy, 401s and retries."""

from __future__ import annotations

import http.client
import json
import os
import shutil
import socket
import ssl
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import ac_fakes as f
import pytest
from conftest import Host, Owner, PsOwner

from agent_chat import cli, config, matrix, note, threads
from agent_chat.listen import SyncLoop
from agent_chat.matrix import AuthError, Client, NetworkError

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
        [sys.executable, str(BIN), "send", "--to", "codex-a", "--to", "@claude-b"],
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
    assert msg["content"]["body"] == f"@codex-a @claude-b: {body}"
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


def test_a_long_backoff_stops_within_a_second_once_the_owner_is_gone() -> None:
    clock = [0.0]

    def sleep(s: float) -> None:
        clock[0] += s

    client = Client(
        "http://matrix.example.test",
        "unused",
        env={},
        sleep=sleep,
        now=lambda: clock[0],
    )
    client.keep_going = lambda: clock[0] < 2.5
    assert client._pause(30) is False
    assert clock[0] <= 3.0


# Threads


def thread(root: str) -> dict[str, Any]:
    """The ``m.relates_to`` of a thread child of ``root``."""
    return {"rel_type": "m.thread", "event_id": root}


def child(hs: f.FakeHomeserver, root: str, body: str) -> str:
    """Post a thread child of ``root`` from the human; return its ID."""
    content = {"msgtype": "m.text", "body": body, "m.relates_to": thread(root)}
    return hs.add(f.ROOM, f.HUMAN, content)


def send_thread(capsys, monkeypatch, thread_id: str) -> tuple[int, str, str]:
    code, out, err, _ = f.run(
        capsys,
        monkeypatch,
        "send",
        "--to",
        "codex-a",
        "--thread",
        thread_id,
        stdin="re",
    )
    return code, out, err


def test_a_thread_send_on_a_top_level_message_starts_its_thread(
    host: Host, capsys, monkeypatch
) -> None:
    root = host.hs.post(f.ROOM, f.HUMAN, "the plan")
    code, out, err = send_thread(capsys, monkeypatch, root[1:])
    assert (code, err) == (0, "")
    msg = host.hs.messages(f.ROOM)[-1]
    assert msg["content"] == {
        "msgtype": "m.text",
        "body": "@codex-a: re",
        "m.mentions": {"user_ids": [f.CODEX_A]},
        "m.relates_to": {
            "rel_type": "m.thread",
            "event_id": root,
            "is_falling_back": True,
            "m.in_reply_to": {"event_id": root},
        },
    }
    assert out == (
        f"sent to {f.ALIAS} as {f.CLAUDE_A} in thread {root[1:]}: "
        f"{msg['event_id'][1:]}\n"
    )


def test_a_thread_send_on_a_child_replies_to_the_latest_message_of_its_root(
    host: Host, capsys, monkeypatch
) -> None:
    root = host.hs.post(f.ROOM, f.HUMAN, "the plan")
    first = child(host.hs, root, "one")
    host.hs.post(f.ROOM, f.HUMAN, "elsewhere")
    latest = child(host.hs, root, "two")
    code, out, _ = send_thread(capsys, monkeypatch, first[1:])
    assert code == 0
    rel = host.hs.messages(f.ROOM)[-1]["content"]["m.relates_to"]
    assert rel["event_id"] == root
    assert rel["m.in_reply_to"] == {"event_id": latest}
    assert f" in thread {root[1:]}: " in out
    [lookup] = [p for p in host.hs.paths("GET") if "/relations/" in p]
    assert lookup.startswith("/_matrix/client/v1/rooms/")
    assert lookup.endswith(f"/relations/%24{root[1:]}/m.thread/m.room.message")
    [query] = [q for _, p, q, _ in host.hs.requests if "/relations/" in p]
    assert (query["dir"], query["limit"]) == (["b"], ["50"])


def test_a_thread_send_on_a_rich_reply_makes_it_the_root(
    host: Host, capsys, monkeypatch
) -> None:
    first = host.hs.post(f.ROOM, f.HUMAN, "question")
    reply = host.hs.add(
        f.ROOM,
        f.CLAUDE_B,
        {
            "msgtype": "m.text",
            "body": "answer",
            "m.relates_to": {"m.in_reply_to": {"event_id": first}},
        },
    )
    assert send_thread(capsys, monkeypatch, reply[1:])[0] == 0
    rel = host.hs.messages(f.ROOM)[-1]["content"]["m.relates_to"]
    assert rel["event_id"] == rel["m.in_reply_to"]["event_id"] == reply


def _refused_ids(hs: f.FakeHomeserver) -> dict[str, tuple[str, str]]:
    """Each refused case: (its --thread value, a phrase of the refusal)."""
    text = {"msgtype": "m.text", "body": "x"}
    top = hs.post(f.ROOM, f.HUMAN, "top")
    nested_root = child(hs, top, "a child posing as a root")
    nested = hs.add(f.ROOM, f.HUMAN, {**text, "m.relates_to": thread(nested_root)})
    redaction = {"redacted_because": {"type": "m.room.redaction"}}
    ids = {
        "edit": (hs.post(f.ROOM, f.HUMAN, "* fix", edit=True), "m.replace"),
        "reaction": (
            hs.add(
                f.ROOM,
                f.HUMAN,
                {"m.relates_to": {"rel_type": "m.annotation", "event_id": top}},
                etype="m.reaction",
            ),
            "not a message",
        ),
        "reference": (
            hs.add(
                f.ROOM,
                f.HUMAN,
                {**text, "m.relates_to": {"rel_type": "m.reference", "event_id": top}},
            ),
            "m.reference",
        ),
        "redacted": (hs.add(f.ROOM, f.HUMAN, text, unsigned=redaction), "redacted"),
        "empty": (hs.add(f.ROOM, f.HUMAN, {}), "empty"),
        "state": (
            hs.add(f.ROOM, f.HUMAN, {"topic": "t"}, "m.room.topic"),
            "not a message",
        ),
        "unknown": ("$nosuchevent", "no such event"),
        "nested": (nested, "not a top-level message"),
    }
    return {k: (v[1:], why) for k, (v, why) in ids.items()}


@pytest.mark.parametrize(
    "case",
    [
        "edit",
        "reaction",
        "reference",
        "redacted",
        "empty",
        "state",
        "unknown",
        "nested",
    ],
)
def test_a_thread_send_refuses_an_event_that_cannot_root_a_thread(
    host: Host, capsys, monkeypatch, case: str
) -> None:
    thread_id, why = _refused_ids(host.hs)[case]
    before = len(host.hs.events)
    code, out, err = send_thread(capsys, monkeypatch, thread_id)
    assert code != 0 and out == ""
    assert why in err and "nothing was sent" in err and err.count("\n") == 1
    assert len(host.hs.events) == before
    assert host.hs.paths("PUT") == []


@pytest.mark.parametrize("bad", ["$$x", "a b", "x:y", "", "$", "x/y"])
def test_a_thread_send_refuses_a_malformed_id_with_exit_2(
    host: Host, capsys, monkeypatch, bad: str
) -> None:
    code, out, err = send_thread(capsys, monkeypatch, bad)
    assert (code, out) == (2, "")
    assert "is not an event ID" in err and err.count("\n") == 1
    assert host.hs.requests == []


def test_a_missing_relations_endpoint_fails_the_send_and_keeps_the_room(
    host: Host, capsys, monkeypatch
) -> None:
    root = host.hs.post(f.ROOM, f.HUMAN, "the plan")
    host.hs.no_relations = True
    code, out, err = send_thread(capsys, monkeypatch, root[1:])
    assert (code, out) == (1, "")
    assert "thread lookup failed" in err and err.count("\n") == 1
    assert host.hs.paths("PUT") == []
    assert len([p for p in host.hs.paths() if "/directory/room/" in p]) == 1


def test_a_thread_id_with_or_without_its_dollar_gives_the_same_post(
    host: Host, capsys, monkeypatch
) -> None:
    root = host.hs.post(f.ROOM, f.HUMAN, "the plan")
    posts = []
    for given in (root, root[1:]):
        assert send_thread(capsys, monkeypatch, given)[0] == 0
        posts.append(host.hs.events.pop()[1])  # the next send sees no reply
    assert posts[0]["content"] == posts[1]["content"]
    assert posts[0]["content"]["m.relates_to"]["event_id"] == root
    paths = host.hs.paths()
    assert (
        f"/_matrix/client/v3/rooms/%21room0001%3Aexample.test/event/%24{root[1:]}"
        in paths
    )
    assert not [p for p in paths if set("$!:") & set(p)]


def test_a_plain_send_prints_its_event_id_without_the_dollar(
    host: Host, capsys, monkeypatch
) -> None:
    code, out, _, _ = f.run(capsys, monkeypatch, "send", stdin="hi")
    [msg] = host.hs.messages(f.ROOM)
    assert code == 0
    assert out == f"sent to {f.ALIAS} as {f.CLAUDE_A}: {msg['event_id'][1:]}\n"
    assert "m.relates_to" not in msg["content"]


# Thread lookups on receiving


def reader(host: Host, account: str) -> SyncLoop:
    """A sync loop for ``account`` whose mail() reads the fake server."""
    cfg = config.load_config()
    client = Client(cfg.homeserver, f.TOKENS[account])
    return SyncLoop(client, cfg, account, host.state(account), "t")


def room_events(hs: f.FakeHomeserver) -> list[dict[str, Any]]:
    return [e for r, e in hs.events if r == f.ROOM]


def in_thread(
    hs: f.FakeHomeserver, sender: str, root: str, body: str, to: list[str] = ()
) -> str:
    content = {
        "msgtype": "m.text",
        "body": body,
        "m.relates_to": thread(root),
        "m.mentions": {"user_ids": list(to)},
    }
    return hs.add(f.ROOM, sender, content)


def bodies(loop: SyncLoop, hs: f.FakeHomeserver, budget=None) -> list[str]:
    budget = budget or loop.budget()
    return [m.body for m in loop.mail(f.ROOM, room_events(hs), budget)]


def test_only_the_newest_50_thread_events_make_the_threads_agents(
    host: Host,
) -> None:
    hs = host.hs
    root = hs.post(f.ROOM, f.HUMAN, "plan?")
    in_thread(hs, f.CLAUDE_A, root, "early")  # pushed out of the window below
    for n in range(48):
        in_thread(hs, f.HUMAN, root, f"h{n}")
    in_thread(hs, f.CLAUDE_B, root, "recent")
    in_thread(hs, f.HUMAN, root, "so?")
    assert bodies(reader(host, f.CLAUDE_B), hs)[-1:] == ["so?"]
    assert "so?" not in bodies(reader(host, f.CLAUDE_A), hs)
    [rel] = [q for _, p, q, _ in hs.requests if "/relations/" in p][:1]
    assert (rel["dir"], rel["limit"]) == (["b"], ["50"])


def test_a_failed_lookup_delivers_mail_and_is_asked_once_per_batch(
    host: Host,
) -> None:
    hs = host.hs
    root = hs.post(f.ROOM, f.HUMAN, "plan?")
    in_thread(hs, f.CLAUDE_B, root, "mine")
    hs.no_relations = True
    in_thread(hs, f.HUMAN, root, "@claude-a: yours", [f.CLAUDE_A])
    in_thread(hs, f.HUMAN, root, "anyone?")
    loop = reader(host, f.CLAUDE_A)
    mail = loop.mail(f.ROOM, room_events(hs), loop.budget())
    assert [m.body for m in mail] == ["plan?", "@claude-a: yours", "anyone?"]
    assert mail[1].thread is mail[2].thread and not mail[1].thread.read
    assert len([p for p in hs.lookups() if "/relations/" in p]) == 1
    assert len([p for p in hs.lookups() if "/event/" in p]) == 1


def test_a_lookup_is_tried_at_most_twice(host: Host) -> None:
    hs = host.hs
    root = hs.post(f.ROOM, f.CLAUDE_B, "mine")
    hs.lookup_fault = "drop"
    in_thread(hs, f.HUMAN, root, "anyone?")
    assert bodies(reader(host, f.CLAUDE_A), hs) == ["anyone?"]
    assert len(hs.lookups()) == 2


def test_a_spent_budget_delivers_addressed_mail_and_wakes_every_listener(
    host: Host,
) -> None:
    hs = host.hs
    root = hs.post(f.ROOM, f.CLAUDE_B, "mine")
    in_thread(hs, f.HUMAN, root, "@claude-a: yours", [f.CLAUDE_A])
    in_thread(hs, f.HUMAN, root, "anyone?")
    loop = reader(host, f.CLAUDE_A)
    spent = threads.Budget(loop.client, loop.cfg, seconds=0)
    assert bodies(loop, hs, spent) == ["@claude-a: yours", "anyone?"]
    assert hs.lookups() == []


def test_a_lookup_during_an_outage_ends_within_the_budget(host: Host) -> None:
    hs = host.hs
    root = hs.post(f.ROOM, f.CLAUDE_B, "mine")
    in_thread(hs, f.HUMAN, root, "anyone?")
    other = hs.post(f.ROOM, f.CLAUDE_B, "another")
    in_thread(hs, f.HUMAN, other, "and here?")
    hs.lookup_fault = "stall"
    loop = reader(host, f.CLAUDE_A)
    started = time.monotonic()
    budget = threads.Budget(loop.client, loop.cfg, seconds=0.5)
    assert bodies(loop, hs, budget) == ["anyone?", "and here?"]
    assert time.monotonic() - started < 1.5
    assert len(hs.lookups()) == 1, "a spent budget asks the server no more"


def test_a_401_during_a_lookup_is_raised(host: Host) -> None:
    hs = host.hs
    root = hs.post(f.ROOM, f.CLAUDE_B, "mine")
    in_thread(hs, f.HUMAN, root, "anyone?")
    hs.lookup_fault = "401"
    with pytest.raises(AuthError):
        bodies(reader(host, f.CLAUDE_A), hs)


def test_a_401_during_a_lookup_makes_hook_wait_log_once_and_exit_0(
    host: Host, owner: Owner, capsys, monkeypatch
) -> None:
    f.run(capsys, monkeypatch, "hook-wait", "--seconds", "0.1")
    root = host.hs.post(f.ROOM, f.CLAUDE_B, "mine")
    host.hs.lookup_fault = "401"
    in_thread(host.hs, f.HUMAN, root, "anyone?")
    assert f.run(capsys, monkeypatch, "hook-wait", "--seconds", "5")[:3] == (0, "", "")
    lines = (host.state() / "log").read_text().splitlines()
    assert len(lines) == 1 and "M_UNKNOWN_TOKEN" in lines[0]


def test_hook_wait_delivers_through_a_lookup_outage(
    host: Host, owner: Owner, capsys, monkeypatch
) -> None:
    monkeypatch.setattr(threads, "BUDGET_SECONDS", 0.5)
    f.run(capsys, monkeypatch, "hook-wait", "--seconds", "0.1")
    root = host.hs.post(f.ROOM, f.CLAUDE_B, "mine")
    host.hs.lookup_fault = "stall"
    in_thread(host.hs, f.HUMAN, root, "anyone?")
    started = time.monotonic()
    code, _, err, _ = f.run(capsys, monkeypatch, "hook-wait", "--seconds", "20")
    assert code == 2 and time.monotonic() - started < 5
    rid = root[1:]
    assert f"Thread {rid} (could not be read; reply with --thread {rid}):" in err
    assert "> anyone?" in err


# A relations answer that also lists the threads of rich replies to the root


def rich_reply(hs: f.FakeHomeserver, sender: str, to: str, body: str) -> str:
    """Post a rich reply to ``to`` (``m.in_reply_to`` only); return its ID."""
    content = {
        "msgtype": "m.text",
        "body": body,
        "m.relates_to": {"m.in_reply_to": {"event_id": to}},
    }
    return hs.add(f.ROOM, sender, content)


def nested_thread(hs: f.FakeHomeserver) -> tuple[str, list[str], str]:
    """Root G with replies C1, C2 and a rich reply R to G with reply C3.

    Returns:
        G, [C1, C2] and C3.
    """
    root = hs.post(f.ROOM, f.HUMAN, "plan?")
    own = [child(hs, root, "c1"), child(hs, root, "c2")]
    reply = rich_reply(hs, f.HUMAN, root, "answer")
    return root, own, child(hs, reply, "c3")


def ids(chunk: list[dict[str, Any]]) -> list[str]:
    return [e["event_id"] for e in chunk]


def test_the_fake_server_lists_a_rich_replys_thread_after_the_roots_own(
    host: Host,
) -> None:
    hs = host.hs
    root, (c1, c2), c3 = nested_thread(hs)
    hs.nested_relations = "after"
    client = Client(config.load_config().homeserver, f.TOKENS[f.CLAUDE_A])
    path = f"/_matrix/client/v1/rooms/{f.ROOM}/relations/{root}/m.thread"
    for limit, want in (("3", [c2, c1, c3]), ("1", [c2])):
        got = client.request(
            "GET", path, query={"dir": "b", "limit": limit}, deadline=time.time() + 5
        )
        assert ids(got["chunk"]) == want


def test_a_thread_lookup_keeps_only_the_roots_own_replies_newest_first(
    host: Host,
) -> None:
    hs = host.hs
    root, (c1, c2), _ = nested_thread(hs)
    hs.nested_relations = "after"
    client = Client(config.load_config().homeserver, f.TOKENS[f.CLAUDE_A])
    got, chunk = client.thread(f.ROOM, root, client.now() + 5)
    assert got["event_id"] == root
    assert ids(chunk) == [c2, c1]


def test_a_thread_send_replies_to_the_roots_own_latest_whatever_the_order(
    host: Host, capsys, monkeypatch
) -> None:
    hs = host.hs
    root, (_, c2), _ = nested_thread(hs)
    hs.nested_relations = "first"
    assert send_thread(capsys, monkeypatch, root[1:])[0] == 0
    rel = hs.messages(f.ROOM)[-1]["content"]["m.relates_to"]
    assert rel["event_id"] == root
    assert rel["m.in_reply_to"] == {"event_id": c2}


def test_a_thread_send_replies_to_the_root_when_none_of_the_window_belongs(
    host: Host, capsys, monkeypatch
) -> None:
    hs = host.hs
    root = hs.post(f.ROOM, f.HUMAN, "plan?")
    child(hs, root, "pushed out of the window")
    reply = rich_reply(hs, f.HUMAN, root, "answer")
    for n in range(50):
        child(hs, reply, f"n{n}")
    hs.nested_relations = "first"
    assert send_thread(capsys, monkeypatch, root[1:])[0] == 0
    rel = hs.messages(f.ROOM)[-1]["content"]["m.relates_to"]
    assert rel["event_id"] == rel["m.in_reply_to"]["event_id"] == root


def test_a_rich_replys_thread_neither_joins_nor_feeds_the_roots_thread(
    host: Host,
) -> None:
    hs = host.hs
    hs.nested_relations = "after"
    root = hs.post(f.ROOM, f.HUMAN, "plan?", mentions=[f.CODEX_A])
    in_thread(hs, f.CLAUDE_B, root, "mine")
    reply = rich_reply(hs, f.HUMAN, root, "answer")
    in_thread(hs, f.CLAUDE_A, reply, "nested")
    in_thread(hs, f.HUMAN, root, "anyone?")
    assert "anyone?" not in bodies(reader(host, f.CLAUDE_A), hs)
    assert bodies(reader(host, f.CLAUDE_B), hs)[-1:] == ["anyone?"]
    loop = reader(host, f.CODEX_A)
    mail = [
        m
        for m in loop.mail(f.ROOM, room_events(hs), loop.budget())
        if m.body == "anyone?"
    ]
    text = note.render(mail, loop.cfg, f.CODEX_A, f.ALIAS)
    assert "Earlier in this thread" in text and "> mine" in text
    assert "nested" not in text


# The bounded mode's total deadline

OK = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{}"
HEAD = b"HTTP/1.1 200 OK\r\nContent-Length: 1000\r\n\r\n"


class Server:
    """A local server whose answer to every request is ``answer(conn)``."""

    def __init__(self, answer, accept: bool = True) -> None:
        self.sock = socket.create_server(("127.0.0.1", 0), backlog=8)
        self.url = f"http://127.0.0.1:{self.sock.getsockname()[1]}"
        self._answer = answer
        if accept:
            threading.Thread(target=self._serve, daemon=True).start()

    def _serve(self) -> None:
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self._one, args=(conn,), daemon=True).start()

    def _one(self, conn: socket.socket) -> None:
        with conn:
            try:
                conn.recv(65536)
                self._answer(conn)
            except OSError:
                pass

    def close(self) -> None:
        self.sock.close()


def drip(data: bytes, gap: float = 0.02):
    def answer(conn: socket.socket) -> None:
        for i in range(len(data)):
            conn.sendall(data[i : i + 1])
            time.sleep(gap)

    return answer


def bounded(url: str, budget: float, now=time.monotonic) -> float:
    """Run one bounded request; return how long it took to fail."""
    client = Client(url, "unused", env={}, now=now)
    started = time.monotonic()
    with pytest.raises(NetworkError):
        client.request("GET", "/x", deadline=client.now() + budget, tries=2)
    return time.monotonic() - started


@pytest.fixture
def serve():
    servers: list[Server] = []

    def start(answer, accept: bool = True) -> Server:
        servers.append(Server(answer, accept))
        return servers[-1]

    yield start
    for s in servers:
        s.close()


def test_a_dripped_answer_ends_a_bounded_request_by_its_budget(serve) -> None:
    server = serve(drip(OK + b" " * 100))
    assert bounded(server.url, 0.15) < 0.65


@pytest.mark.parametrize(
    "answer",
    [drip(HEAD * 20), lambda conn: (conn.sendall(HEAD), drip(b"x" * 1000)(conn))],
    ids=["slow-headers", "slow-body"],
)
def test_slow_headers_and_a_slow_body_end_by_the_budget(serve, answer) -> None:
    assert bounded(serve(answer).url, 0.3) < 0.8


def test_a_connection_never_accepted_ends_by_the_budget(serve) -> None:
    server = serve(lambda conn: None, accept=False)
    assert bounded(server.url, 0.3) < 0.8


def test_an_answer_completed_after_the_deadline_is_a_failure(serve) -> None:
    answered = threading.Event()

    def answer(conn: socket.socket) -> None:
        answered.set()
        conn.sendall(OK)

    server = serve(answer)
    clock = lambda: 100.0 if answered.is_set() else 0.0  # noqa: E731
    bounded(server.url, 5.0, now=clock)
    unbounded = Client(server.url, "unused", env={})
    assert unbounded.request("GET", "/x", deadline=unbounded.now() + 5) == {}


def test_bounded_requests_leave_no_watchdog_alive(serve) -> None:
    server = serve(lambda conn: conn.sendall(OK))
    client = Client(server.url, "unused", env={})
    for _ in range(50):
        assert client.request("GET", "/x", deadline=client.now() + 5, tries=2) == {}
    alive = [t for t in threading.enumerate() if t.name == "agent-chat-watchdog"]
    assert alive == []


@pytest.mark.skipif(shutil.which("openssl") is None, reason="needs openssl")
def test_a_slow_tunnel_and_tls_handshake_end_by_the_budget(
    serve, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cert, key = tmp_path / "c.pem", tmp_path / "k.pem"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1"]
        + ["-subj", "/CN=matrix.example", "-keyout", key, "-out", cert],
        check=True,
        capture_output=True,
    )
    server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_ctx.load_cert_chain(cert, key)
    client_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    client_ctx.check_hostname = False
    client_ctx.verify_mode = ssl.CERT_NONE
    monkeypatch.setattr(matrix, "tls_context", lambda: client_ctx)

    def proxy(conn: socket.socket) -> None:
        time.sleep(0.2)
        conn.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
        time.sleep(0.15)
        drip(OK + b" " * 100)(server_ctx.wrap_socket(conn, server_side=True))

    url = f"http://127.0.0.1:{serve(proxy).sock.getsockname()[1]}"
    client = Client("https://matrix.example", "unused", env={"HTTPS_PROXY": url})
    started = time.monotonic()
    with pytest.raises(NetworkError):
        client.request("GET", "/x", deadline=client.now() + 0.3, tries=2)
    assert time.monotonic() - started < 0.8
