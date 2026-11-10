"""Hub receiving: the wake rule per (account, project), Claude's wait, note, status.

Sessions are (account, project) pairs; the projects ``alpha``, ``beta`` and
``gamma`` and the hub ``#agents-hub`` are placeholders on the fake homeserver.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import ac_fakes as f
import pytest
from conftest import Host, Owner

from agent_chat import cli, config
from agent_chat.addressing import HUB_FIELD
from agent_chat.listen import Listener
from agent_chat.lock import WaitLock
from agent_chat.matrix import Client
from agent_chat.note import CODEX_REPLY, HubMail, Message, render
from agent_chat.room import room_alias
from agent_chat.threads import observe

HUB, HUB_ROOM = f"#agents-hub:{f.SERVER}", "!hub0001:example.test"
EVERYONE = {f.HUMAN, f.CLAUDE_A, f.CODEX_A, f.CLAUDE_B, f.CODEX_B, f.STRANGER}
PROJECT_ROOMS = {p: f"!{p}0001:example.test" for p in ("alpha", "beta", "gamma")}
A, B, CA = f.CLAUDE_A, f.CLAUDE_B, f.CODEX_A


@pytest.fixture
def hub(host: Host) -> Host:
    """The host with ``hub = "agents-hub"``; everyone is in the hub and the rooms."""
    f.write_config(
        host.home,
        f"http://127.0.0.1:{host.hs.port}",
        {"claude": f.CLAUDE_A, "codex": f.CODEX_A},
        hub='"agents-hub"',
    )
    host.hs.room(HUB, HUB_ROOM, joined=EVERYONE, invited=set())
    for project, room in PROJECT_ROOMS.items():
        alias = f"#agents-{project}:{f.SERVER}"
        host.hs.room(alias, room, joined=EVERYONE, invited=set())
    return host


def listener(
    host: Host, account: str, project: str, logs: list[str] | None = None
) -> Listener:
    cfg = config.load_config()
    client = Client(cfg.homeserver, f.TOKENS[account])
    sink = logs.append if logs is not None else (lambda line: None)
    alias = room_alias(cfg, project)
    return Listener(
        client, cfg, account, config.state_dir(account), alias, project, sink
    )


def hub_events(hs: f.FakeHomeserver) -> list[dict[str, Any]]:
    return [e for r, e in hs.events if r == HUB_ROOM]


def mail(
    host: Host,
    account: str,
    project: str,
    since: int = 0,
    logs: list[str] | None = None,
) -> list[Message]:
    """The hub mail of the session among the hub's events from index ``since``."""
    loop = listener(host, account, project, logs)
    return loop.hub_mail(HUB_ROOM, hub_events(host.hs)[since:], loop.budget())


def woken(host: Host, sessions: list[tuple[str, str]], since: int = 0) -> set:
    return {s for s in sessions if mail(host, *s, since=since)}


def say(
    hs: f.FakeHomeserver,
    sender: str,
    body: str,
    mentions: list[str] | None = None,
    root: str | None = None,
    field: dict[str, Any] | None = None,
) -> str:
    """Post into the hub: a body, its mentions, a thread and a raw hub field."""
    content: dict[str, Any] = {"msgtype": "m.text", "body": body}
    if mentions is not None:
        content["m.mentions"] = {"user_ids": mentions}
    if field is not None:
        content[HUB_FIELD] = field
    if root is not None:
        content["m.relates_to"] = {"rel_type": "m.thread", "event_id": root}
    return hs.add(HUB_ROOM, sender, content)


def agent(
    hs: f.FakeHomeserver,
    sender: str,
    project: str,
    to: list[str],
    body: str,
    accounts: list[str] = (),
    root: str | None = None,
) -> str:
    """Post what ``send --hub`` posts for ``sender`` of ``project``."""
    content = cli.hub_content(body, project, to, list(accounts), f.SERVER)
    if root is not None:
        content["m.relates_to"] = {"rel_type": "m.thread", "event_id": root}
    return hs.add(HUB_ROOM, sender, content)


# The address and the wake rule


def test_the_users_address_wakes_the_named_projects_and_not_alpha(hub: Host) -> None:
    say(hub.hs, f.HUMAN, "beta, gamma: x")
    sessions = [(A, "alpha"), (A, "beta"), (B, "gamma"), (CA, "beta"), (B, "alpha")]
    assert woken(hub, sessions) == {(A, "beta"), (B, "gamma"), (CA, "beta")}


