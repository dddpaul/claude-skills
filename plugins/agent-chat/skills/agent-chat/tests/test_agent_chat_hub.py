"""The hub: the optional ``hub`` key and ``send --hub`` into the shared room.

This project (``proj``) addresses the projects ``beta`` and ``gamma``, whose
rooms this account has not joined. Names are placeholders.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote

import ac_fakes as f
import pytest
from conftest import Host

from agent_chat import config

HUB, HUB_ROOM = f"#agents-hub:{f.SERVER}", "!hub0001:example.test"
BETA, BETA_ROOM = f"#agents-beta:{f.SERVER}", "!beta0001:example.test"
GAMMA, GAMMA_ROOM = f"#agents-gamma:{f.SERVER}", "!gamma001:example.test"
API = "/_matrix/client/v3"


@pytest.fixture
def hub(host: Host) -> Host:
    """The host with ``hub = "agents-hub"``, the hub room and two other projects."""
    f.write_config(
        host.home,
        f"http://127.0.0.1:{host.hs.port}",
        {"claude": f.CLAUDE_A, "codex": f.CODEX_A},
        hub='"agents-hub"',
    )
    host.hs.room(HUB, HUB_ROOM, joined={f.HUMAN, f.CLAUDE_B}, invited={f.CLAUDE_A})
    host.hs.joined[HUB_ROOM].add(f.CODEX_A)
    for alias, room in ((BETA, BETA_ROOM), (GAMMA, GAMMA_ROOM)):
        host.hs.room(alias, room, joined={f.HUMAN, f.CLAUDE_B}, invited={f.CLAUDE_A})
    return host


@pytest.fixture
def box(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The outbox under a private temp root of this test."""
    root = tmp_path / "t"
    monkeypatch.setenv("AGENT_CHAT_TMP", str(root))
    return root / "outbox"


def send(capsys, monkeypatch, *argv: str, text: str = "hello") -> tuple[int, str, str]:
    code, out, err, _ = f.run(capsys, monkeypatch, "send", *argv, stdin=text)
    return code, out, err


def refused(host: Host, code: int, out: str, err: str) -> None:
    """One line on stderr, a non-zero exit, nothing posted and no target joined."""
    assert code != 0 and out == ""
    assert err.startswith("agent-chat: ") and err.count("\n") == 1, err
    assert "nothing was sent" in err or "config" in err, err
    assert host.hs.paths("PUT") == []
    hub_join = f"{API}/join/{quote(HUB, safe='')}"
    joins = [p for p in host.hs.paths("POST") if p.startswith(f"{API}/join/")]
    assert set(joins) <= {hub_join}


def resolved(host: Host) -> list[str]:
    """The aliases this test looked up, in order."""
    head = f"{API}/directory/room/"
    return [
        p.removeprefix(head).replace("%23", "#").replace("%3A", ":")
        for p in host.hs.paths("GET")
        if p.startswith(head)
    ]


# The hub key


def test_without_a_hub_send_hub_refuses_and_a_plain_send_is_unchanged(
    host: Host, capsys, monkeypatch
) -> None:
    host.hs.room(HUB, HUB_ROOM, joined={f.CLAUDE_A}, invited=set())
    assert config.load_config().hub is None
    code, out, err = send(capsys, monkeypatch, "--hub", "--project", "beta")
    refused(host, code, out, err)
    assert "names no hub" in err
    assert host.hs.requests == []
    assert send(capsys, monkeypatch, text="plain")[0] == 0
    [msg] = host.hs.messages(f.ROOM)
    assert msg["content"] == {
        "msgtype": "m.text",
        "body": "plain",
        "m.mentions": {"user_ids": []},
    }


@pytest.mark.parametrize(
    ("value", "why"),
    [
        ("5", "hub must be a string"),
        ('["agents-hub"]', "hub must be a string"),
        ('"other-hub"', "starts with 'agents-'"),
        ('"agents-"', "and then letters"),
        ('"agents-a b"', "and then letters"),
    ],
)
def test_a_bad_hub_is_a_config_error(
    host: Host, capsys, monkeypatch, value: str, why: str
) -> None:
    f.write_config(
        host.home,
        f"http://127.0.0.1:{host.hs.port}",
        {"claude": f.CLAUDE_A},
        hub=value,
    )
    with pytest.raises(config.AgentChatError, match=why):
        config.load_config()
    code, out, err = send(capsys, monkeypatch, text="x")
    refused(host, code, out, err)
    assert why in err


def test_the_hub_key_names_the_hub_and_its_project(hub: Host) -> None:
    cfg = config.load_config()
    assert (cfg.hub, cfg.hub_alias, cfg.hub_project) == ("agents-hub", HUB, "hub")


# Refusals


