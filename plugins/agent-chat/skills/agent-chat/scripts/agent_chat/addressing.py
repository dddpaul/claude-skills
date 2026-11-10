"""Who a room message is addressed to, and whether it wakes a listener."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .config import PROJECT_TOKEN, Config

# One mention at the start of the body: a full ID or @localpart, then ':' or
# whitespace (or the end of the body).
_MENTION = re.compile(
    r"@([A-Za-z0-9._=/+-]+)(?::([A-Za-z0-9.-]+(?::\d+)?))?(?=[:\s]|$)"
)
_GAP = re.compile(r":?\s*")
# A hub address: comma-separated project tokens at the start, then ':'.
_ADDRESS = re.compile(r"[A-Za-z0-9._-]+(?:[ \t]*,[ \t]*[A-Za-z0-9._-]+)*:")
# The content field that names a hub message's sender project and addressees.
HUB_FIELD = "agent_chat.hub"


def leading_mentions(body: str, server_name: str) -> list[str]:
    """Return the full IDs in the run of mentions that opens ``body``.

    ``@claude-a @codex-a: hello`` yields both accounts; a run ends at the
    first word that is not a mention.
    """
    found: list[str] = []
    pos = 0
    while True:
        m = _MENTION.match(body, pos)
        if not m:
            return found
        local, server = m.group(1), m.group(2)
        if server is None:
            found.append(f"@{local}:{server_name}")
            end = m.end()
        elif server == server_name or "." in server:
            found.append(f"@{local}:{server}")
            end = m.end()
        else:
            # "@claude-a:hi" is @claude-a followed by ':' and text.
            found.append(f"@{local}:{server_name}")
            return found
        gap = _GAP.match(body, end)
        pos = gap.end() if gap else end
        if pos == end and pos < len(body):
            return found


def addressees(content: dict[str, Any], server_name: str) -> set[str]:
    """Return every account the message content addresses."""
    out: set[str] = set()
    mentions = content.get("m.mentions")
    if isinstance(mentions, dict) and isinstance(mentions.get("user_ids"), list):
        out.update(u for u in mentions["user_ids"] if isinstance(u, str))
    body = content.get("body")
    if isinstance(body, str):
        out.update(leading_mentions(body, server_name))
    return out


def is_edit(content: dict[str, Any]) -> bool:
    """Tell whether the content replaces an earlier message (``m.replace``)."""
    rel = content.get("m.relates_to")
    return isinstance(rel, dict) and rel.get("rel_type") == "m.replace"


def thread_root(content: dict[str, Any]) -> str | None:
    """Return the root ID of the thread the content was posted in, if any."""
    rel = content.get("m.relates_to")
    if not isinstance(rel, dict) or rel.get("rel_type") != "m.thread":
        return None
    root = rel.get("event_id")
    return root if isinstance(root, str) and root else None


class Wake(Enum):
    """Whether a message wakes a listener: no, yes, or as its thread decides."""

    NO = "no"
    YES = "yes"
    THREAD = "ask the thread"


def wakes(event: dict[str, Any], me: str, cfg: Config) -> Wake:
    """Tell whether ``event`` wakes the listener of account ``me``.

    A message wakes ``me`` when it addresses ``me``; a message from the human
    that addresses nobody wakes every listener, unless it was posted in a
    thread: then the thread's agents decide (:attr:`Wake.THREAD`). An agent's
    message that addresses nobody, an edit, and ``me``'s own messages wake
    nobody.
    """
    content = event.get("content")
    sender = event.get("sender")
    if event.get("type") != "m.room.message" or not isinstance(content, dict):
        return Wake.NO
    if sender == me or is_edit(content) or not isinstance(content.get("body"), str):
        return Wake.NO
    to = addressees(content, cfg.server_name)
    if to:
        return Wake.YES if me in to else Wake.NO
    if sender != cfg.human:
        return Wake.NO
    return Wake.THREAD if thread_root(content) else Wake.YES


@dataclass(frozen=True)
class HubField:
    """A valid ``agent_chat.hub`` field: the sender's project and the addressed."""

    sender: str
    to: tuple[str, ...]


