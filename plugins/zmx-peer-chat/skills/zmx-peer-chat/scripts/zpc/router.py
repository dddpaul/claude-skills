"""Route one message to the peer: ``codex queue`` for Codex, the mailbox for Claude."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

from .common import (
    LABEL_INC,
    LABEL_PAIR,
    LABEL_PROTO,
    LABEL_ROLE,
    LABEL_THREAD,
    PROTO,
    ROLES,
    SENDER_NAMES,
    ZpcError,
    is_uuid,
)
from .mailbox import Mailbox
from .register import thread_name
from .zmx import Session, Zmx

_REQUIRED = (LABEL_PAIR, LABEL_ROLE, LABEL_INC, LABEL_PROTO)
# How many non-empty lines at the end of the Codex screen may hold its footer.
_FOOTER_LINES = 6

CodexQueue = Callable[[str, str], None]


def own_session(explicit: str | None) -> str:
    """Return this side's zmx session name: ``--session`` or ``$ZMX_SESSION``."""
    name = explicit or os.environ.get("ZMX_SESSION", "")
    if not name:
        raise ZpcError("not inside a zmx session (ZMX_SESSION is unset)", 2)
    return name


def find_me(sessions: dict[str, Session], explicit: str | None) -> Session:
    """Return this side's registered session.

    Codex runs commands in its app-server daemon, so their ``ZMX_SESSION`` is
    the daemon's, not the TUI's. A command run by Codex carries
    ``CODEX_THREAD_ID`` instead: its session is the one whose ``zpc.thread``
    label holds that id, and ``ZMX_SESSION`` is never consulted then.
    """
    if explicit:
        return registered(sessions, explicit)
    thread = os.environ.get("CODEX_THREAD_ID", "")
    if not thread:
        return registered(sessions, own_session(None))
    if not is_uuid(thread):
        raise ZpcError(f"CODEX_THREAD_ID is not a thread id: {thread!r}", 2)
    bound = sorted(
        s.name
        for s in sessions.values()
        if s.labels.get(LABEL_ROLE) == "codex" and s.labels.get(LABEL_THREAD) == thread
    )
    if not bound:
        raise ZpcError(
            f"no zmx session is bound to this Codex thread ({thread}); the "
            "launcher bound another one (moved by /new or /resume?)"
        )
    if len(bound) > 1:
        raise ZpcError(
            f"several zmx sessions are bound to thread {thread}: "
            f"{', '.join(bound)}; refusing to pick one"
        )
    return registered(sessions, bound[0])


def registered(sessions: dict[str, Session], name: str) -> Session:
    """Return session ``name`` if it carries every pairing label this side speaks."""
    me = sessions.get(name)
    if me is None:
        raise ZpcError(f"zmx session {name} is not running")
    if any(k not in me.labels for k in _REQUIRED) or me.labels[LABEL_ROLE] not in ROLES:
        raise ZpcError(f"zmx session {name} is not registered with zmx-peer-chat")
    if me.labels[LABEL_PROTO] != PROTO:
        raise ZpcError(
            f"zmx session {name} speaks protocol {me.labels[LABEL_PROTO]!r}, "
            f"this plugin {PROTO!r}"
        )
    return me


def find_peer(sessions: dict[str, Session], me: Session, role: str) -> Session:
    """Return the one session of ``role`` that shares ``me``'s pair id.

    Raises:
        ZpcError: When there is none, more than one, or it speaks another
            protocol version. Nothing is sent then.
    """
    pair = me.labels[LABEL_PAIR]
    found = [
        s
        for s in sessions.values()
        if s.name != me.name
        and s.labels.get(LABEL_PAIR) == pair
        and s.labels.get(LABEL_ROLE) == role
    ]
    if not found:
        raise ZpcError(f"no {role} session is paired with {me.name}; nothing was sent")
    if len(found) > 1:
        names = ", ".join(sorted(s.name for s in found))
        raise ZpcError(
            f"several {role} sessions share pair {pair} ({names}); "
            "refusing to pick one, nothing was sent"
        )
    peer = found[0]
    if peer.labels.get(LABEL_PROTO) != PROTO:
        raise ZpcError(
            f"{peer.name} speaks protocol {peer.labels.get(LABEL_PROTO)!r}, "
            f"this side {PROTO!r}; nothing was sent"
        )
    return peer


def clean_text(raw: str, label: str) -> str:
    """Trim ``raw`` and drop a ``Chat from X:`` label the sender wrote itself."""
    text = raw.strip()
    while text.startswith(label.rstrip()):
        text = text[len(label.rstrip()) :].strip()
    if not text:
        raise ZpcError("the message is empty; nothing was sent", 2)
    return text


def tui_shows(screen: str, name: str) -> bool:
    """Tell whether the Codex footer at the end of ``screen`` names thread ``name``."""
    lines = [line.rstrip() for line in screen.splitlines() if line.strip()]
    return any(line.endswith(f"· {name}") for line in lines[-_FOOTER_LINES:])


def run_codex_queue(thread: str, message: str) -> None:
    """Queue ``message`` as the next turn of Codex thread ``thread``."""
    codex = os.environ.get("ZPC_CODEX", "codex").split()
    try:
        done = subprocess.run(
            [*codex, "queue", "--thread", thread, "--message", message],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ZpcError(f"codex queue failed: {exc}") from exc
    if done.returncode != 0:
        why = done.stderr.strip() or f"exit {done.returncode}"
        raise ZpcError(f"codex queue failed: {why}")


def send(
    to: str,
    raw: str,
    session: str | None,
    zmx: Zmx,
    root: Path,
    codex_queue: CodexQueue = run_codex_queue,
) -> str:
    """Send ``raw`` from this session to its ``to`` peer; return queued or delivered."""
    sessions = zmx.sessions()
    me = find_me(sessions, session)
    mine = me.labels[LABEL_ROLE]
    if to == mine or to not in ROLES:
        raise ZpcError(f"cannot send to {to!r} from the {mine} side", 2)
    label = f"Chat from {SENDER_NAMES[mine]}: "
    text = clean_text(raw, label)
    peer = find_peer(sessions, me, to)
    if to == "claude":
        box = Mailbox(root, me.labels[LABEL_PAIR])
        box.deliver(label + text, mine, peer.labels[LABEL_INC])
        return "delivered" if box.waiting() else "queued"
    thread = peer.labels.get(LABEL_THREAD, "")
    if not is_uuid(thread):
        raise ZpcError(f"{peer.name} has no bound Codex thread; nothing was sent")
    name = thread_name(peer.labels[LABEL_INC])
    if not tui_shows(zmx.history(peer.name), name):
        raise ZpcError(
            f"the Codex TUI in {peer.name} does not show thread {name} (moved by "
            "/new or /resume, or a dialog covers the footer); nothing was queued"
        )
    codex_queue(thread, label + text)
    return "queued"
