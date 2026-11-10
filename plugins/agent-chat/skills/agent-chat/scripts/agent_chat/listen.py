"""The sync loop: wait for messages that address one account.

Claude's ``hook-wait`` (one room, :class:`Listener`) and the Codex watcher
(every agent room) share :class:`SyncLoop`. The cursor is saved before a batch
is handed on, so a crash after reading never replays it; it is not saved when
the owner is gone, so the next wait delivers that batch.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .addressing import (
    Wake,
    addressees,
    hub_field,
    hub_wakes,
    project_address,
    root_address,
    thread_root,
    wakes,
)
from .config import PROJECT_TOKEN, AgentChatError, Config
from .matrix import AuthError, Client, MatrixError
from .note import HubMail, Message
from .room import Rooms, alias_slug, read_json, write_json
from .threads import Budget, Thread

# Each /sync long-polls for at most this long, so a gone owner is noticed soon.
SYNC_SECONDS = 30.0
TIMELINE_LIMIT = 50
# The hub's resolve and join at wait start share this many seconds.
HUB_SECONDS = 10.0
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
        self.log: Callable[[str], None] = lambda line: None

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

    def candidates(self, events: list[Any]) -> list[tuple[dict[str, Any], Wake]]:
        """Return the events that may wake this account, each with its verdict.

        A verdict of :attr:`Wake.THREAD` still needs the thread's agents.
        """
        out = []
        for e in since_join(events, self.account):
            if isinstance(e, dict):
                verdict = wakes(e, self.account, self.cfg)
                if verdict is not Wake.NO:
                    out.append((e, verdict))
        return out

    def budget(self) -> Budget:
        """Return a fresh lookup budget for one batch."""
        return Budget(self.client, self.cfg)

    def mail(self, room: str, events: list[Any], budget: Budget) -> list[Message]:
        """Return the messages among ``events`` of ``room`` that wake this account.

        Each thread with mail is looked up once, within ``budget``.

        Raises:
            AuthError: When a lookup's token is refused.
        """
        out = []
        for e, verdict in self.candidates(events):
            content = e["content"]
            root = thread_root(content)
            thread = None if root is None else budget.thread(room, root)
            if verdict is Wake.THREAD and thread and not thread.wakes(self.account):
                continue
            sender, body = str(e["sender"]), str(content["body"])
            out.append(Message(sender, body, str(e.get("event_id", "")), thread))
        return out

    def _hub_message(
        self, e: dict[str, Any], thread: Thread | None, project: str
    ) -> Message:
        content, sender = e["content"], str(e["sender"])
        field = hub_field(content) if sender in self.cfg.agents else None
        if field is not None:
            hub = HubMail(project, field.sender, field.to)
        else:
            parsed = project_address(content, self.cfg.server_name)
            hub = HubMail(project, None, parsed.projects if parsed else ())
        eid = str(e.get("event_id", ""))
        return Message(sender, str(content["body"]), eid, thread, hub)

    def _hub_targets(
        self, e: dict[str, Any], room: str, budget: Budget
    ) -> list[str] | None:
        """Return the projects hub ``e`` may wake for this account, in order.

        They are the projects its field or address names; for the user's
        unaddressed thread reply, this account's participant pairs and the
        root's address. None when that thread could not be read.
        """
        content, sender = e.get("content"), e.get("sender")
        if not isinstance(content, dict):
            return []
        if sender in self.cfg.agents:
            field = hub_field(content)
            return list(field.to) if field else []
        if sender != self.cfg.human:
            return []
        address = project_address(content, self.cfg.server_name)
        if address is not None:
            return list(address.projects)
        root = thread_root(content)
        if root is None:
            return []
        thread = budget.thread(room, root)
        if not thread.read or thread.root is None:
            return None
        mine = sorted(p for a, p in thread.pairs if a == self.account)
        address = root_address(thread.root, self.cfg)
        return mine + list(address.projects if address else ())

    def _unread(self, e: dict[str, Any]) -> None:
        root = thread_root(e["content"])
        self.log(
            f"hub: the thread {root} of the user's unaddressed reply "
            f"{e.get('event_id')} could not be read; it wakes nobody"
        )

    def hub_routes(
        self,
        room: str,
        events: list[Any],
        budget: Budget,
        projects: list[str] | None = None,
    ) -> list[tuple[str, Message]]:
        """Return each hub message among ``events`` with the project it wakes.

        A message is returned once for each session (this account, project)
        it wakes, among ``projects``, or among the projects it names when
        ``projects`` is None. The user's unaddressed reply asks its thread;
        when the thread cannot be read it wakes nobody and is logged once.
        Addressed mail is delivered even then.

        Raises:
            AuthError: When a lookup's token is refused.
        """
        me, out = self.account, []
        for e in since_join(events, me):
            if not isinstance(e, dict):
                continue
            targets = projects
            if targets is None:
                targets = self._hub_targets(e, room, budget)
            if targets is None:
                self._unread(e)
                continue
            for project in dict.fromkeys(targets):
                if project == self.cfg.hub_project:
                    continue
                verdict = hub_wakes(e, me, project, self.cfg)
                if verdict is Wake.NO:
                    continue
                content = e["content"]
                root = thread_root(content)
                thread = None if root is None else budget.thread(room, root)
                if verdict is Wake.THREAD:
                    if thread is None or not thread.read:
                        self._unread(e)
                        break
                    mentions = addressees(content, self.cfg.server_name)
                    if mentions and me not in mentions:
                        continue
                    if not thread.hub_selects(me, project, self.cfg):
                        continue
                out.append((project, self._hub_message(e, thread, project)))
        return out

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


def _write_text(path: Path, text: str) -> None:
    """Replace ``path`` with ``text`` atomically; a failure is ignored."""
    tmp = path.with_name(f".{path.name}.{os.getpid()}")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass


class Listener(SyncLoop):
    """Waits for mail to ``account`` in the room behind ``alias``, and in the hub.

    The hub is served for the session (``account``, ``project``) when the
    config names one; it never keeps project-room mail from being delivered.
    While a wait runs, ``<slug>.hub`` next to its lock says ``covered`` or
    ``unavailable: <reason>``.

    Args:
        client: The account's homeserver client.
        cfg: The host's configuration.
        account: The listening account's full ID.
        state: The account's state directory.
        alias: The project room's alias.
        project: The project this wait serves in the hub; None serves no hub.
        log: Takes one line per hub failure or unreadable hub thread.
    """

    def __init__(
        self,
        client: Client,
        cfg: Config,
        account: str,
        state: Path,
        alias: str,
        project: str | None = None,
        log: Callable[[str], None] = lambda line: None,
    ) -> None:
        super().__init__(client, cfg, account, state, alias_slug(alias))
        self.alias = alias
        self.rooms = Rooms(client, cfg, state)
        self.project = project
        self.log = log
        self.hub_file = state / f"{alias_slug(alias)}.hub"

    def _hub_down(self, why: str) -> None:
        self.log(
            f"the hub {self.cfg.hub_alias} is unavailable ({why}); this wait "
            f"serves {self.alias} only, the next wait tries again"
        )
        _write_text(self.hub_file, f"unavailable: {why}\n")

    def _hub(self, deadline: float) -> str | None:
        """Join the hub within :data:`HUB_SECONDS`; return its room, or None."""
        hub, project = self.cfg.hub_alias, self.project
        if hub is None or project is None:
            return None
        if not PROJECT_TOKEN.fullmatch(project):
            self._hub_down(f"the project name {project!r} cannot be addressed")
            return None
        until = min(deadline, self.client.now() + HUB_SECONDS)
        try:
            room = self.rooms.room_id(hub, until, verify=True)
        except AuthError:
            raise
        except AgentChatError as exc:
            self._hub_down(str(exc).splitlines()[0] if str(exc) else repr(exc))
            return None
        if room is None:
            self._hub_down("no such alias")
            return None
        _write_text(self.hub_file, "covered\n")
        return room

    def hub_mail(self, room: str, events: list[Any], budget: Budget) -> list[Message]:
        """Return the hub messages among ``events`` that wake this session.

        Raises:
            AuthError: When a lookup's token is refused.
        """
        project = str(self.project)
        return [m for _, m in self.hub_routes(room, events, budget, [project])]

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
        try:
            return self._serve(room, deadline, owner_alive, now)
        finally:
            self.hub_file.unlink(missing_ok=True)

    def _serve(
        self,
        room: str,
        deadline: float,
        owner_alive: Callable[[], bool],
        now: Callable[[], float],
    ) -> WaitResult:
        hub = self._hub(deadline)
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
            if hub is not None and self._left(hub, rooms):
                self.rooms.forget(str(self.cfg.hub_alias))
                self._hub_down("this account left it")
                hub = None
            budget = self.budget()
            mail = self.mail(room, timeline(rooms, room), budget)
            if hub is not None:
                mail += self.hub_mail(hub, timeline(rooms, hub), budget)
            if mail:
                return WaitResult("mail", mail)
        return WaitResult("owner-gone" if self.owner_gone else "timeout")