@dataclass(frozen=True)
class HubAddress:
    """The projects a hub message names and the accounts that narrow them."""

    projects: tuple[str, ...]
    accounts: frozenset[str]

    def selects(self, me: str, project: str) -> bool:
        """Tell whether the address selects the session (``me``, ``project``)."""
        named = project in self.projects
        return named and (not self.accounts or me in self.accounts)


def _token(value: Any) -> bool:
    return isinstance(value, str) and PROJECT_TOKEN.fullmatch(value) is not None


def hub_field(content: dict[str, Any]) -> HubField | None:
    """Return the content's valid ``agent_chat.hub`` field, or None.

    Valid is ``{"v": 1, "from": <project>, "to": [<project>, ...]}`` with
    every project a token; ``to`` may be empty.
    """
    raw = content.get(HUB_FIELD)
    if not isinstance(raw, dict) or type(raw.get("v")) is not int or raw["v"] != 1:
        return None
    sender, to = raw.get("from"), raw.get("to")
    if not _token(sender) or not isinstance(to, list) or not all(map(_token, to)):
        return None
    return HubField(str(sender), tuple(to))


def _mentioned(content: dict[str, Any]) -> set[str]:
    mentions = content.get("m.mentions")
    if not isinstance(mentions, dict) or not isinstance(mentions.get("user_ids"), list):
        return set()
    return {u for u in mentions["user_ids"] if isinstance(u, str)}


def project_address(content: dict[str, Any], server_name: str) -> HubAddress | None:
    """Return the address that opens the user's hub message, or None.

    ``beta, gamma: @claude-a x`` names beta and gamma, narrowed to
    ``@claude-a``; accounts come from ``m.mentions`` and the ``@``-run right
    after the colon.
    """
    body = content.get("body")
    m = _ADDRESS.match(body) if isinstance(body, str) else None
    if m is None:
        return None
    projects = tuple(t.strip() for t in m.group(0)[:-1].split(","))
    rest = body[m.end() :].lstrip()
    accounts = _mentioned(content) | set(leading_mentions(rest, server_name))
    return HubAddress(projects, frozenset(accounts))


def agent_address(content: dict[str, Any], server_name: str) -> HubAddress:
    """Return what an agent's hub message addresses: its field's ``to``, narrowed.

    Accounts come from ``m.mentions`` and the ``@``-run after the visible
    prefix; a message without a valid field addresses nobody.
    """
    field = hub_field(content)
    if field is None:
        return HubAddress((), frozenset())
    accounts = _mentioned(content)
    body = content.get("body")
    to = ", ".join(field.to)
    prefix = f"{field.sender} → {to}: " if field.to else f"{field.sender}: "
    if isinstance(body, str) and body.startswith(prefix):
        accounts |= set(leading_mentions(body[len(prefix) :], server_name))
    return HubAddress(field.to, frozenset(accounts))


def root_address(root: dict[str, Any], cfg: Config) -> HubAddress | None:
    """Return a hub thread root's address: the user's text or an agent's field."""
    content = root.get("content")
    if not isinstance(content, dict):
        return None
    sender = root.get("sender")
    if sender == cfg.human:
        return project_address(content, cfg.server_name)
    if sender in cfg.agents:
        return agent_address(content, cfg.server_name)
    return None


def hub_wakes(event: dict[str, Any], me: str, project: str, cfg: Config) -> Wake:
    """Tell whether a hub ``event`` wakes the session (``me``, ``project``).

    An agent's message wakes the sessions its valid field addresses, never its
    own pair's; the user's message wakes the sessions its address selects.
    The user's unaddressed message wakes nobody at top level, and in a thread
    the thread decides (:attr:`Wake.THREAD`). Nothing else wakes anyone.
    """
    content = event.get("content")
    sender = event.get("sender")
    if event.get("type") != "m.room.message" or not isinstance(content, dict):
        return Wake.NO
    if is_edit(content) or not isinstance(content.get("body"), str):
        return Wake.NO
    if sender in cfg.agents:
        field = hub_field(content)
        if field is None or not field.to or (sender, field.sender) == (me, project):
            return Wake.NO
        selected = agent_address(content, cfg.server_name).selects(me, project)
        return Wake.YES if selected else Wake.NO
    if sender != cfg.human:
        return Wake.NO
    address = project_address(content, cfg.server_name)
    if address is not None:
        return Wake.YES if address.selects(me, project) else Wake.NO
    return Wake.THREAD if thread_root(content) else Wake.NO
