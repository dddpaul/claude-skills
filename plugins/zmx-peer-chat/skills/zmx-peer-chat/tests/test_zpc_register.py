"""The register helper: labels read before any attach, and the Codex thread pick.

The launcher calls ``register`` just before ``zmx attach`` creates a session.
An existing session keeps its labels (``zmx attach --labels`` would overwrite
them, so nothing here attaches). For Codex the helper snapshots the daemon's
loaded threads and binds the one thread the new TUI shows in the session
directory. The session's command picks it exactly where it can: ``codex`` binds
the thread of the first ``thread/started`` notification in the directory,
``codex resume --last`` the thread the TUI's own ``thread/list`` query returns,
``codex resume <id>`` that id. Once an exact candidate fails a footer check the
time-based candidates join it, and ``--last`` is asked once more. Without such a
signal the fallback infers it at once:
candidates are tried in order: a newly loaded id created after the
snapshot, any other newly loaded id whatever its times (codex-cli 0.166.0
leaves the times of a resumed, unloaded thread alone), a thread whose
``updatedAt`` moved past the snapshot (``codex resume --last``), and, after
``FALLBACK_SECONDS``, the other idle threads loaded at the snapshot. A candidate
is bound only once the session's footer shows the name it was given; without
one the bind sets no label.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest
from zpc_fakes import (
    THREAD_A,
    THREAD_B,
    THREAD_C,
    THREAD_E,
    Clock,
    FakeDaemon,
    FakeZmx,
    LateDaemon,
    thread,
    tui_footer,
)

from zpc.common import ZpcError, pair_id
from zpc.daemon import DaemonError, ThreadInfo
from zpc.register import (
    BIND_SECONDS,
    FALLBACK_SECONDS,
    Registration,
    _candidates,
    _command,
    bind,
    bind_in_background,
    prepare,
)
from zpc.zmx import Session, Zmx


BIN = Path(__file__).resolve().parents[3] / "bin" / "zmx-peer-chat"

# The wall clock at the snapshot; the fake threads' times are on the same scale.
SINCE = 1000


def NOW() -> float:  # noqa: N802 - a constant clock
    return SINCE + 0.4


def _no_daemon() -> FakeDaemon:
    raise AssertionError("the daemon must not be asked")


def _prepare(
    tmp_path: Path, daemon: FakeDaemon, zmx: FakeZmx, cmd: str | None = None
) -> Registration:
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    reg = prepare(
        "codex", "w-codex", str(work), None, zmx, tmp_path, lambda: daemon, NOW
    )
    assert reg is not None
    zmx.live["w-codex"] = Session("w-codex", 42, cmd=cmd)
    return reg


def _register(
    tmp_path: Path,
    daemon: FakeDaemon,
    zmx: FakeZmx,
    clock: Clock,
    shown: str | None = None,
    timeout: float | None = 10,
    cmd: str | None = None,
) -> tuple[Registration, dict[str, str]]:
    """Register a Codex session whose TUI shows thread ``shown`` (None: none)."""
    if shown is not None:
        zmx.footers["w-codex"] = tui_footer(daemon, shown)
    reg = _prepare(tmp_path, daemon, zmx, cmd)
    try:
        if timeout is None:
            got = bind(reg, zmx, lambda: daemon, sleep=clock.sleep, now=clock.now)
        else:
            got = bind(reg, zmx, lambda: daemon, timeout, clock.sleep, clock.now)
        return reg, got
    finally:
        assert reg.lock is not None
        reg.lock.close()


def _fake_zmx_exe(tmp_path: Path, ls_lines: list[str]) -> tuple[Path, Path]:
    log, listing = tmp_path / "zmx.log", tmp_path / "ls.txt"
    listing.write_text("".join(f"{line}\n" for line in ls_lines))
    exe = tmp_path / "zmx"
    exe.write_text(
        "#!/bin/sh\n"
        f'echo "$@" >> "{log}"\n'
        f'case $1 in ls) cat "{listing}" ;; set) exit 0 ;; *) exit 9 ;; esac\n'
    )
    exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
    return exe, log


def test_existing_session_keeps_its_labels(tmp_path: Path) -> None:
    exe, log = _fake_zmx_exe(
        tmp_path, ["  name=w-codex\tpid=7\tclients=1\tzpc.pair=old\tcmd=codex"]
    )
    reg = prepare(
        "codex", "w-codex", str(tmp_path), None, Zmx(str(exe)), tmp_path, _no_daemon
    )
    assert reg is None
    assert log.read_text().split("\n")[:-1] == ["ls"]


def test_new_session_is_listed_then_labelled_with_zmx_set_only(tmp_path: Path) -> None:
    exe, log = _fake_zmx_exe(tmp_path, [])
    zmx = Zmx(str(exe))
    reg = prepare("claude", "w-claude", str(tmp_path), None, zmx, tmp_path, _no_daemon)
    assert reg is not None
    _fake_zmx_exe(tmp_path, ["  name=w-claude\tpid=8\tclients=1\tcmd=claude"])
    clock = Clock()
    try:
        got = bind(reg, zmx, _no_daemon, 10, clock.sleep, clock.now)
    finally:
        assert reg.lock is not None
        reg.lock.close()
    calls = log.read_text().split("\n")[:-1]
    assert [c.split()[0] for c in calls] == ["ls", "ls", "set"]
    assert not any("attach" in c for c in calls)
    assert calls[-1] == "set w-claude " + " ".join(
        f"{k}={v}" for k, v in sorted(got.items())
    )
    assert got["zpc.pair"] == pair_id(str(tmp_path))
    assert got["zpc.role"] == "claude"
    assert "zpc.thread" not in got


def test_fresh_start_binds_the_one_new_thread_in_the_directory(tmp_path: Path) -> None:
    work, other = str((tmp_path / "work").resolve()), "/elsewhere"
    (tmp_path / "work").mkdir()
    before = {THREAD_A: thread(THREAD_A, other, 1), THREAD_B: thread(THREAD_B, work, 5)}
    after = dict(before)
    after[THREAD_C] = thread(THREAD_C, work, SINCE + 1, created=SINCE + 1)
    after[THREAD_E] = thread(THREAD_E, other, SINCE + 1, created=SINCE + 1)
    daemon = FakeDaemon([before, before, after])
    zmx = FakeZmx()
    reg, got = _register(tmp_path, daemon, zmx, Clock(), THREAD_C)
    assert got["zpc.thread"] == THREAD_C
    assert daemon.names == {THREAD_C: f"zpc-{reg.inc}"}
    assert zmx.set_calls == [("w-codex", got)]


def test_a_fresh_start_binds_the_thread_of_its_thread_started_notification(
    tmp_path: Path,
) -> None:
    # Leftover A, loaded at the snapshot, reads as now on every poll, which
    # the fallback would take for a resume. The session runs `codex`, so only
    # the thread/started notification counts: first one in another directory,
    # then the new TUI's thread C in the session directory.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    left = {THREAD_A: thread(THREAD_A, work, 5, created=5)}
    opened = dict(left)
    opened[THREAD_E] = thread(THREAD_E, "/elsewhere", SINCE + 1, created=SINCE + 1)
    opened[THREAD_C] = thread(THREAD_C, work, SINCE + 3, created=SINCE + 3)
    clock = Clock()
    started = {4: [(THREAD_E, "/elsewhere")], 9: [(THREAD_C, work)]}
    daemon = FakeDaemon(
        [left] * 9 + [opened], {THREAD_A}, lambda: SINCE + clock.t, started
    )
    reg, got = _register(tmp_path, daemon, FakeZmx(), clock, THREAD_C, cmd="codex")
    assert got["zpc.thread"] == THREAD_C
    assert daemon.names == {THREAD_C: f"zpc-{reg.inc}"}
    # The connection opened at prepare is the one that heard the notification.
    assert reg.watch is daemon and daemon.closed


def test_resume_last_binds_the_thread_the_tuis_query_returns(tmp_path: Path) -> None:
    # B was loaded at the snapshot and its times never move; A, updated more
    # recently, and C, loaded again during the bind, are what the fallback
    # would try first. The thread/list query says B, so only B is named.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    snap = {THREAD_A: thread(THREAD_A, work, 9), THREAD_B: thread(THREAD_B, work, 7)}
    later = dict(snap)
    later[THREAD_C] = thread(THREAD_C, work, SINCE + 1, created=SINCE + 1)
    daemon, clock = FakeDaemon([snap, later], last=THREAD_B), Clock()
    reg, got = _register(
        tmp_path, daemon, FakeZmx(), clock, THREAD_B, cmd="codex resume --last"
    )
    assert got["zpc.thread"] == THREAD_B
    assert daemon.names == {THREAD_B: f"zpc-{reg.inc}"}
    assert daemon.queries == [work]
    assert clock.t < FALLBACK_SECONDS


def test_resume_of_an_id_binds_that_id_once_loaded(tmp_path: Path) -> None:
    # C starts loading first with fresh times, which the fallback would try
    # before anything else; the session resumes B, loaded a few polls later.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    early = {THREAD_C: thread(THREAD_C, work, SINCE + 1, created=SINCE + 1)}
    late = dict(early)
    late[THREAD_B] = thread(THREAD_B, work, 7, created=3)
    daemon = FakeDaemon([{}, early, early, early, late])
    cmd = f"codex resume {THREAD_B}"
    reg, got = _register(tmp_path, daemon, FakeZmx(), Clock(), THREAD_B, cmd=cmd)
    assert got["zpc.thread"] == THREAD_B
    assert daemon.names == {THREAD_B: f"zpc-{reg.inc}"}
    assert daemon.queries == []


def _work(tmp_path: Path) -> str:
    (tmp_path / "work").mkdir()
    return str((tmp_path / "work").resolve())


def test_a_wrong_last_answer_gives_way_to_the_thread_the_tui_shows(
    tmp_path: Path,
) -> None:
    # The --last query names A, which another TUI shows, so the footer never
    # shows it; the new TUI shows C. After A's failed check the time-based
    # candidates join, C is bound and A gets its own name back.
    work = _work(tmp_path)
    snap = {THREAD_A: ThreadInfo(THREAD_A, work, "idle", "mine", 3, 9)}
    later = dict(snap)
    later[THREAD_C] = thread(THREAD_C, work, SINCE + 1, created=SINCE + 1)
    daemon, clock = FakeDaemon([snap, later], last=THREAD_A), Clock()
    reg, got = _register(
        tmp_path, daemon, FakeZmx(), clock, THREAD_C, None, "codex resume --last"
    )
    assert got["zpc.thread"] == THREAD_C
    assert daemon.names == {THREAD_A: "mine", THREAD_C: f"zpc-{reg.inc}"}
    assert reg.left_exact
    assert clock.t < FALLBACK_SECONDS < BIND_SECONDS


def test_a_stale_last_answer_is_asked_again_after_a_failed_check(
    tmp_path: Path,
) -> None:
    # Both threads were loaded at the snapshot and no time moves, so the
    # time-based pick could not tell C before FALLBACK_SECONDS; the second
    # query, run after A's failed check, names C.
    work = _work(tmp_path)
    snap = {THREAD_A: thread(THREAD_A, work, 9), THREAD_C: thread(THREAD_C, work, 7)}
    daemon, clock = FakeDaemon([snap], last=[THREAD_A, THREAD_C]), Clock()
    reg, got = _register(
        tmp_path, daemon, FakeZmx(), clock, THREAD_C, None, "codex resume --last"
    )
    assert got["zpc.thread"] == THREAD_C
    assert daemon.queries == [work, work]
    assert daemon.names == {
        THREAD_A: f"zpc-{reg.inc}-unbound",
        THREAD_C: f"zpc-{reg.inc}",
    }
    assert not reg.left_exact
    assert clock.t < FALLBACK_SECONDS


def test_a_right_exact_pick_behind_a_dialog_is_still_bound(tmp_path: Path) -> None:
    # A dialog hides the footer for 8 s, past CONFIRM_SECONDS: resumed A fails
    # its first check, newly loaded C joins and is tried, then A again, now
    # shown.
    work = _work(tmp_path)
    table = {
        THREAD_A: thread(THREAD_A, work, 7, created=3),
        THREAD_C: thread(THREAD_C, work, SINCE + 1, created=SINCE + 1),
    }
    clock = Clock()
    daemon, zmx = FakeDaemon([{}, table]), FakeZmx()
    footer = tui_footer(daemon, THREAD_A)
    zmx.footers["w-codex"] = lambda: "" if clock.t < 8 else footer()
    cmd = f"codex resume {THREAD_A}"
    reg, got = _register(tmp_path, daemon, zmx, clock, None, None, cmd)
    assert got["zpc.thread"] == THREAD_A
    assert daemon.names == {
        THREAD_C: f"zpc-{reg.inc}-unbound",
        THREAD_A: f"zpc-{reg.inc}",
    }
    assert not reg.left_exact


def _foreign_start(tmp_path: Path) -> FakeDaemon:
    """A ``codex`` start whose only thread/started is another TUI's thread E."""
    work = _work(tmp_path)
    opened = {
        THREAD_E: thread(THREAD_E, work, SINCE + 1, created=SINCE + 1),
        THREAD_C: thread(THREAD_C, work, SINCE + 1, created=SINCE + 1),
    }
    return FakeDaemon([{}, opened], started={1: [(THREAD_E, work)]})


