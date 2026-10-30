"""The wait's owner from a fake process table, in the /proc and the ps form."""

from __future__ import annotations

from pathlib import Path

import ac_fakes as f
import pytest

from agent_chat.procs import LinuxProcs, PsProcs, alive, claude_ancestor

ARGV0 = [
    "/usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe",
    "/usr/lib/node_modules/happy-coder/node_modules/@anthropic-ai/claude-agent-sdk/claude",
]
CHAIN = {10: (1, "/usr/bin/node"), 30: (20, "/bin/sh"), 40: (30, "python3")}


def linux(tmp_path: Path, rows: dict[int, tuple[int, str]]) -> LinuxProcs:
    for pid, (ppid, argv0) in rows.items():
        f.proc_entry(tmp_path / "proc", pid, ppid, argv0)
    return LinuxProcs(str(tmp_path / "proc"))


def mac(tmp_path: Path, rows: dict[int, tuple[int, str]]) -> PsProcs:
    table = tmp_path / "ps-table"
    f.ps_table(table, rows)
    return PsProcs(str(f.fake_ps(tmp_path, table)))


@pytest.mark.parametrize("form", [linux, mac])
@pytest.mark.parametrize("argv0", ARGV0)
def test_finds_the_claude_above_the_hook(tmp_path: Path, form, argv0: str) -> None:
    table = form(tmp_path, {**CHAIN, 20: (10, argv0)})
    assert claude_ancestor(table, 40) == 20
    assert alive(table, 20)
    assert not alive(table, 99)


@pytest.mark.parametrize("form", [linux, mac])
def test_no_claude_above_means_no_owner(tmp_path: Path, form) -> None:
    table = form(tmp_path, {**CHAIN, 20: (10, "/usr/bin/claude-helper")})
    assert claude_ancestor(table, 40) is None


def test_ps_form_takes_argv0_from_the_args_column(tmp_path: Path) -> None:
    table = mac(
        tmp_path, {20: (1, "/Applications/x/claude --resume abc"), 40: (20, "sh")}
    )
    assert table.entry(20) == (1, "/Applications/x/claude")
    assert claude_ancestor(table, 40) == 20


def test_a_zombie_counts_as_gone(tmp_path: Path) -> None:
    table = linux(tmp_path, {20: (1, "claude")})
    stat = tmp_path / "proc" / "20" / "stat"
    stat.write_text(stat.read_text().replace(" S ", " Z "))
    assert not alive(table, 20)


def test_ps_form_finds_a_claude_under_a_path_with_a_space(tmp_path: Path) -> None:
    binary = tmp_path / "Claude Tools" / "claude"
    binary.parent.mkdir()
    binary.write_text("")
    table = mac(tmp_path, {20: (1, f"{binary} --resume x"), 40: (20, "sh")})
    assert table.entry(20) == (1, str(binary))
    assert claude_ancestor(table, 40) == 20