@pytest.mark.parametrize(
    ("project", "why"),
    [
        ("be ta", "is not a project"),
        ("beta,", "is not a project"),
        ("beta,@claude-b", "is not a project"),
        ("Beta", "has no room #agents-Beta:"),
        ("beta,delta", "--project delta has no room #agents-delta:"),
        (f.PROJECT, f"--project {f.PROJECT} is this project"),
        ("beta,hub", "--project hub is the hub"),
    ],
)
def test_send_hub_refuses_a_bad_target(
    hub: Host, capsys, monkeypatch, project: str, why: str
) -> None:
    code, out, err = send(capsys, monkeypatch, "--hub", "--project", project)
    refused(hub, code, out, err)
    assert why in err


def test_targets_are_resolved_but_never_joined(hub: Host, capsys, monkeypatch) -> None:
    code, _, err = send(capsys, monkeypatch, "--hub", "--project", "beta,gamma")
    assert code == 0, err
    assert set(resolved(hub)) >= {BETA, GAMMA, f.ALIAS, HUB}
    joins = [p for p in hub.hs.paths("POST") if p.startswith(f"{API}/join/")]
    assert joins == [f"{API}/join/{quote(HUB, safe='')}"]
    assert f.CLAUDE_A not in hub.hs.joined[BETA_ROOM] | hub.hs.joined[GAMMA_ROOM]


def test_send_hub_refuses_when_this_projects_room_does_not_resolve(
    hub: Host, capsys, monkeypatch
) -> None:
    del hub.hs.aliases[f.ALIAS]
    code, out, err = send(capsys, monkeypatch, "--hub", "--project", "beta")
    refused(hub, code, out, err)
    assert f"this project has no room {f.ALIAS}" in err


def test_a_project_that_cannot_be_named_in_the_hub_cannot_send_to_it(
    hub: Host, tmp_path: Path, capsys, monkeypatch
) -> None:
    there = tmp_path / "work" / "my proj"
    there.mkdir()
    monkeypatch.chdir(there)
    hub.hs.room(
        f"#agents-my proj:{f.SERVER}", "!odd0001:example.test", {f.CLAUDE_A}, set()
    )
    code, out, err = send(capsys, monkeypatch, "--hub", "--project", "beta")
    refused(hub, code, out, err)
    assert "this project's name 'my proj' cannot be named in the hub" in err


@pytest.mark.parametrize(
    "argv",
    [["--hub", "--project", "beta"], ["--hub", "--thread", "abc"], []],
    ids=["hub", "hub-thread", "plain"],
)
def test_the_hubs_own_directory_cannot_send(
    hub: Host, tmp_path: Path, capsys, monkeypatch, argv: list[str]
) -> None:
    there = tmp_path / "work" / "hub"
    there.mkdir()
    monkeypatch.chdir(there)
    code, out, err = send(capsys, monkeypatch, *argv)
    refused(hub, code, out, err)
    assert f"this project's room {HUB} is the hub" in err


@pytest.mark.parametrize(
    ("argv", "why"),
    [
        (["--hub", "--to", "claude-b"], "--hub --to needs --project"),
        (["--hub", "--thread", "abc", "--to", "claude-b"], "--to needs --project"),
        (["--hub"], "--hub needs --project, or --thread"),
        (["--project", "beta"], "--project needs --hub"),
        (["--project", "be ta"], "--project needs --hub"),
    ],
)
def test_send_hub_refuses_a_missing_address(
    hub: Host, capsys, monkeypatch, argv: list[str], why: str
) -> None:
    code, out, err = send(capsys, monkeypatch, *argv)
    refused(hub, code, out, err)
    assert code == 2 and why in err
    assert hub.hs.requests == []


# What a hub send posts


def test_a_hub_send_carries_the_prefix_the_field_and_the_mentions(
    hub: Host, capsys, monkeypatch
) -> None:
    code, out, err = send(
        capsys,
        monkeypatch,
        "--hub",
        "--project",
        "beta,gamma",
        "--to",
        "claude-b",
        text="which version?\n",
    )
    assert (code, err) == (0, "")
    [msg] = hub.hs.messages(HUB_ROOM)
    assert msg["sender"] == f.CLAUDE_A
    assert msg["content"] == {
        "msgtype": "m.text",
        "body": f"{f.PROJECT} → beta, gamma: @claude-b: which version?",
        "m.mentions": {"user_ids": [f.CLAUDE_B]},
        "agent_chat.hub": {"v": 1, "from": f.PROJECT, "to": ["beta", "gamma"]},
    }
    assert out == f"sent to {HUB} as {f.CLAUDE_A}: {msg['event_id'][1:]}\n"
    assert hub.hs.messages(f.ROOM) == []


def test_repeated_projects_are_named_once(hub: Host, capsys, monkeypatch) -> None:
    assert send(capsys, monkeypatch, "--hub", "--project", "beta, gamma,beta")[0] == 0
    [msg] = hub.hs.messages(HUB_ROOM)
    assert msg["content"]["agent_chat.hub"]["to"] == ["beta", "gamma"]
    assert msg["content"]["body"] == f"{f.PROJECT} → beta, gamma: hello"