def test_another_tuis_thread_started_gives_way_to_the_shown_thread(
    tmp_path: Path,
) -> None:
    daemon, clock = _foreign_start(tmp_path), Clock()
    reg, got = _register(tmp_path, daemon, FakeZmx(), clock, THREAD_C, cmd="codex")
    assert got["zpc.thread"] == THREAD_C
    assert daemon.names == {
        THREAD_E: f"zpc-{reg.inc}-unbound",
        THREAD_C: f"zpc-{reg.inc}",
    }
    assert reg.left_exact


def test_the_log_says_when_the_bind_left_the_exact_pick(tmp_path: Path) -> None:
    daemon, zmx, clock = _foreign_start(tmp_path), FakeZmx(), Clock()
    zmx.footers["w-codex"] = tui_footer(daemon, THREAD_C)
    reg = _prepare(tmp_path, daemon, zmx, "codex")
    log = tmp_path / "register.log"
    assert reg.lock is not None
    reg.lock.close()
    bind_in_background(
        reg, log, lambda: bind(reg, zmx, lambda: daemon, 10, clock.sleep, clock.now)
    )
    for _ in range(100):
        if log.exists() and log.read_text().endswith("\n"):
            break
        time.sleep(0.05)
    line = log.read_text()
    assert "w-codex: labelled " in line and f"zpc.thread={THREAD_C}" in line
    assert line.endswith(" (after the exact pick)\n")


