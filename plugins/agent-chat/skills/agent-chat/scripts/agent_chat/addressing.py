"""Who a room message is addressed to, and whether it wakes a listener."""

from __future__ import annotations

import re
from typing import Any

from .config import Config

# One mention at the start of the body: a full ID or @localpart, then ':' or
# whitespace (or the end of the body).
_MENTION = re.compile(
    r"@([A-Za-z0-9._=/+-]+)(?::([A-Za-z0-9.-]+(?::\d+)?))?(?=[:\s]|$)"
)
_GAP = re.compile(r":?\s*")


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


def wakes(event: dict[str, Any], me: str, cfg: Config) -> bool:
    """Tell whether ``event`` wakes the listener of account ``me``.

    A message wakes ``me`` when it addresses ``me``; a message from the human
    that addresses nobody wakes every listener; an agent's message that
    addresses nobody, an edit, and ``me``'s own messages wake nobody.
    """
    content = event.get("content")
    sender = event.get("sender")
    if event.get("type") != "m.room.message" or not isinstance(content, dict):
        return False
    if sender == me or is_edit(content) or not isinstance(content.get("body"), str):
        return False
    to = addressees(content, cfg.server_name)
    if to:
        return me in to
    return sender == cfg.human
