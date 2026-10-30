"""The sync loop: wait for messages that address one account.

Claude's ``hook-wait`` (one room, :class:`Listener`) and the Codex watcher
(every agent room) share :class:`SyncLoop`. The cursor is saved before a batch
is handed on, so a crash after reading never replays it; it is not saved when
the owner is gone, so the next wait delivers that batch.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator
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
MEMBER = "m.room.member"


def filter_definition(limit: int = TIMELINE_LIMIT) -> dict[str, Any]:
    """Room messages, and membership so a lost room shows; nothing else.

    State, ephemeral, presence and account data are excluded. Membership
    events ride in the timeline because a server may leave a room the account
    was removed from out of a sync whose filter lets none of its events through.
    """
    return {
        "presence": _NONE,
        "account_data": _NONE,
        "room": {
            "timeline": {"types": ["m.room.message", MEMBER], "limit": limit},
            "state": _NONE,
            "ephemeral": _NONE,
            "account_data": _NONE,
        },
    }


def _joins(event: Any, account: str) -> bool:
    """Tell whether ``event`` is ``account`` joining (not a profile change)."""
    if not isinstance(event, dict) or event.get("type") != MEMBER:
        return False
    if event.get("state_key") != account:
        return False
    content = event.get("content") or {}
    prev = (event.get("unsigned") or {}).get("prev_content") or {}
    return content.get("membership") == "join" and prev.get("membership") != "join"


def since_join(events: list[Any], account: str) -> list[Any]:
    """Drop the events up to ``account``'s own join in this timeline.

    The first sync after a join carries some of the room's history; those
    messages were posted before the account was there and are not mail.
    """
    last = max((i for i, e in enumerate(events) if _joins(e, account)), default=-1)
    return events[last + 1 :]


def timeline(rooms: dict[str, Any], room: str) -> list[Any]:
    """Return the timeline events of joined ``room`` in a sync's ``rooms``."""
    joined = (rooms.get("join") or {}).get(room) or {}
    return (joined.get("timeline") or {}).get("events") or []


@dataclass
class WaitResult:
    """How a wait ended: ``mail``, ``timeout``, ``owner-gone`` or ``no-room``."""

    outcome: str
    messages: list[Message] = field(default_factory=list)


class SyncLoop:
    """One account's sync loop with a persisted cursor.

    Args:
        client: The account's homeserver client.
        cfg: The host's configuration.
        account: The listening account's full ID.
        state: The account's state directory.
        cursor_name: The cursor file's name, without ``.cursor``.
    """

    def __init__(
        self, client: Client, cfg: Config, account: str, state: Path, cursor_name: str
    ) -> None:
        self.client = client
        self.cfg = cfg
        self.account = account
        self.state = state
        self.cursor_file = state / f"{cursor_name}.cursor"
        self.owner_gone = False

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
        token = str(self._sync(None, first, 0, deadline)["next_batch"])
        self._save(token)
        return token

    def _sync(
        self, since: str | None, filt: str, seconds: float, deadline: float
    ) -> dict[str, Any]:
        """One ``/sync``; a subclass may wrap it."""
        return self.client.sync(since, filt, seconds, deadline)

    def mail(self, events: list[Any]) -> list[Message]:
        """Return the messages among ``events`` that wake this account."""
        return [
            Message(str(e["sender"]), str(e["content"]["body"]))
            for e in since_join(events, self.account)
            if isinstance(e, dict) and wakes(e, self.account, self.cfg)
        ]

    def batches(
        self,
        deadline: float,
        owner_alive: Callable[[], bool],
        now: Callable[[], float] = time.monotonic,
    ) -> Iterator[dict[str, Any]]:
        """Yield each sync's ``rooms``, its cursor already saved.

        Stops at ``deadline``, or once ``owner_alive`` says no; then
        :attr:`owner_gone` is set and that last batch's cursor is not saved.
        """
        fid = self._filter(deadline)
        since = self.cursor() or self._start(deadline)
        recovered = 0
        while (remaining := deadline - now()) > 0:
            try:
                got = self._sync(since, fid, min(SYNC_SECONDS, remaining), deadline)
            except MatrixError as exc:
                # A rejected filter is registered again; a rejected cursor
                # restarts from now. Each once.
                if exc.status not in (400, 404) or recovered == 2:
                    raise
                recovered += 1
                if recovered == 1:
                    fid = self._filter(deadline, fresh=True)
                else:
                    since = self._start(deadline)
                continue
            if not owner_alive():
                self.owner_gone = True
                return
            since = str(got["next_batch"])
            self._save(since)
            yield got.get("rooms") or {}


class Listener(SyncLoop):
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
        super().__init__(client, cfg, account, state, alias_slug(alias))
        self.alias = alias
        self.rooms = Rooms(client, cfg, state)

    def _left(self, room: str, rooms: dict[str, Any]) -> bool:
        """Tell whether this sync shows the account out of ``room``."""
        if room in (rooms.get("leave") or {}):
            return True
        return any(
            isinstance(e, dict)
            and e.get("type") == MEMBER
            and e.get("state_key") == self.account
            and (e.get("content") or {}).get("membership") in ("leave", "ban")
            for e in timeline(rooms, room)
        )

    def wait(
        self,
        deadline: float,
        owner_alive: Callable[[], bool],
        now: Callable[[], float] = time.monotonic,
    ) -> WaitResult:
        """Wait until mail arrives, ``deadline`` passes or the owner is gone."""
        room = self.rooms.room_id(self.alias, deadline, verify=True)
        if room is None:
            return WaitResult("no-room")
        rejoined = False
        for rooms in self.batches(deadline, owner_alive, now):
            if not rejoined and self._left(room, rooms):
                # The cached room is gone for this account: resolve the alias again.
                self.rooms.forget(self.alias)
                room, rejoined = (
                    self.rooms.room_id(self.alias, deadline, refresh=True),
                    True,
                )
                if room is None:
                    return WaitResult("no-room")
            mail = self.mail(timeline(rooms, room))
            if mail:
                return WaitResult("mail", mail)
        return WaitResult("owner-gone" if self.owner_gone else "timeout")