@pytest.mark.parametrize("cmd", ["codex", "codex resume --last", "resume-id"])
def test_an_exact_pick_shown_at_once_names_no_time_based_candidate(
    tmp_path: Path, cmd: str
) -> None:
    # B is the exact pick; started C and resumed A come first in the
    # time-based order but are never named.
    work = _work(tmp_path)
    snap = {THREAD_A: thread(THREAD_A, work, 9)}
    later = {
        THREAD_A: thread(THREAD_A, work, SINCE + 1),
        THREAD_B: thread(THREAD_B, work, SINCE + 1, created=SINCE + 1),
        THREAD_C: thread(THREAD_C, work, SINCE + 1, created=SINCE + 1),
    }
    started = {1: [(THREAD_B, work)]}
    daemon = FakeDaemon([snap, later], started=started, last=THREAD_B)
    cmd = f"codex resume {THREAD_B}" if cmd == "resume-id" else cmd
    reg, got = _register(tmp_path, daemon, FakeZmx(), Clock(), THREAD_B, cmd=cmd)
    assert got["zpc.thread"] == THREAD_B
    assert daemon.names == {THREAD_B: f"zpc-{reg.inc}"}
    assert not reg.left_exact


@pytest.mark.parametrize("cmd", [None, "bash", "codex --yolo", "codex resume --last"])
def test_without_an_exact_signal_the_bind_falls_back(tmp_path: Path, cmd: str) -> None:
    # No cmd, another command, or a --last query that returns nothing: the
    # TASK-63 pick binds the thread loaded again with unmoved times.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    resumed = thread(THREAD_B, work, SINCE - 50, created=SINCE - 100)
    daemon = FakeDaemon([{}, {}, {THREAD_B: resumed}], last=None)
    reg, got = _register(tmp_path, daemon, FakeZmx(), Clock(), THREAD_B, cmd=cmd)
    assert got["zpc.thread"] == THREAD_B
    assert daemon.names == {THREAD_B: f"zpc-{reg.inc}"}