def test_an_account_after_the_colon_narrows_the_address(hub: Host) -> None:
    say(hub.hs, f.HUMAN, "beta: @claude-b x")
    sessions = [(A, "beta"), (B, "beta"), (B, "alpha"), (CA, "beta")]
    assert woken(hub, sessions) == {(B, "beta")}


def test_an_element_pill_narrows_the_address_wherever_it_sits(hub: Host) -> None:
    say(hub.hs, f.HUMAN, "beta: please ask Claude B about it", mentions=[B])
    assert woken(hub, [(A, "beta"), (B, "beta")]) == {(B, "beta")}


@pytest.mark.parametrize(
    "body", ["beta @claude-b: x", "Summary: x", "@claude-b: x", "beta x"]
)
def test_what_is_not_an_address_wakes_nobody(hub: Host, body: str) -> None:
    say(hub.hs, f.HUMAN, body)
    sessions = [(A, "beta"), (B, "beta"), (A, "alpha"), (B, "alpha")]
    assert woken(hub, sessions) == set()


def test_an_agent_message_wakes_its_addressees_and_never_its_own_pair(
    hub: Host,
) -> None:
    agent(hub.hs, A, "beta", ["alpha"], "x")
    assert woken(hub, [(A, "alpha"), (A, "beta"), (B, "beta")]) == {(A, "alpha")}


def test_an_agent_message_naming_its_own_project_skips_only_its_own_pair(
    hub: Host,
) -> None:
    field = {"v": 1, "from": "beta", "to": ["alpha", "beta"]}
    say(hub.hs, A, "beta → alpha, beta: x", mentions=[], field=field)
    sessions = [(A, "alpha"), (A, "beta"), (B, "beta")]
    assert woken(hub, sessions) == {(A, "alpha"), (B, "beta")}


@pytest.mark.parametrize(
    "field",
    [
        None,
        {"v": 2, "from": "beta", "to": ["alpha"]},
        {"v": True, "from": "beta", "to": ["alpha"]},
        {"v": 1, "from": "beta", "to": "alpha"},
        {"v": 1, "from": "beta gamma", "to": ["alpha"]},
    ],
)
def test_an_agent_hub_message_without_a_valid_field_wakes_nobody(
    hub: Host, field: dict[str, Any] | None
) -> None:
    say(hub.hs, B, "beta → alpha: x", field=field)
    say(hub.hs, B, "alpha: x", field=field)
    assert woken(hub, [(A, "alpha"), (B, "alpha"), (CA, "alpha")]) == set()


def test_a_stranger_and_an_edit_wake_nobody(hub: Host) -> None:
    say(hub.hs, f.STRANGER, "alpha: x")
    hub.hs.add(
        HUB_ROOM,
        f.HUMAN,
        {
            "msgtype": "m.text",
            "body": "alpha: x",
            "m.relates_to": {"rel_type": "m.replace", "event_id": "$x"},
        },
    )
    assert woken(hub, [(A, "alpha")]) == set()


def test_the_users_unaddressed_top_level_message_wakes_nobody(hub: Host) -> None:
    say(hub.hs, f.HUMAN, "anyone?")
    assert woken(hub, [(A, "alpha"), (B, "beta")]) == set()


# Threads


def test_a_thread_reply_wakes_the_roots_addressees_and_its_posters(
    hub: Host,
) -> None:
    hs = hub.hs
    root = say(hs, f.HUMAN, "alpha, gamma: @claude-b plan?")
    sessions = [
        (B, "alpha"),
        (B, "gamma"),
        (A, "beta"),
        (A, "alpha"),
        (A, "gamma"),
        (CA, "beta"),
    ]
    assert woken(hub, sessions) == {(B, "alpha"), (B, "gamma")}
    start = len(hub_events(hs))
    agent(hs, A, "beta", [], "beta can help", root=root)
    assert woken(hub, sessions, since=start) == set(), "an empty to wakes nobody"
    start = len(hub_events(hs))
    say(hs, f.HUMAN, "go on", root=root)
    assert woken(hub, sessions, since=start) == {
        (B, "alpha"),
        (B, "gamma"),
        (A, "beta"),
    }


