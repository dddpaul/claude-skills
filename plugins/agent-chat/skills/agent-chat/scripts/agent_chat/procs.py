"""The wait's owner: the nearest Claude Code process above the command.

Linux answers from ``/proc``; macOS has no ``/proc`` and answers from ``ps``.
"""

from __future__ import annotations

import os
import subprocess
from typing import Protocol

# argv[0] basenames of a Claude Code process: the npm package's native binary
# runs as claude.exe, the Agent SDK's bundled binary (Happy's remote mode) as
# claude.
CLAUDE_NAMES = {"claude", "claude.exe"}


class ProcTable(Protocol):
    """Read access to the process table."""

    def entry(self, pid: int) -> tuple[int, str] | None:
        """Return (parent pid, argv[0]) of ``pid``, or None when it is gone."""
        ...


class LinuxProcs:
    """The process table in ``/proc`` (or a fake of it under ``root``)."""

    def __init__(self, root: str = "/proc") -> None:
        self.root = root

    def entry(self, pid: int) -> tuple[int, str] | None:
        try:
            with open(
                f"{self.root}/{pid}/stat", encoding="utf-8", errors="replace"
            ) as f:
                stat = f.read()
            with open(f"{self.root}/{pid}/cmdline", "rb") as f:
                cmdline = f.read()
        except OSError:
            return None
        # The command name sits in parentheses and may itself hold spaces.
        rest = stat[stat.rfind(")") + 2 :].split()
        if len(rest) < 2 or not rest[1].isdigit() or rest[0] == "Z":
            return None
        return int(rest[1]), cmdline.split(b"\0", 1)[0].decode(errors="replace")


class PsProcs:
    """The process table as ``ps -o ppid= -o args= -p <pid>`` shows it (macOS)."""

    def __init__(self, ps: str = "ps") -> None:
        self.ps = ps

    def entry(self, pid: int) -> tuple[int, str] | None:
        try:
            out = subprocess.run(
                [self.ps, "-o", "ppid=", "-o", "args=", "-p", str(pid)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        fields = out.stdout.strip().split(None, 1)
        if out.returncode != 0 or not fields or not fields[0].isdigit():
            return None
        return int(fields[0]), (fields[1].split() or [""])[0] if len(fields) > 1 else ""


def system_table() -> ProcTable:
    """Return the table for this system: ``/proc`` when it exists, else ``ps``."""
    return LinuxProcs() if os.path.isdir("/proc/self") else PsProcs()


def alive(table: ProcTable, pid: int) -> bool:
    """Tell whether ``pid`` is in the process table."""
    return table.entry(pid) is not None


def claude_ancestor(table: ProcTable, start: int | None = None) -> int | None:
    """Return the pid of the nearest Claude Code process above ``start``.

    A hook runs below the ``claude`` process that started it; that process is
    the wait's owner, and the wait ends when it exits.

    Args:
        table: The process table to read.
        start: The pid to start from; defaults to this process's parent.
    """
    pid = os.getppid() if start is None else start
    seen: set[int] = set()
    while pid > 1 and pid not in seen:
        seen.add(pid)
        got = table.entry(pid)
        if got is None:
            return None
        if os.path.basename(got[1]) in CLAUDE_NAMES:
            return pid
        pid = got[0]
    return None