def test_a_fresh_start_after_a_late_daemon_falls_back(tmp_path: Path) -> None:
    # No daemon at registration: the TUI started it, so its thread/started
    # went out before register could listen. The bind's own connection never
    # hears it; the TASK-63 pick binds the new thread.
    work = str((tmp_path / "work").resolve())
    opened = {THREAD_C: thread(THREAD_C, work, SINCE + 2, created=SINCE + 2)}
    daemon = FakeDaemon([{}, opened])
    opener, zmx = LateDaemon(daemon, 3), FakeZmx()
    zmx.footers["w-codex"] = tui_footer(daemon, THREAD_C)
    reg = _prepare_late(tmp_path, opener, zmx)
    zmx.live["w-codex"].cmd = "codex"
    assert reg.watch is None
    clock = Clock()
    got = bind(reg, zmx, opener, 10, clock.sleep, clock.now)
    assert got["zpc.thread"] == THREAD_C
    assert daemon.names == {THREAD_C: f"zpc-{reg.inc}"}


@pytest.mark.parametrize(
    ("cmd", "how"),
    [
        ("codex", ("start", None)),
        ("/usr/local/bin/codex", ("start", None)),
        ("codex resume --last", ("last", None)),
        (f"codex resume {THREAD_B}", ("id", THREAD_B)),
        ("codex resume", None),
        ("codex resume not-an-id", None),
        ("codex exec hi", None),
        ("claude", None),
        ("codex 'unclosed", None),
        ("", None),
        (None, None),
    ],
)
def test_the_session_command_says_how_codex_starts(
    cmd: str | None, how: tuple[str, str | None] | None
) -> None:
    assert _command(cmd) == how


def test_resume_binds_the_still_loaded_thread_whose_update_moved(
    tmp_path: Path,
) -> None:
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    before = {THREAD_A: thread(THREAD_A, work, 5), THREAD_B: thread(THREAD_B, work, 7)}
    after = {
        THREAD_A: thread(THREAD_A, work, 5),
        THREAD_B: thread(THREAD_B, work, SINCE + 2),
    }
    daemon = FakeDaemon([before, after])
    reg, got = _register(tmp_path, daemon, FakeZmx(), Clock(), THREAD_B)
    assert got["zpc.thread"] == THREAD_B
    assert daemon.names == {THREAD_B: f"zpc-{reg.inc}"}


def test_resume_of_an_unloaded_thread_binds_it(tmp_path: Path) -> None:
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    after = {THREAD_B: thread(THREAD_B, work, SINCE + 2, created=3)}
    daemon = FakeDaemon([{}, {}, after])
    _, got = _register(tmp_path, daemon, FakeZmx(), Clock(), THREAD_B)
    assert got["zpc.thread"] == THREAD_B


def test_a_resumed_unloaded_thread_whose_times_did_not_move_is_bound(
    tmp_path: Path,
) -> None:
    # Seen on the box with codex-cli 0.166.0: the daemon had unloaded the
    # thread; the resume loaded it again, but createdAt and updatedAt both
    # stayed before the snapshot. Being loaded again is what marks it.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    resumed = thread(THREAD_B, work, SINCE - 50, created=SINCE - 100)
    daemon = FakeDaemon([{}, {}, {THREAD_B: resumed}])
    reg, got = _register(tmp_path, daemon, FakeZmx(), Clock(), THREAD_B)
    assert got["zpc.thread"] == THREAD_B
    assert daemon.names == {THREAD_B: f"zpc-{reg.inc}"}


def test_an_older_thread_loaded_again_is_tried_and_gets_its_name_back(
    tmp_path: Path,
) -> None:
    # Seen on the box: while `codex resume --last` resumed one thread, the
    # starting TUI loaded another, older thread of the same directory again.
    # Both read as old; the footer shows only the resumed one.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    reloaded = ThreadInfo(THREAD_C, work, "idle", "earlier-name", 600, 700)
    resumed = thread(THREAD_B, work, 800, created=600)
    daemon = FakeDaemon([{}, {THREAD_C: reloaded, THREAD_B: resumed}])
    reg, got = _register(tmp_path, daemon, FakeZmx(), Clock(), THREAD_B)
    assert got["zpc.thread"] == THREAD_B
    assert daemon.names == {THREAD_C: "earlier-name", THREAD_B: f"zpc-{reg.inc}"}