def test_an_agent_root_addresses_its_to_and_mentions(hub: Host) -> None:
    hs = hub.hs
    root = agent(hs, B, "gamma", ["alpha"], "plan?", [A])
    start = len(hub_events(hs))
    say(hs, f.HUMAN, "and?", root=root)
    sessions = [(A, "alpha"), (CA, "alpha"), (B, "gamma"), (B, "alpha")]
    assert woken(hub, sessions, since=start) == {(A, "alpha"), (B, "gamma")}


def test_a_mention_in_an_unaddressed_reply_narrows_the_thread(hub: Host) -> None:
    hs = hub.hs
    root = say(hs, f.HUMAN, "alpha, beta: plan?")
    start = len(hub_events(hs))
    say(hs, f.HUMAN, "@claude-a: yours", root=root)
    sessions = [(A, "alpha"), (A, "beta"), (B, "alpha")]
    assert woken(hub, sessions, since=start) == {(A, "alpha"), (A, "beta")}


def test_an_agents_reply_never_inherits_the_thread(hub: Host) -> None:
    hs = hub.hs
    root = say(hs, f.HUMAN, "alpha, beta: plan?")
    start = len(hub_events(hs))
    agent(hs, A, "alpha", ["gamma"], "gamma?", root=root)
    sessions = [(A, "beta"), (B, "beta"), (B, "gamma")]
    assert woken(hub, sessions, since=start) == {(B, "gamma")}


def test_an_unreadable_thread_wakes_only_explicitly_addressed_mail(
    hub: Host,
) -> None:
    hs = hub.hs
    root = say(hs, f.HUMAN, "alpha: plan?")
    start = len(hub_events(hs))
    say(hs, f.HUMAN, "anyone?", root=root)
    say(hs, f.HUMAN, "alpha: you", root=root)
    hs.lookup_fault = "drop"
    logs: list[str] = []
    got = mail(hub, A, "alpha", since=start, logs=logs)
    assert [m.body for m in got] == ["alpha: you"]
    assert got[0].thread is not None and not got[0].thread.read
    assert len(logs) == 1 and "could not be read" in logs[0] and root in logs[0]


# Claude's wait


def wait(loop: Listener, seconds: float) -> list[Message]:
    return loop.wait(time.monotonic() + seconds, lambda: True).messages


def test_two_waits_of_one_account_each_get_their_projects_mail_once(
    hub: Host,
) -> None:
    alpha, beta = listener(hub, A, "alpha"), listener(hub, A, "beta")
    for loop in (alpha, beta):
        assert wait(loop, 0.3) == []  # starts its cursor at now
    say(hub.hs, f.HUMAN, "alpha: one")
    say(hub.hs, f.HUMAN, "beta: two")
    say(hub.hs, f.HUMAN, "alpha, beta: both")
    assert [m.body for m in wait(alpha, 3)] == ["alpha: one", "alpha, beta: both"]
    assert [m.body for m in wait(beta, 3)] == ["beta: two", "alpha, beta: both"]
    assert wait(alpha, 0.3) == [] and wait(beta, 0.3) == []
    cursors = sorted(p.name for p in hub.state(A).glob("*.cursor"))
    assert cursors == ["agents-alpha.cursor", "agents-beta.cursor"]


def test_the_wait_delivers_hub_and_project_mail_in_one_batch(hub: Host) -> None:
    loop = listener(hub, A, "alpha")
    wait(loop, 0.3)
    hub.hs.post(PROJECT_ROOMS["alpha"], f.HUMAN, "here")
    say(hub.hs, f.HUMAN, "alpha: there")
    got = wait(loop, 3)
    assert [(m.body, m.hub is not None) for m in got] == [
        ("here", False),
        ("alpha: there", True),
    ]


def test_mail_in_the_hub_before_the_join_is_not_delivered(hub: Host) -> None:
    hub.hs.joined[HUB_ROOM].discard(A)
    hub.hs.invited[HUB_ROOM].add(A)
    say(hub.hs, f.HUMAN, "alpha: before")
    loop = listener(hub, A, "alpha")
    wait(loop, 0.3)  # joins the hub and starts the cursor
    hub.hs.joined[HUB_ROOM].discard(A)  # the next wait joins again
    say(hub.hs, f.HUMAN, "alpha: also before")
    assert wait(loop, 1) == []
    say(hub.hs, f.HUMAN, "alpha: after")
    assert [m.body for m in wait(loop, 3)] == ["alpha: after"]


