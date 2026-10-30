"""Fixtures: a configured host, a fake homeserver, a fake owner process table."""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import ac_fakes as f
import pytest

from agent_chat import cli, matrix, procs


@dataclass
class Host:
    """A configured host: its home, project directory and fake homeserver."""

    home: Path
    project: Path
    hs: f.FakeHomeserver

    @property
    def config(self) -> Path:
        return self.home / ".config" / "agent-chat"

    def state(self, account: str = f.CLAUDE_A) -> Path:
        return self.home / ".local" / "state" / "agent-chat" / account[1:].split(":")[0]

    def cursor(self, account: str = f.CLAUDE_A) -> str | None:
        path = self.state(account) / f"agents-{f.PROJECT}.cursor"
        return path.read_text() if path.exists() else None


@dataclass
class Owner:
    """A fake /proc where this test's parent pid sits below a ``claude`` process."""

    root: Path
    pid: int = 5000

    def exits(self) -> None:
        """The owner process exits."""
        for p in (self.root / str(self.pid)).iterdir():
            p.unlink()
        (self.root / str(self.pid)).rmdir()

    def arrives(self, pid: int) -> None:
        """A new claude process ``pid`` now sits above this test's parent."""
        f.proc_entry(self.root, pid, 1, "/opt/claude/bin/claude")
        f.proc_entry(self.root, os.getppid(), pid, "/bin/sh")
        self.pid = pid


@dataclass
class PsOwner:
    """The same as :class:`Owner`, in the macOS ``ps`` form."""

    table: Path
    rows: dict[int, tuple[int, str]]
    pid: int = 5000

    def exits(self) -> None:
        del self.rows[self.pid]
        f.ps_table(self.table, self.rows)

    def arrives(self, pid: int) -> None:
        self.rows[pid] = (1, "/opt/claude/bin/claude.exe")
        self.rows[os.getppid()] = (pid, "/bin/sh")
        self.pid = pid
        f.ps_table(self.table, self.rows)


@pytest.fixture
def hs() -> Iterator[f.FakeHomeserver]:
    server = f.FakeHomeserver()
    server.room(
        f.ALIAS,
        f.ROOM,
        joined={f.HUMAN, f.CLAUDE_A, f.CODEX_A, f.CLAUDE_B, f.CODEX_B, f.STRANGER},
        invited=set(),
    )
    yield server
    server.close()


@pytest.fixture
def host(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hs: f.FakeHomeserver) -> Host:
    home = tmp_path / "home"
    project = tmp_path / "work" / f.PROJECT
    project.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    for var in ("XDG_CONFIG_HOME", "XDG_STATE_HOME", "HTTPS_PROXY", "https_proxy"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv(cli.LISTEN_ENV, "1")
    monkeypatch.chdir(project)
    monkeypatch.setattr(matrix, "BACKOFF_FIRST", 0.01)
    monkeypatch.setattr(matrix, "BACKOFF_MAX", 0.05)
    f.write_config(
        home, f"http://127.0.0.1:{hs.port}", {"claude": f.CLAUDE_A, "codex": f.CODEX_A}
    )
    return Host(home, project, hs)


@pytest.fixture
def owner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Owner:
    root = tmp_path / "proc"
    f.proc_entry(root, 5000, 1, "/opt/claude/bin/claude.exe")
    f.proc_entry(root, os.getppid(), 5000, "/bin/sh")
    monkeypatch.setattr(procs, "system_table", lambda: procs.LinuxProcs(str(root)))
    return Owner(root)


@pytest.fixture
def ps_owner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PsOwner:
    table = tmp_path / "ps-table"
    rows = {os.getppid(): (5000, "/bin/sh"), 5000: (1, "/opt/claude/bin/claude")}
    f.ps_table(table, rows)
    ps = f.fake_ps(tmp_path, table)
    monkeypatch.setattr(procs, "system_table", lambda: procs.PsProcs(str(ps)))
    return PsOwner(table, rows)


@pytest.fixture(params=["proc", "ps"])
def any_owner(request: pytest.FixtureRequest) -> Owner | PsOwner:
    """The owner in the Linux /proc form, then in the macOS ps form."""
    return request.getfixturevalue("owner" if request.param == "proc" else "ps_owner")