def test_a_still_loaded_thread_whose_times_did_not_move_is_a_fallback(
    tmp_path: Path,
) -> None:
    # A resume of a thread the daemon still has loaded, if it moves no time:
    # nothing is started, newly loaded or resumed, so after FALLBACK_SECONDS
    # the idle threads of the snapshot are tried, the most recent first.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    table = {THREAD_A: thread(THREAD_A, work, 5), THREAD_B: thread(THREAD_B, work, 7)}
    daemon, clock = FakeDaemon([table]), Clock()
    reg, got = _register(tmp_path, daemon, FakeZmx(), clock, THREAD_B, timeout=None)
    assert got["zpc.thread"] == THREAD_B
    assert daemon.names == {THREAD_B: f"zpc-{reg.inc}"}
    assert clock.t >= FALLBACK_SECONDS


def test_newly_loaded_threads_are_tried_before_any_fallback(tmp_path: Path) -> None:
    # Thread C is loaded again during the bind but not shown; thread A, loaded
    # at the snapshot with unmoved times, is the one the footer shows. C is
    # named first and taken back; A is tried only as a fallback.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    snap = {THREAD_A: thread(THREAD_A, work, 5)}
    later = dict(snap)
    later[THREAD_C] = thread(THREAD_C, work, 6, created=6)
    daemon, clock = FakeDaemon([snap, later]), Clock()
    reg, got = _register(tmp_path, daemon, FakeZmx(), clock, THREAD_A, timeout=None)
    assert got["zpc.thread"] == THREAD_A
    assert list(daemon.names) == [THREAD_C, THREAD_A]
    assert daemon.names[THREAD_C] == f"zpc-{reg.inc}-unbound"
    assert clock.t >= FALLBACK_SECONDS


def test_the_candidate_order_once_the_fallback_has_joined() -> None:
    # Started, newly loaded, resumed, then the idle snapshot threads, the most
    # recently updated first (the one `codex resume --last` picks).
    work, thread_f = "/work", "01a15a38-0000-7000-8000-00000000000f"
    reg = Registration("codex", "w-codex", work, "dpair", "inc0", since=SINCE)
    reg.before = {THREAD_A: 5, THREAD_B: 7, THREAD_E: 3}
    table = {
        THREAD_A: thread(THREAD_A, work, 5),
        THREAD_B: thread(THREAD_B, work, 7),
        THREAD_E: thread(THREAD_E, work, SINCE + 1),
        thread_f: thread(thread_f, work, 9, created=9),
        THREAD_C: thread(THREAD_C, work, SINCE + 1, created=SINCE + 1),
    }
    daemon = FakeDaemon([table])
    order = [THREAD_C, thread_f, THREAD_E, THREAD_B, THREAD_A]
    assert _candidates(daemon, reg, True) == order
    assert _candidates(daemon, reg, False) == order[:3]


@pytest.mark.parametrize("status", ["notLoaded", "systemError"])
def test_only_an_idle_snapshot_thread_is_a_fallback(status: str) -> None:
    reg = Registration("codex", "w-codex", "/work", "dpair", "inc0", since=SINCE)
    reg.before = {THREAD_A: 5}
    daemon = FakeDaemon([{THREAD_A: thread(THREAD_A, "/work", 5, status=status)}])
    assert _candidates(daemon, reg, True) == []


def test_a_thread_seen_running_a_turn_is_never_a_fallback(tmp_path: Path) -> None:
    # Thread A ran a turn during the bind and then sat idle with its old
    # times; even though the footer would show it, it is never named.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    idle = {THREAD_A: thread(THREAD_A, work, 5)}
    turn = {THREAD_A: thread(THREAD_A, work, 5, status="active")}
    daemon, zmx = FakeDaemon([idle, turn, idle]), FakeZmx()
    with pytest.raises(ZpcError, match="no Codex thread opened") as err:
        _register(tmp_path, daemon, zmx, Clock(), THREAD_A, timeout=None)
    assert err.value.code == 5
    assert daemon.names == {} and zmx.set_calls == []


def test_a_running_turn_is_no_resume(tmp_path: Path) -> None:
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    before = {THREAD_A: thread(THREAD_A, work, 5)}
    after = {THREAD_A: thread(THREAD_A, work, SINCE + 1, status="active")}
    daemon, zmx = FakeDaemon([before, after]), FakeZmx()
    with pytest.raises(ZpcError) as err:
        _register(tmp_path, daemon, zmx, Clock())
    assert err.value.code == 5
    assert zmx.set_calls == [] and daemon.names == {}