def thread_child(hs: f.FakeHomeserver, root: str, body: str) -> str:
    rel = {"rel_type": "m.thread", "event_id": root}
    return hs.add(
        HUB_ROOM, f.HUMAN, {"msgtype": "m.text", "body": body, "m.relates_to": rel}
    )


def test_a_hub_thread_reply_for_the_user_has_an_empty_to(
    hub: Host, capsys, monkeypatch
) -> None:
    root = hub.hs.post(HUB_ROOM, f.HUMAN, f"{f.PROJECT}: status?")
    latest = thread_child(hub.hs, root, "and the tests?")
    code, out, err = send(capsys, monkeypatch, "--hub", "--thread", latest[1:])
    assert (code, err) == (0, "")
    msg = hub.hs.messages(HUB_ROOM)[-1]
    assert msg["content"] == {
        "msgtype": "m.text",
        "body": f"{f.PROJECT}: hello",
        "m.mentions": {"user_ids": []},
        "agent_chat.hub": {"v": 1, "from": f.PROJECT, "to": []},
        "m.relates_to": {
            "rel_type": "m.thread",
            "event_id": root,
            "is_falling_back": True,
            "m.in_reply_to": {"event_id": latest},
        },
    }
    assert out == (
        f"sent to {HUB} as {f.CLAUDE_A} in thread {root[1:]}: {msg['event_id'][1:]}\n"
    )


def test_a_hub_thread_send_with_projects_posts_into_the_thread(
    hub: Host, capsys, monkeypatch
) -> None:
    root = hub.hs.post(HUB_ROOM, f.HUMAN, f"{f.PROJECT}: ask beta")
    argv = ("--hub", "--thread", root, "--project", "beta", "--to", "claude-b")
    assert send(capsys, monkeypatch, *argv)[0] == 0
    content = hub.hs.messages(HUB_ROOM)[-1]["content"]
    assert content["body"] == f"{f.PROJECT} → beta: @claude-b: hello"
    assert content["agent_chat.hub"] == {"v": 1, "from": f.PROJECT, "to": ["beta"]}
    assert content["m.relates_to"]["event_id"] == root


def test_the_thread_root_refusals_apply_in_the_hub(
    hub: Host, capsys, monkeypatch
) -> None:
    top = hub.hs.post(HUB_ROOM, f.HUMAN, "top")
    nested_root = thread_child(hub.hs, top, "a child posing as a root")
    rel = {"rel_type": "m.thread", "event_id": nested_root}
    nested = hub.hs.add(
        HUB_ROOM, f.HUMAN, {"msgtype": "m.text", "body": "x", "m.relates_to": rel}
    )
    cases = {
        hub.hs.post(HUB_ROOM, f.HUMAN, "* fix", edit=True): "m.replace",
        nested: "not a top-level message",
        "$nosuchevent": "no such event",
    }
    # The project room's events are no roots in the hub.
    cases[hub.hs.post(f.ROOM, f.HUMAN, "elsewhere")] = "no such event"
    for event, why in cases.items():
        code, out, err = send(capsys, monkeypatch, "--hub", "--thread", event[1:])
        refused(hub, code, out, err)
        assert why in err, event


# The Codex form


def test_the_codex_form_posts_the_same_message(
    hub: Host, box: Path, capsys, monkeypatch
) -> None:
    f.run(capsys, monkeypatch, "prepare-message", "x.txt")
    (box / "x.txt").write_text("which version?\n")
    code, out, err, _ = f.run(
        capsys,
        monkeypatch,
        "send",
        "--as",
        "codex",
        "--message-file",
        "x.txt",
        "--hub",
        "--project",
        "beta",
        "--to",
        "claude-b",
    )
    assert (code, err) == (0, "")
    assert send(capsys, monkeypatch, *codex_argv(), text="which version?")[0] == 0
    codex, claude = hub.hs.messages(HUB_ROOM)
    assert (codex["sender"], claude["sender"]) == (f.CODEX_A, f.CLAUDE_A)
    assert codex["content"] == claude["content"]
    assert codex["content"]["agent_chat.hub"] == {
        "v": 1,
        "from": f.PROJECT,
        "to": ["beta"],
    }
    assert out.startswith(f"sent to {HUB} as {f.CODEX_A}: ")
    assert not (box / "x.txt").exists()


def codex_argv() -> tuple[str, ...]:
    """The Claude form of the Codex send above."""
    return ("--hub", "--project", "beta", "--to", "claude-b")


def test_a_refused_codex_hub_send_keeps_the_prepared_file(
    hub: Host, box: Path, capsys, monkeypatch
) -> None:
    f.run(capsys, monkeypatch, "prepare-message", "y.txt")
    (box / "y.txt").write_text("hello")
    argv: Any = ("--as", "codex", "--message-file", "y.txt", "--hub")
    code, out, err = send(capsys, monkeypatch, *argv, "--project", "delta")
    refused(hub, code, out, err)
    assert (box / "y.txt").read_text() == "hello"
