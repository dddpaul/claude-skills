"""The register helper: labels read before any attach, and the Codex thread pick.

The launcher calls ``register`` just before ``zmx attach`` creates a session.
An existing session keeps its labels (``zmx attach --labels`` would overwrite
them, so nothing here attaches). For Codex the helper snapshots the daemon's
loaded threads and binds the one thread the new TUI opened in the session
directory: a newly loaded id created after the snapshot, or a thread whose
``updatedAt`` moved past it (``codex resume --last``). A thread that is only
loaded again keeps its old times and is no candidate. Zero or several
candidates set no label.
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
    thread,
)

from zpc.common import ZpcError, pair_id
from zpc.register import Registration, bind, prepare
from zpc.zmx import Session, Zmx


BIN = Path(__file__).resolve().parents[3] / "bin" / "zmx-peer-chat"

# The wall clock at the snapshot; the fake threads' times are on the same scale.
SINCE = 1000


def NOW() -> float:  # noqa: N802 - a constant clock
    return SINCE + 0.4


def _no_daemon() -> FakeDaemon:
    raise AssertionError("the daemon must not be asked")


def _register(
    tmp_path: Path, daemon: FakeDaemon, zmx: FakeZmx, clock: Clock
) -> tuple[Registration, dict[str, str]]:
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    reg = prepare(
        "codex", "w-codex", str(work), None, zmx, tmp_path, lambda: daemon, NOW
    )
    assert reg is not None
    zmx.live["w-codex"] = Session("w-codex", 42)
    try:
        return reg, bind(reg, zmx, lambda: daemon, 10, clock.sleep, clock.now)
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
    reg, got = _register(tmp_path, daemon, zmx, Clock())
    assert got["zpc.thread"] == THREAD_C
    assert daemon.names == {THREAD_C: f"zpc-{reg.inc}"}
    assert zmx.set_calls == [("w-codex", got)]


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
    reg, got = _register(tmp_path, daemon, FakeZmx(), Clock())
    assert got["zpc.thread"] == THREAD_B
    assert daemon.names == {THREAD_B: f"zpc-{reg.inc}"}


def test_resume_of_an_unloaded_thread_binds_it(tmp_path: Path) -> None:
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    after = {THREAD_B: thread(THREAD_B, work, SINCE + 2, created=3)}
    daemon = FakeDaemon([{}, {}, after])
    _, got = _register(tmp_path, daemon, FakeZmx(), Clock())
    assert got["zpc.thread"] == THREAD_B


def test_an_older_thread_loaded_again_is_no_candidate(tmp_path: Path) -> None:
    # Seen on the box: while `codex resume --last` resumed one thread, the
    # starting TUI loaded another, turnless thread of the same directory
    # again. It keeps its old times; only the resumed thread is bound.
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    reloaded = thread(THREAD_C, work, 700, created=700)
    resumed = thread(THREAD_B, work, SINCE + 1, created=600)
    daemon = FakeDaemon(
        [{}, {THREAD_C: reloaded}, {THREAD_C: reloaded, THREAD_B: resumed}]
    )
    reg, got = _register(tmp_path, daemon, FakeZmx(), Clock())
    assert got["zpc.thread"] == THREAD_B
    assert daemon.names == {THREAD_B: f"zpc-{reg.inc}"}


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
    reg, got = _register(tmp_path, daemon, FakeZmx(), Clock())
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


def test_several_candidates_set_no_label(tmp_path: Path) -> None:
    work = str((tmp_path / "work").resolve())
    (tmp_path / "work").mkdir()
    before = {THREAD_A: thread(THREAD_A, work, 5)}
    after = {
        THREAD_A: thread(THREAD_A, work, SINCE + 1),
        THREAD_C: thread(THREAD_C, work, SINCE + 1, created=SINCE + 1),
    }
    daemon, zmx = FakeDaemon([before, after]), FakeZmx()
    with pytest.raises(ZpcError, match="refusing to guess") as err:
        _register(tmp_path, daemon, zmx, Clock())
    assert err.value.code == 4
    assert zmx.set_calls == [] and daemon.names == {}


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