def test_a_thread_that_ran_a_turn_is_no_resume(tmp_path: Path) -> None:
    # Another TUI's thread in the same directory: running a turn at the
    # snapshot, or seen running one while the bind polls, then idle with a
    # fresh updatedAt. Only the new TUI's thread, which comes later, is bound.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    snap = {
        THREAD_A: thread(THREAD_A, work, 5, status="active"),
        THREAD_B: thread(THREAD_B, work, 7),
    }
    turn = {
        THREAD_A: thread(THREAD_A, work, 5, status="active"),
        THREAD_B: thread(THREAD_B, work, 7, status="active"),
    }
    ended = {
        THREAD_A: thread(THREAD_A, work, SINCE + 1),
        THREAD_B: thread(THREAD_B, work, SINCE + 1),
    }
    opened = dict(ended)
    opened[THREAD_C] = thread(THREAD_C, work, SINCE + 2, created=SINCE + 2)
    daemon = FakeDaemon([snap, turn, ended, ended, opened])
    reg, got = _register(tmp_path, daemon, FakeZmx(), Clock(), THREAD_C)
    assert got["zpc.thread"] == THREAD_C
    assert daemon.names == {THREAD_C: f"zpc-{reg.inc}"}


def test_detached_register_lets_go_of_the_callers_output(tmp_path: Path) -> None:
    # A launcher may capture the helper's output; it must get end-of-file when
    # the helper returns, not when the background bind ends.
    exe, _ = _fake_zmx_exe(tmp_path, [])
    mail = tmp_path / "mail"
    env = dict(os.environ, ZPC_ZMX=str(exe), ZPC_MAIL_DIR=str(mail))
    env.pop("CODEX_THREAD_ID", None)
    argv = [sys.executable, str(BIN), "register", "--role", "claude"]
    argv += ["--session", "w-late", "--dir", str(tmp_path), "--timeout", "3"]
    start = time.monotonic()
    done = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=10)
    assert time.monotonic() - start < 2
    assert done.returncode == 0 and "in the background" in done.stdout
    log = mail / "register.log"
    for _ in range(100):
        if log.exists() and "did not appear" in log.read_text():
            break
        time.sleep(0.1)
    assert "w-late: session w-late did not appear; no label set" in log.read_text()


def test_zero_candidates_set_no_label(tmp_path: Path) -> None:
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    table = {THREAD_A: thread(THREAD_A, work, 5), THREAD_B: thread(THREAD_B, "/x", 1)}
    after = dict(table)
    after[THREAD_C] = thread(THREAD_C, "/x", SINCE + 1, created=SINCE + 1)  # elsewhere
    daemon, zmx, clock = FakeDaemon([table, after]), FakeZmx(), Clock()
    with pytest.raises(ZpcError, match="no label set") as err:
        _register(tmp_path, daemon, zmx, clock)
    assert err.value.code == 5
    assert clock.t >= 10
    assert zmx.set_calls == [] and daemon.names == {}


def test_of_several_candidates_the_one_the_footer_shows_is_bound(
    tmp_path: Path,
) -> None:
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    before = {THREAD_A: thread(THREAD_A, work, 5)}
    after = {
        THREAD_A: thread(THREAD_A, work, SINCE + 1),
        THREAD_C: thread(THREAD_C, work, SINCE + 1, created=SINCE + 1),
    }
    daemon, zmx = FakeDaemon([before, after]), FakeZmx()
    reg, got = _register(tmp_path, daemon, zmx, Clock(), THREAD_A)
    assert got["zpc.thread"] == THREAD_A
    # The started thread comes first; the footer never shows it, so it is
    # renamed away and only the bound thread carries the name.
    assert daemon.names == {
        THREAD_C: f"zpc-{reg.inc}-unbound",
        THREAD_A: f"zpc-{reg.inc}",
    }
    assert zmx.set_calls == [("w-codex", got)]


def test_a_leftover_thread_that_reads_as_now_is_not_bound(tmp_path: Path) -> None:
    # Seen on the box: a TUI killed before its first turn left thread A loaded,
    # unpersisted, so thread/read gives its times as the moment of the read
    # and it looks resumed on every poll. The new TUI shows thread C, which
    # loads 2 s later; C is bound, not A.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    left = {THREAD_A: thread(THREAD_A, work, 5, created=5)}
    opened = dict(left)
    opened[THREAD_C] = thread(THREAD_C, work, SINCE + 2, created=SINCE + 2)
    clock = Clock()
    daemon = FakeDaemon([left] * 8 + [opened], {THREAD_A}, lambda: SINCE + clock.t)
    zmx = FakeZmx()
    reg, got = _register(tmp_path, daemon, zmx, clock, THREAD_C)
    assert got["zpc.thread"] == THREAD_C
    assert daemon.names == {
        THREAD_A: f"zpc-{reg.inc}-unbound",  # tried, never shown
        THREAD_C: f"zpc-{reg.inc}",
    }
    assert zmx.set_calls == [("w-codex", got)]


def test_a_candidate_the_footer_never_shows_sets_no_label(tmp_path: Path) -> None:
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    after = {THREAD_C: thread(THREAD_C, work, SINCE + 1, created=SINCE + 1)}
    daemon, zmx = FakeDaemon([{}, after]), FakeZmx(screens={"w-codex": "x · y"})
    reg = _prepare(tmp_path, daemon, zmx)
    assert reg.lock is not None
    reg.lock.close()
    clock = Clock()
    with pytest.raises(ZpcError) as err:
        bind(reg, zmx, lambda: daemon, 10, clock.sleep, clock.now)
    assert err.value.code == 5
    assert str(err.value) == (
        f"the Codex TUI in w-codex never showed zpc-{reg.inc} in its "
        f"footer; named but not bound: {THREAD_C}; no label set"
    )
    assert daemon.names == {THREAD_C: f"zpc-{reg.inc}-unbound"}
    assert zmx.set_calls == []


