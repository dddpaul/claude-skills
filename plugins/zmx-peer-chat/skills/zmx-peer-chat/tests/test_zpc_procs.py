"""The wait's owner: the nearest ``claude`` process above the command.

Local mode runs the npm package's ``claude.exe``; Happy's remote mode runs the
Agent SDK's bundled ``claude``. A command name with spaces or parentheses in
``/proc/<pid>/stat`` must not shift the parent pid.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import zpc_fakes  # noqa: F401 - puts the zpc package on sys.path

from zpc.procs import claude_ancestor


def _proc(root: Path, pid: int, ppid: int, comm: str, argv0: str) -> None:
    d = root / str(pid)
    d.mkdir()
    (d / "stat").write_text(f"{pid} ({comm}) S {ppid} {pid} {pid} 0 -1\n")
    (d / "cmdline").write_bytes(argv0.encode() + b"\0--flag\0")


@pytest.mark.parametrize(
    "argv0",
    [
        "/usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe",
        "/usr/lib/node_modules/happy-coder/node_modules/@anthropic-ai/"
        "claude-agent-sdk-linux-x64/claude",
    ],
)
def test_finds_the_claude_above_the_hook(tmp_path: Path, argv0: str) -> None:
    _proc(tmp_path, 10, 1, "node", "/usr/bin/node")
    _proc(tmp_path, 20, 10, "claude", argv0)
    _proc(tmp_path, 30, 20, "sh", "/bin/sh")
    _proc(tmp_path, 40, 30, "python3 (zpc) x", "python3")
    assert claude_ancestor(40, str(tmp_path)) == 20


def test_no_claude_above_is_none(tmp_path: Path) -> None:
    _proc(tmp_path, 10, 1, "bash", "-bash")
    _proc(tmp_path, 20, 10, "python3", "python3")
    assert claude_ancestor(20, str(tmp_path)) is None
    assert claude_ancestor(99, str(tmp_path)) is None