def test_leaving_the_hub_mid_wait_keeps_project_mail_flowing(hub: Host) -> None:
    logs: list[str] = []
    loop = listener(hub, A, "alpha", logs)
    wait(loop, 0.3)
    logs.clear()
    got: list[list[Message]] = []
    t = threading.Thread(target=lambda: got.append(wait(loop, 5)))
    t.start()
    end = time.monotonic() + 3
    while not loop.hub_file.exists():
        assert time.monotonic() < end
        time.sleep(0.02)
    hub.hs.kick(HUB_ROOM, A)
    time.sleep(0.3)
    hub.hs.post(PROJECT_ROOMS["alpha"], f.HUMAN, "still here")
    t.join(10)
    assert [m.body for m in got[0]] == ["still here"]
    assert len(logs) == 1 and "left" in logs[0]


def hub_lines(host: Host) -> list[str]:
    log = host.state() / "log"
    lines = log.read_text().splitlines() if log.exists() else []
    return [line for line in lines if HUB in line]


@pytest.mark.parametrize("trouble", ["unresolvable", "not joinable"])
def test_a_broken_hub_never_blocks_project_mail_and_is_logged_once(
    host: Host, owner: Owner, capsys, monkeypatch, trouble: str
) -> None:
    f.write_config(
        host.home,
        f"http://127.0.0.1:{host.hs.port}",
        {"claude": f.CLAUDE_A, "codex": f.CODEX_A},
        hub='"agents-hub"',
    )
    if trouble == "not joinable":
        host.hs.room(HUB, HUB_ROOM, joined={f.HUMAN}, invited=set())
    assert f.run(capsys, monkeypatch, "hook-wait", "--seconds", "1.5")[:3] == (
        0,
        "",
        "",
    )
    assert len(hub_lines(host)) == 1, "one line for a wait of several syncs"
    host.hs.post(f.ROOM, f.HUMAN, "project mail")
    code, _, err, _ = f.run(capsys, monkeypatch, "hook-wait", "--seconds", "5")
    assert code == 2 and "> project mail" in err
    assert len(hub_lines(host)) == 2, "each wait tries the hub again"
    assert "unavailable" in hub_lines(host)[0]


def test_hook_wait_refuses_the_project_whose_room_is_the_hub(
    hub: Host, owner: Owner, capsys, monkeypatch
) -> None:
    project = hub.project.parent / "hub"
    project.mkdir()
    monkeypatch.chdir(project)
    assert f.run(capsys, monkeypatch, "hook-wait", "--seconds", "1")[:3] == (0, "", "")
    assert "is the hub; not waiting" in (hub.state() / "log").read_text()
    assert not list(hub.state().glob("*.cursor"))


# status


def status_hub_line(capsys, monkeypatch) -> str:
    code, out, _, _ = f.run(capsys, monkeypatch, "status")
    assert code == 0
    [line] = [x for x in out.splitlines() if x.startswith("hub:")]
    return line


def test_status_shows_the_hub_covered_while_a_wait_runs(
    hub: Host, owner: Owner, capsys, monkeypatch
) -> None:
    f.run(capsys, monkeypatch, "hook-wait", "--seconds", "0.1")
    codes: list[int] = []
    t = threading.Thread(
        target=lambda: codes.append(cli.main(["hook-wait", "--seconds", "10"]))
    )
    t.start()
    flag = hub.state() / f"agents-{f.PROJECT}.hub"
    end = time.monotonic() + 5
    while not flag.exists():
        assert time.monotonic() < end
        time.sleep(0.02)
    assert status_hub_line(capsys, monkeypatch) == f"hub: {HUB}: covered"
    owner_file = hub.state() / f"agents-{f.PROJECT}.owner"
    assert owner_file.read_text() == f"{owner.pid}\n"
    say(hub.hs, f.HUMAN, f"{f.PROJECT}: hello")
    t.join(15)
    assert codes == [2]
    err = capsys.readouterr().err
    assert f"Hub: from the user ({f.HUMAN}, the user speaking) to {f.PROJECT}" in err
    assert not flag.exists()
    assert status_hub_line(capsys, monkeypatch) == (
        f"hub: {HUB}: not covered (no wait listens)"
    )