def test_a_hidden_footer_never_confirms_another_candidate(tmp_path: Path) -> None:
    # A dialog hides the footer past the confirm window while the new TUI's
    # thread C is tried. Leftover A is tried next; the footer, now visible,
    # shows C's name, which was taken back, so A is not bound. C gets its
    # turn again and is bound.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    left = {THREAD_A: thread(THREAD_A, work, 5, created=5)}
    opened = dict(left)
    opened[THREAD_C] = thread(THREAD_C, work, SINCE + 1, created=SINCE + 1)
    clock = Clock()
    daemon = FakeDaemon([left, opened], {THREAD_A}, lambda: SINCE + clock.t)
    zmx, footer = FakeZmx(), tui_footer(daemon, THREAD_C)
    zmx.footers["w-codex"] = lambda: "" if clock.t < 6 else footer()
    reg, got = _register(tmp_path, daemon, zmx, clock, timeout=None)
    assert got["zpc.thread"] == THREAD_C
    assert daemon.names == {
        THREAD_A: f"zpc-{reg.inc}-unbound",
        THREAD_C: f"zpc-{reg.inc}",
    }


def test_the_log_says_why_the_footer_check_set_no_label(tmp_path: Path) -> None:
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    after = {THREAD_C: thread(THREAD_C, work, SINCE + 1, created=SINCE + 1)}
    daemon, zmx, clock = FakeDaemon([{}, after]), FakeZmx(), Clock()
    reg = _prepare(tmp_path, daemon, zmx)
    log = tmp_path / "register.log"
    assert reg.lock is not None
    reg.lock.close()
    bind_in_background(
        reg, log, lambda: bind(reg, zmx, lambda: daemon, 10, clock.sleep, clock.now)
    )
    for _ in range(100):
        if log.exists():
            break
        time.sleep(0.05)
    line = log.read_text()
    assert f"w-codex: the Codex TUI in w-codex never showed zpc-{reg.inc}" in line
    assert f"named but not bound: {THREAD_C}; no label set" in line
    assert zmx.set_calls == []


def _late_thread(tmp_path: Path, delay: float) -> FakeDaemon:
    """A daemon whose new thread loads ``delay`` seconds into the bind."""
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    opened = {THREAD_C: thread(THREAD_C, work, SINCE + 16, created=SINCE + 16)}
    polls = round(delay / 0.3)  # one loaded_threads call per 0.3 s poll
    return FakeDaemon([{}] * (1 + polls) + [opened])


def test_a_thread_opened_behind_a_startup_dialog_is_bound_by_default(
    tmp_path: Path,
) -> None:
    # Seen on the box: Codex's update notice and "Trust this folder?" held
    # the new TUI's thread back past the old 10 s window.
    assert BIND_SECONDS == 60
    daemon, zmx, clock = _late_thread(tmp_path, 15), FakeZmx(), Clock()
    _, got = _register(tmp_path, daemon, zmx, clock, THREAD_C, timeout=None)
    assert got["zpc.thread"] == THREAD_C
    assert clock.t >= 15


def test_a_shorter_timeout_still_gives_up(tmp_path: Path) -> None:
    daemon, zmx, clock = _late_thread(tmp_path, 15), FakeZmx(), Clock()
    with pytest.raises(ZpcError, match="no Codex thread opened") as err:
        _register(tmp_path, daemon, zmx, clock, THREAD_C, timeout=10)
    assert err.value.code == 5
    assert zmx.set_calls == [] and daemon.names == {}


def _prepare_late(tmp_path: Path, opener: LateDaemon, zmx: FakeZmx) -> Registration:
    """Prepare a Codex session through ``opener``; let go of its lock."""
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    reg = prepare("codex", "w-codex", str(work), None, zmx, tmp_path, opener, NOW)
    assert reg is not None and reg.lock is not None
    reg.lock.close()
    zmx.live["w-codex"] = Session("w-codex", 42)
    return reg


def _bind_logged(reg: Registration, zmx: FakeZmx, opener: LateDaemon, log: Path) -> str:
    """Run the background bind on a fake clock; return its register.log line."""
    clock = Clock()
    bind_in_background(
        reg, log, lambda: bind(reg, zmx, opener, 10, clock.sleep, clock.now)
    )
    for _ in range(100):
        if log.exists() and log.read_text().endswith("\n"):
            break
        time.sleep(0.05)
    return log.read_text()


def test_no_daemon_at_prepare_keeps_an_empty_snapshot(tmp_path: Path) -> None:
    opener = LateDaemon(None, None)
    reg = _prepare_late(tmp_path, opener, FakeZmx())
    assert opener.opens == 1
    assert reg.before == {} and reg.busy == set()
    assert reg.since == SINCE and reg.snapshot is False


