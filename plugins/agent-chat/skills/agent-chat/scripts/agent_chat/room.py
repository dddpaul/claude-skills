"""The project's room: its alias, the cached room ID, and joining on first use."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from .config import AgentChatError, Config
from .matrix import Client

_SAFE = re.compile(r"[A-Za-z0-9._-]{1,64}")


def project_alias(cfg: Config, cwd: str | None = None) -> str:
    """Return ``#<room_prefix><basename of the physical cwd>:<server_name>``."""
    base = os.path.basename(os.path.realpath(cwd or os.getcwd()))
    return f"#{cfg.room_prefix}{base}:{cfg.server_name}"


def alias_slug(alias: str) -> str:
    """Return a file-name-safe key for ``alias`` (its localpart, or a hash)."""
    local = alias[1:].split(":", 1)[0]
    if _SAFE.fullmatch(local) and not local.startswith("."):
        return local
    return "h" + hashlib.sha256(alias.encode()).hexdigest()[:16]


def write_json(path: Path, data: Any) -> None:
    """Write ``data`` to ``path`` atomically and durably, mode 0600."""
    tmp = path.with_name(f".{path.name}.{os.getpid()}")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def read_json(path: Path) -> dict[str, Any]:
    """Return the JSON object in ``path``, or an empty one."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


class Rooms:
    """Resolves the project's alias to a room this account has joined.

    The room ID is cached in ``rooms.json`` in the account's state directory.
    """

    def __init__(self, client: Client, cfg: Config, state: Path) -> None:
        self.client = client
        self.cfg = cfg
        self.cache = state / "rooms.json"

    def forget(self, alias: str) -> None:
        """Drop the cached room ID of ``alias``."""
        cached = read_json(self.cache)
        if cached.pop(alias, None) is not None:
            write_json(self.cache, cached)

    def room_id(self, alias: str, deadline: float, refresh: bool = False) -> str | None:
        """Return the joined room behind ``alias``, or None when it does not resolve.

        An account that is invited but has not joined joins here, and only for
        aliases that carry the configured ``room_prefix``.

        Args:
            alias: The room alias.
            deadline: When retries stop.
            refresh: Ignore the cache and ask the homeserver.
        """
        cached = read_json(self.cache)
        if not refresh and isinstance(cached.get(alias), str):
            return cached[alias]
        room = self.client.resolve_alias(alias, deadline)
        if room is None:
            self.forget(alias)
            return None
        if room not in self.client.joined_rooms(deadline):
            if not alias.startswith(f"#{self.cfg.room_prefix}"):
                raise AgentChatError(f"refusing to join {alias}: not an agent room")
            self.client.join(alias, deadline)
        cached[alias] = room
        write_json(self.cache, cached)
        return room