def test_status_shows_the_hub_unavailable_or_unknown(
    hub: Host, capsys, monkeypatch
) -> None:
    lock = WaitLock(config.state_dir(A), f"agents-{f.PROJECT}")
    assert lock.try_acquire()
    try:
        line = status_hub_line(capsys, monkeypatch)
        assert line == f"hub: {HUB}: unknown (the wait does not report the hub)"
        (hub.state() / f"agents-{f.PROJECT}.hub").write_text(
            "unavailable: no such alias\n"
        )
        line = status_hub_line(capsys, monkeypatch)
        assert line == f"hub: {HUB}: unavailable: no such alias"
    finally:
        lock.release()


def test_status_without_a_hub_has_no_hub_line(host: Host, capsys, monkeypatch) -> None:
    code, out, _, _ = f.run(capsys, monkeypatch, "status")
    assert code == 0 and "hub:" not in out


# The note


def cfg_with_hub(tmp_path: Path) -> config.Config:
    f.write_config(tmp_path, "http://127.0.0.1:1", {"claude": A}, hub='"agents-hub"')
    path = tmp_path / ".config" / "agent-chat" / "config.toml"
    return config.load_config(path)


def event(n: int, sender: str, content: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "m.room.message",
        "sender": sender,
        "event_id": f"$e{n}",
        "content": content,
    }


def hub_post(
    project: str, to: list[str], body: str, root: str | None = None
) -> dict[str, Any]:
    content = cli.hub_content(body, project, to, [], f.SERVER)
    if root is not None:
        content["m.relates_to"] = {"rel_type": "m.thread", "event_id": root}
    return content


def test_the_note_names_the_hub_provenance_and_reply_commands(tmp_path: Path) -> None:
    cfg = cfg_with_hub(tmp_path)
    alias = room_alias(cfg, "alpha")
    from_beta = Message(
        B, "beta → alpha: x", "$e1", None, HubMail("alpha", "beta", ("alpha",))
    )
    from_user = Message(
        f.HUMAN, "alpha: y", "$e2", None, HubMail("alpha", None, ("alpha",))
    )
    note = render([from_beta, from_user], cfg, A, alias)
    head = f"agent-chat: messages for {A} in {alias} and for project alpha in the hub"
    assert note.startswith(f"{head} {HUB}.")
    assert "never with a plain send" in note
    assert f"Hub: from beta ({B}, peer mail from another agent;" in note
    reply = f"`agent-chat send --hub --thread e1 --project beta --to {B}`"
    assert f"to alpha; reply with {reply}:" in note
    assert (
        f"Hub: from the user ({f.HUMAN}, the user speaking) to alpha; reply with "
        "`agent-chat send --hub --thread e2`:" in note
    )
    codex = render([from_beta], cfg, CA, alias, CODEX_REPLY)
    assert (
        "`agent-chat send --as codex --message-file <fresh-name> --hub --thread e1 "
        f"--project beta --to {B}`" in codex
    )


def test_the_notes_own_label_and_skipped_context_compare_pairs(tmp_path: Path) -> None:
    cfg = cfg_with_hub(tmp_path)
    root = event(0, A, hub_post("beta", ["alpha"], "plan?"))
    earlier = event(1, A, hub_post("beta", [], "beta thinks so", "$e0"))
    reply = event(
        2,
        f.HUMAN,
        {
            "msgtype": "m.text",
            "body": "go on",
            "m.relates_to": {"rel_type": "m.thread", "event_id": "$e0"},
        },
    )
    thread = observe("$e0", root, [reply, earlier], cfg)

    def note(project: str) -> str:
        m = Message(f.HUMAN, "go on", "$e2", thread, HubMail(project, None, ()))
        return render([m], cfg, A, room_alias(cfg, project))

    as_beta, as_alpha = note("beta"), note("alpha")
    assert f"Hub thread e0, started by {A} (this account);" in as_beta
    assert "Earlier in this thread" not in as_beta
    assert f"Hub thread e0, started by {A}, peer mail" in as_alpha
    assert "beta thinks so" in as_alpha and "Earlier in this thread" in as_alpha
    to = "to this thread, which includes alpha"
    assert f"{to}; reply with `agent-chat send --hub --thread e0`" in as_alpha
