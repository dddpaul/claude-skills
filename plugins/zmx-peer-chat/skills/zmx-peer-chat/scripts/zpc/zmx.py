"""A thin wrapper around the zmx CLI: list sessions with their labels, set labels.

Labels are only ever set with ``zmx set`` on a session that already exists:
``zmx attach --labels`` on a live session overwrites its labels, so this
module never attaches.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field

from .common import ZpcError

# Fields `zmx ls` prints for every session; any other key=value field is a label.
_BUILTIN = {"name", "pid", "clients", "created", "cwd", "cmd"}


@dataclass
class Session:
    """One live zmx session as `zmx ls` reports it."""

    name: str
    pid: int | None = None
    labels: dict[str, str] = field(default_factory=dict)


def parse_ls(text: str) -> dict[str, Session]:
    """Parse `zmx ls` output into sessions keyed by name.

    Each line is tab-separated ``key=value`` fields, starting with ``name=``
    (the line may be indented or carry a marker before it).

    Raises:
        ZpcError: When a line has no ``name=`` field.
    """
    sessions: dict[str, Session] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        start = line.find("name=")
        if start < 0:
            raise ZpcError(f"unexpected zmx ls line: {line!r}")
        fields = dict(
            part.split("=", 1) for part in line[start:].split("\t") if "=" in part
        )
        name = fields["name"]
        pid = fields.get("pid", "")
        labels = {k: v for k, v in fields.items() if k not in _BUILTIN}
        sessions[name] = Session(name, int(pid) if pid.isdigit() else None, labels)
    return sessions


class Zmx:
    """Run zmx commands; ``ZPC_ZMX`` overrides the binary (tests use a fake)."""

    def __init__(self, exe: str | None = None) -> None:
        self.exe = exe or os.environ.get("ZPC_ZMX", "zmx")

    def _run(self, *args: str) -> str:
        try:
            done = subprocess.run(
                [self.exe, *args], capture_output=True, text=True, timeout=10
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ZpcError(f"zmx {args[0]} failed: {exc}") from exc
        if done.returncode != 0:
            why = done.stderr.strip() or f"exit {done.returncode}"
            raise ZpcError(f"zmx {args[0]} failed: {why}")
        return done.stdout

    def sessions(self) -> dict[str, Session]:
        """Return every live session with its labels."""
        return parse_ls(self._run("ls"))

    def set_labels(self, name: str, labels: dict[str, str]) -> None:
        """Merge ``labels`` into the labels of the existing session ``name``."""
        self._run("set", name, *(f"{k}={v}" for k, v in sorted(labels.items())))

    def history(self, name: str) -> str:
        """Return the plain-text scrollback of session ``name``."""
        return self._run("history", name)
