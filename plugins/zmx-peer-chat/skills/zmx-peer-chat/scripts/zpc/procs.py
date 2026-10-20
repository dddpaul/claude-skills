"""Process helpers: is a pid alive, and which claude process owns this command."""

from __future__ import annotations

import os

# argv[0] basenames of a Claude Code process: the npm package's native binary
# runs as claude.exe, the Agent SDK's bundled binary (Happy's remote mode) as
# claude.
CLAUDE_NAMES = {"claude", "claude.exe"}


def pid_alive(pid: int) -> bool:
    """Tell whether process ``pid`` exists (EPERM still means it exists)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _parent(pid: int, proc: str) -> int | None:
    try:
        with open(f"{proc}/{pid}/stat", encoding="utf-8", errors="replace") as f:
            stat = f.read()
    except OSError:
        return None
    # The command name sits in parentheses and may itself hold spaces.
    rest = stat[stat.rfind(")") + 2 :].split()
    return int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else None


def _argv0(pid: int, proc: str) -> str:
    try:
        with open(f"{proc}/{pid}/cmdline", "rb") as f:
            raw = f.read()
    except OSError:
        return ""
    return raw.split(b"\0", 1)[0].decode(errors="replace")


def claude_ancestor(start: int | None = None, proc: str = "/proc") -> int | None:
    """Return the pid of the nearest Claude Code process above ``start``.

    A background Bash task or a hook runs below the ``claude`` process that
    started it; that process is the wait's owner, and the wait ends when it
    exits (a Happy mode switch replaces it).

    Args:
        start: The pid to start from; defaults to this process's parent.
        proc: The procfs mount, overridable for tests.
    """
    pid = os.getppid() if start is None else start
    seen: set[int] = set()
    while pid and pid > 1 and pid not in seen:
        seen.add(pid)
        if os.path.basename(_argv0(pid, proc)) in CLAUDE_NAMES:
            return pid
        pid = _parent(pid, proc) or 0
    return None
