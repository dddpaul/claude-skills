"""Claude's mailbox: atomic delivery, one collector at a time, one wait per pair.

Mail for an earlier incarnation of the Claude session, in another protocol
version or unreadable is quarantined and reported, never consumed or dropped.
``waiting`` trusts a heartbeat only while both the wait and its owning claude
live, so a killed wait reads as no wait at once. A send to Claude prints
``delivered`` while a wait runs and ``queued`` otherwise.
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
from zpc_fakes import PAIR, THREAD_A, FakeZmx, labels

from zpc.common import ZpcError
from zpc.mailbox import Mailbox, mail_root, prepare_message, take_message
from zpc.router import send
from zpc.zmx import Session


def _box(tmp_path: Path) -> Mailbox:
    return Mailbox(tmp_path, PAIR)


def _dead_pid() -> int:
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    return child.pid


def test_collect_takes_each_message_once_under_concurrency(tmp_path: Path) -> None:
    box = _box(tmp_path)
    sent = [f"m{i:03d}" for i in range(200)]
    for text in sent:
        box.deliver(text, "codex", "inc1")
    taken: list[str] = []
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            other = _box(tmp_path)
            while any(other.inbox.glob("*.msg")):
                taken.extend(other.collect("inc1").messages)
        except BaseException as exc:  # noqa: BLE001 - reported below
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert sorted(taken) == sent


def test_collect_waits_for_the_lock(tmp_path: Path) -> None:
    box = _box(tmp_path)
    box.deliver("hello", "codex", "inc1")
    done: list[list[str]] = []
    with open(box.dir / "collect.lock", "a") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        t = threading.Thread(target=lambda: done.append(box.collect("inc1").messages))
        t.start()
        time.sleep(0.3)
        assert done == []
    t.join(5)
    assert done == [["hello"]]


def test_second_wait_is_busy(tmp_path: Path) -> None:
    box = _box(tmp_path)
    with open(box.dir / "waiter.lock", "a") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        assert box.wait("inc1", os.getpid(), 5).outcome == "busy"


def test_wait_returns_mail_and_clears_its_heartbeat(tmp_path: Path) -> None:
    box = _box(tmp_path)
    seen: list[bool] = []

    def sleep(_: float) -> None:
        seen.append(box.waiting())
        box.deliver("Chat from Codex: hi", "codex", "inc1")

    got = box.wait("inc1", os.getpid(), 60, sleep=sleep)
    assert got.outcome == "mail" and got.collected is not None
    assert got.collected.messages == ["Chat from Codex: hi"]
    assert seen == [True]
    assert not box.waiting() and not (box.dir / "waiter").exists()


def test_wait_leaves_mail_when_its_owner_is_gone(tmp_path: Path) -> None:
    box = _box(tmp_path)
    box.deliver("hi", "codex", "inc1")
    assert box.wait("inc1", 1, 60, alive=lambda pid: False).outcome == "owner-gone"
    assert len(list(box.inbox.glob("*.msg"))) == 1


def test_wait_times_out(tmp_path: Path) -> None:
    box = _box(tmp_path)
    clock = [0.0]

    def sleep(dt: float) -> None:
        clock[0] += dt

    got = box.wait("inc1", os.getpid(), 3, sleep=sleep, now=lambda: clock[0])
    assert got.outcome == "timeout"


def test_earlier_incarnation_mail_is_quarantined_and_reported(tmp_path: Path) -> None:
    box = _box(tmp_path)
    old = box.deliver("for the old claude", "codex", "inc-old")
    box.deliver("for this claude", "codex", "inc-new")
    got = box.collect("inc-new")
    assert got.messages == ["for this claude"]
    assert len(got.quarantined) == 1 and "earlier incarnation" in got.quarantined[0]
    assert (box.quarantine / old.name).exists()
    assert "zmx-peer-chat: quarantined " + old.name in got.render()


@pytest.mark.parametrize(
    ("body", "why"),
    [
        ({"proto": "2", "pair": PAIR, "inc": "i", "text": "x"}, "protocol version '2'"),
        ({"proto": "1", "pair": "dother", "inc": "i", "text": "x"}, "mail for pair"),
        ({"proto": "1", "pair": PAIR, "inc": "i", "text": 3}, "unreadable"),
        ("not json", "unreadable"),
    ],
)
def test_bad_mail_is_quarantined(tmp_path: Path, body: object, why: str) -> None:
    box = _box(tmp_path)
    path = box.inbox / "1-1-0000.msg"
    path.write_text(body if isinstance(body, str) else json.dumps(body))
    got = box.collect("i")
    assert got.messages == [] and why in got.quarantined[0]
    assert (box.quarantine / path.name).exists()


def test_waiting_needs_a_fresh_heartbeat_of_a_live_wait(tmp_path: Path) -> None:
    box = _box(tmp_path)
    beat = box.dir / "waiter"
    assert not box.waiting()
    beat.write_text(f"{os.getpid()} {os.getpid()}\n")
    assert box.waiting()
    beat.write_text(f"{os.getpid()} {_dead_pid()}\n")  # the wait was killed
    assert not box.waiting()
    beat.write_text(f"{os.getpid()}\n")
    assert not box.waiting()
    beat.write_text(f"{os.getpid()} {os.getpid()}\n")
    os.utime(beat, (time.time() - 60, time.time() - 60))
    assert not box.waiting()


def _claude_and_codex() -> FakeZmx:
    return FakeZmx(
        [
            Session("w-claude", 1, labels("claude", "c1a0de00")),
            Session("w-codex", 2, labels("codex", "c0dec0de", thread=THREAD_A)),
        ]
    )


def test_send_to_claude_is_queued_without_a_wait(tmp_path: Path) -> None:
    out = send("claude", "hi", "w-codex", _claude_and_codex(), tmp_path)
    assert out == "queued"
    box = _box(tmp_path)
    (msg,) = box.inbox.glob("*.msg")
    body = json.loads(msg.read_text())
    assert body["text"] == "Chat from Codex: hi"
    assert body["inc"] == "c1a0de00" and body["proto"] == "1"
    assert msg.stat().st_mode & 0o777 == 0o600


def test_send_to_claude_is_delivered_while_a_wait_runs(tmp_path: Path) -> None:
    box = _box(tmp_path)
    box._beat(os.getpid())
    out = send("claude", "hi", "w-codex", _claude_and_codex(), tmp_path)
    assert out == "delivered"
    assert box.collect("c1a0de00").messages == ["Chat from Codex: hi"]


def test_prepared_message_is_private_and_taken_once(tmp_path: Path) -> None:
    path = prepare_message(tmp_path, "zpc-codex-a91f.txt")
    assert path.stat().st_mode & 0o777 == 0o600
    path.write_text("one paragraph")
    assert take_message(tmp_path, "zpc-codex-a91f.txt") == "one paragraph"
    assert not path.exists()
    with pytest.raises(ZpcError):
        take_message(tmp_path, "zpc-codex-a91f.txt")
    prepare_message(tmp_path, "again.txt")
    with pytest.raises(ZpcError, match="choose a fresh name"):
        prepare_message(tmp_path, "again.txt")
    for bad in ("../x", "a/b", "-x"):
        with pytest.raises(ZpcError):
            prepare_message(tmp_path, bad)


def test_a_symlinked_message_file_is_refused(tmp_path: Path) -> None:
    prepare_message(tmp_path, "real.txt")
    os.symlink(tmp_path / "outbox" / "real.txt", tmp_path / "outbox" / "link.txt")
    with pytest.raises(ZpcError, match="not a plain file"):
        take_message(tmp_path, "link.txt")


def test_mail_root_must_be_private(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "mail"
    monkeypatch.setenv("ZPC_MAIL_DIR", str(root))
    assert mail_root() == root and root.stat().st_mode & 0o777 == 0o700
    root.chmod(0o755)
    with pytest.raises(ZpcError, match="not a private directory"):
        mail_root()


def test_a_delivery_in_progress_is_not_mail(tmp_path: Path) -> None:
    box = _box(tmp_path)
    (box.inbox / ".1-2-abcd.msg.part").write_text('{"proto": "1", "pa')
    (box.inbox / ".hidden.msg").write_text("not mail")
    box.deliver("hello", "codex", "inc1")
    got = box.collect("inc1")
    assert got.messages == ["hello"] and got.quarantined == []
    assert sorted(p.name for p in box.inbox.iterdir()) == [
        ".1-2-abcd.msg.part",
        ".hidden.msg",
    ]


def test_deliveries_and_collects_race_without_loss(tmp_path: Path) -> None:
    _box(tmp_path)  # create the mailbox before the threads start
    sent = [f"m{i:03d}" for i in range(300)]
    taken: list[str] = []
    quarantined: list[str] = []
    errors: list[BaseException] = []
    done = threading.Event()

    def writer(part: list[str]) -> None:
        try:
            for text in part:
                _box(tmp_path).deliver(text, "codex", "inc1")
        except BaseException as exc:  # noqa: BLE001 - reported below
            errors.append(exc)

    def reader() -> None:
        other = _box(tmp_path)
        while not done.is_set() or any(other.inbox.glob("*.msg")):
            got = other.collect("inc1")
            taken.extend(got.messages)
            quarantined.extend(got.quarantined)

    writers = [threading.Thread(target=writer, args=(sent[i::3],)) for i in range(3)]
    readers = [threading.Thread(target=reader) for _ in range(2)]
    for t in readers + writers:
        t.start()
    for t in writers:
        t.join()
    done.set()
    for t in readers:
        t.join()
    assert errors == [] and quarantined == []
    assert sorted(taken) == sent
