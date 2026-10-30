"""The sync loop: wait for messages that address one account in one room.

Claude's ``hook-wait`` and the Codex watcher share it. The cursor is saved
before the messages are returned, so a crash after reading never replays
them; it is not saved when the owner is gone, so the next wait delivers them.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .addressing import wakes
from .config import Config
from .matrix import Client, MatrixError
from .note import Message
from .room import Rooms, alias_slug, read_json, write_json

# Each /sync long-polls for at most this long, so a gone owner is noticed soon.
SYNC_SECONDS = 30.0
TIMELINE_LIMIT = 50
_NONE = {"not_types": ["*"]}


def filter_definition(limit: int = TIMELINE_LIMIT) -> dict[str, Any]:
    """Room messages only; state, ephemeral, presence and account data excluded."""
    return {
        "presence": _NONE,
        "account_data": _NONE,
        "room": {
            "timeline": {"types": ["m.room.message"], "limit": limit},
            "state": _NONE,
            "ephemeral": _NONE,
            "account_data": _NONE,
        },
    }


@dataclass
class WaitResult:
    """How a wait ended: ``mail``, ``timeout``, ``owner-gone`` or ``no-room``."""

    outcome: str
    messages: list[Message] = field(default_factory=list)


class Listener:
    """Waits for mail to ``account`` in the room behind ``alias``.

    Args:
        client: The account's homeserver client.
        cfg: The host's configuration.
        account: The listening account's full ID.
        state: The account's state directory.
        alias: The project room's alias.
    """

    def __init__(
        self, client: Client, cfg: Config, account: str, state: Path, alias: str
    ) -> None:
        self.client = client
        self.cfg = cfg
        self.account = account
        self.state = state
        self.alias = alias
        self.rooms = Rooms(client, cfg, state)
        self.cursor_file = state / f"{alias_slug(alias)}.cursor"

    def _filter(self, deadline: float, fresh: bool = False) -> str:
        path = self.state / "filter.json"
        definition = filter_definition()
        key = json.dumps(definition, sort_keys=True)
        cached = read_json(path)
        if not fresh and cached.get("definition") == key and "id" in cached:
            return str(cached["id"])
        fid = self.client.create_filter(self.account, definition, deadline)
        write_json(path, {"definition": key, "id": fid})
        return fid

    def cursor(self) -> str | None:
        """Return the saved sync cursor, if any."""
        value = read_json(self.cursor_file).get("next_batch")
        return value if isinstance(value, str) and value else None

    def _save(self, token: str) -> None:
        write_json(self.cursor_file, {"next_batch": token})

    def _start(self, deadline: float) -> str:
        """First run: a sync with a timeline limit of 0 gives "now" as the cursor."""
        first = json.dumps(filter_definition(limit=0), separators=(",", ":"))
        token = str(self.client.sync(None, first, 0, deadline)["next_batch"])
        self._save(token)
        return token

    def _mail(self, events: list[dict[str, Any]]) -> list[Message]:
        return [
            Message(str(e["sender"]), str(e["content"]["body"]))
            for e in events
            if isinstance(e, dict) and wakes(e, self.account, self.cfg)
        ]

    def wait(
        self,
        deadline: float,
        owner_alive: Callable[[], bool],
        now: Callable[[], float] = time.monotonic,
    ) -> WaitResult:
        """Wait until mail arrives, ``deadline`` passes or the owner is gone."""
        room = self.rooms.room_id(self.alias, deadline)
        if room is None:
            return WaitResult("no-room")
        fid = self._filter(deadline)
        since = self.cursor() or self._start(deadline)
        rejoined = refiltered = False
        while (remaining := deadline - now()) > 0:
            try:
                got = self.client.sync(
                    since, fid, min(SYNC_SECONDS, remaining), deadline
                )
            except MatrixError as exc:
                if refiltered or exc.status not in (400, 404):
                    raise
                fid, refiltered = self._filter(deadline, fresh=True), True
                continue
            if not owner_alive():
                return WaitResult("owner-gone")
            rooms = got.get("rooms") or {}
            if room in (rooms.get("leave") or {}) and not rejoined:
                # The cached room is gone for this account: resolve the alias again.
                self.rooms.forget(self.alias)
                room, rejoined = self.rooms.room_id(self.alias, deadline, True), True
                if room is None:
                    return WaitResult("no-room")
            joined = (rooms.get("join") or {}).get(room) or {}
            mail = self._mail((joined.get("timeline") or {}).get("events") or [])
            since = str(got["next_batch"])
            self._save(since)
            if mail:
                return WaitResult("mail", mail)
        return WaitResult("timeout")
