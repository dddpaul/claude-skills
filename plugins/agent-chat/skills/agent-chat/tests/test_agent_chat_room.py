"""The project's room: the alias, its cache, re-resolving, joining, onboarding."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

import ac_fakes as f
import pytest
from conftest import Host, Owner

from agent_chat.config import AgentChatError, load_config
from agent_chat.matrix import Client
from agent_chat.room import Rooms, project_alias

API = "/_matrix/client/v3"


def enc(alias: str) -> str:
    return quote(alias, safe="")


def lookups(host: Host) -> int:
    return host.hs.paths("GET").count(f"{API}/directory/room/{enc(f.ALIAS)}")


def send(capsys, monkeypatch, text: str = "hello", *extra: str) -> tuple[int, str, str]:
    code, out, err, _ = f.run(capsys, monkeypatch, "send", *extra, stdin=text)
    return code, out, err


def test_the_alias_comes_from_the_physical_cwd(
    host: Host, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    link = tmp_path / "link-with-another-name"
    link.symlink_to(host.project)
    monkeypatch.chdir(link)
    monkeypatch.setenv("PWD", str(link))
    assert project_alias(load_config()) == f"#agents-{f.PROJECT}:{f.SERVER}"


def test_send_resolves_the_alias_and_caches_the_room_id(
    host: Host, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert send(capsys, monkeypatch, "one")[0] == 0
    assert send(capsys, monkeypatch, "two")[0] == 0
    assert lookups(host) == 1
    cache = json.loads((host.state() / "rooms.json").read_text())
    assert cache == {f.ALIAS: f.ROOM}
    assert [m["content"]["body"] for m in host.hs.messages(f.ROOM)] == ["one", "two"]


def test_a_rejected_cached_room_id_is_resolved_again_once(
    host: Host, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    host.state().mkdir(parents=True)
    (host.state() / "rooms.json").write_text(
        json.dumps({f.ALIAS: "!stale:example.test"})
    )
    code, out, err = send(capsys, monkeypatch, "after a rebuild")
    assert code == 0, err
    assert lookups(host) == 1
    assert [m["content"]["body"] for m in host.hs.messages(f.ROOM)] == [
        "after a rebuild"
    ]
    assert json.loads((host.state() / "rooms.json").read_text()) == {f.ALIAS: f.ROOM}


def test_a_room_rejected_twice_fails_the_send(
    host: Host, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    host.hs.kick(f.ROOM, f.CLAUDE_A)  # not joined and not invited: join is refused
    host.state().mkdir(parents=True)
    (host.state() / "rooms.json").write_text(json.dumps({f.ALIAS: f.ROOM}))
    code, out, err = send(capsys, monkeypatch, "x")
    assert code != 0 and out == ""
    assert err.count("\n") == 1 and err.startswith("agent-chat: ")
    assert lookups(host) == 1


def test_an_invited_account_joins_on_first_use(
    host: Host, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    host.hs.joined[f.ROOM].discard(f.CLAUDE_A)
    host.hs.invited[f.ROOM].add(f.CLAUDE_A)
    code, _, err = send(capsys, monkeypatch, "first words")
    assert code == 0, err
    assert host.hs.paths("POST").count(f"{API}/join/{enc(f.ALIAS)}") == 1
    assert f.CLAUDE_A in host.hs.joined[f.ROOM]
    assert host.hs.messages(f.ROOM)[-1]["sender"] == f.CLAUDE_A


def test_a_join_is_never_tried_for_an_alias_without_the_prefix(host: Host) -> None:
    plain = f"#plain:{f.SERVER}"
    host.hs.room(plain, "!plain:example.test", joined=set(), invited={f.CLAUDE_A})
    cfg = load_config()
    host.state().mkdir(parents=True)
    rooms = Rooms(Client(cfg.homeserver, f.TOKENS[f.CLAUDE_A]), cfg, host.state())
    with pytest.raises(AgentChatError, match="not an agent room"):
        rooms.room_id(plain, float("inf"))
    assert f"{API}/join/{enc(plain)}" not in host.hs.paths("POST")


def test_a_project_without_a_room(
    host: Host, owner: Owner, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    elsewhere = tmp_path / "work" / "not-onboarded"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert f.run(capsys, monkeypatch, "hook-wait", "--seconds", "5")[:3] == (0, "", "")
    code, out, err = send(capsys, monkeypatch, "anyone?")
    assert code != 0 and out == ""
    assert err == (
        f"agent-chat: this project has no room #agents-not-onboarded:{f.SERVER} "
        "(not onboarded); nothing was sent\n"
    )