def test_a_bad_answer_from_an_open_daemon_still_fails_closed(tmp_path: Path) -> None:
    class Broken(FakeDaemon):
        def loaded_threads(self) -> list[str]:
            raise DaemonError("unexpected answer to thread/loaded/list")

    work, daemon, zmx = str(tmp_path), Broken([{}]), FakeZmx()
    with pytest.raises(ZpcError) as err:
        prepare("codex", "w-x", work, None, zmx, tmp_path, lambda: daemon, NOW)
    assert err.value.code == 3
    # The lock was let go: the next registration in the directory goes ahead.
    again = prepare("claude", "w-c", work, None, zmx, tmp_path, _no_daemon)
    assert again is not None and again.lock is not None
    again.lock.close()


def test_a_daemon_that_comes_up_late_binds_the_new_thread(tmp_path: Path) -> None:
    # Seen on the box: the launcher registered the Codex session before its
    # TUI started the box's first daemon.
    work = str((tmp_path / "work").resolve())
    opened = {THREAD_C: thread(THREAD_C, work, SINCE + 2, created=SINCE + 2)}
    daemon = FakeDaemon([{}, opened])
    opener, zmx = LateDaemon(daemon, 4), FakeZmx()  # prepare and three bind opens
    zmx.footers["w-codex"] = tui_footer(daemon, THREAD_C)
    reg = _prepare_late(tmp_path, opener, zmx)
    assert reg.snapshot is False
    line = _bind_logged(reg, zmx, opener, tmp_path / "register.log")
    assert f"zpc.thread={THREAD_C}" in line
    assert line.endswith(" (no Codex daemon at registration)\n")


def test_a_daemon_that_never_comes_up_sets_no_label(tmp_path: Path) -> None:
    opener, zmx = LateDaemon(None, None), FakeZmx()
    reg = _prepare_late(tmp_path, opener, zmx)
    line = _bind_logged(reg, zmx, opener, tmp_path / "register.log")
    assert "w-codex: no Codex daemon was reachable in time (last error: " in line
    assert "cannot start codex" in line and line.endswith("; no label set\n")
    assert zmx.live["w-codex"].labels == {}


def test_a_late_daemon_binds_the_new_thread_not_a_leftover(tmp_path: Path) -> None:
    # With no snapshot, a turn-less leftover reads as created after it, like
    # the new TUI's thread; only the one the footer shows is bound.
    work = str((tmp_path / "work").resolve())
    clock = Clock()
    table = {
        THREAD_A: thread(THREAD_A, work, 5, created=5),
        THREAD_C: thread(THREAD_C, work, SINCE + 1, created=SINCE + 1),
    }
    daemon = FakeDaemon([table], {THREAD_A}, lambda: SINCE + clock.t)
    opener, zmx = LateDaemon(daemon, 3), FakeZmx()
    zmx.footers["w-codex"] = tui_footer(daemon, THREAD_C)
    reg = _prepare_late(tmp_path, opener, zmx)
    got = bind(reg, zmx, opener, 10, clock.sleep, clock.now)
    assert got["zpc.thread"] == THREAD_C
    assert daemon.names == {
        THREAD_A: f"zpc-{reg.inc}-unbound",
        THREAD_C: f"zpc-{reg.inc}",
    }
    assert zmx.set_calls == [("w-codex", got)]


def test_two_registrations_in_one_directory_refuse(tmp_path: Path) -> None:
    zmx = FakeZmx()
    first = prepare("claude", "w-1", str(tmp_path), None, zmx, tmp_path, _no_daemon)
    try:
        with pytest.raises(ZpcError) as err:
            prepare("codex", "w-2", str(tmp_path), None, zmx, tmp_path, _no_daemon)
        assert err.value.code == 4
    finally:
        assert first is not None and first.lock is not None
        first.lock.close()
    again = prepare("claude", "w-2", str(tmp_path), None, zmx, tmp_path, _no_daemon)
    assert again is not None and again.lock is not None
    again.lock.close()


def test_session_that_never_appears_gets_no_label(tmp_path: Path) -> None:
    zmx, clock = FakeZmx(), Clock()
    reg = prepare("claude", "w-x", str(tmp_path), None, zmx, tmp_path, _no_daemon)
    assert reg is not None and reg.lock is not None
    try:
        with pytest.raises(ZpcError, match="did not appear") as err:
            bind(reg, zmx, _no_daemon, 10, clock.sleep, clock.now)
    finally:
        reg.lock.close()
    assert err.value.code == 5 and zmx.set_calls == []


@pytest.mark.parametrize(
    ("role", "session", "code"),
    [("opencode", "w-x", 2), ("claude", "-x", 2), ("claude", "a/b", 2)],
)
def test_bad_arguments_exit_2(
    tmp_path: Path, role: str, session: str, code: int
) -> None:
    with pytest.raises(ZpcError) as err:
        prepare(role, session, str(tmp_path), None, FakeZmx(), tmp_path, _no_daemon)
    assert err.value.code == code


def test_pair_id_comes_from_the_full_path(tmp_path: Path) -> None:
    for parent in ("a", "b"):
        (tmp_path / parent / "foo").mkdir(parents=True)
    os.symlink(tmp_path / "a" / "foo", tmp_path / "link")
    a, b = pair_id(str(tmp_path / "a" / "foo")), pair_id(str(tmp_path / "b" / "foo"))
    assert a != b
    assert pair_id(str(tmp_path / "link")) == a
    assert pair_id(str(tmp_path), "two") == "two"
    with pytest.raises(ZpcError):
        pair_id(str(tmp_path), "../x")
