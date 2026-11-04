"""The agent-chat command line.

``send``, ``hook-wait`` and ``status`` serve Claude; ``prepare-message``,
``send --as codex --message-file`` and ``watch-codex`` serve Codex.
``send`` fails loudly: any failure is one line on stderr and a non-zero exit,
so the agent knows nothing was sent. ``hook-wait`` never fails: it exits 2
with mail on stderr, else 0.
"""

from __future__ import annotations

import argparse
import os
import re
import secrets
import signal
import sys
import threading
import time
import traceback
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from . import outbox, procs, watch
from .config import (
    AgentChatError,
    Config,
    config_dir,
    load_config,
    localpart,
    read_token,
    state_dir,
)
from .listen import SYNC_SECONDS, Listener
from .lock import WaitLock
from .matrix import SOCKET_SLACK, AuthError, Client, MatrixError
from .note import bare, render
from .room import Rooms, alias_slug, project_alias

# The wait ends a little before the hooks' 24 h timeout; the next hook starts another.
HOOK_WAIT_SECONDS = 86100
# How long a send keeps retrying a network failure.
SEND_SECONDS = 60.0
# Extra time to wait for an orphaned wait's lock beyond its last sync: the
# socket slack of that sync plus a few seconds.
LOCK_GRACE = SOCKET_SLACK + 5.0
LISTEN_ENV = "AGENT_CHAT_LISTEN"
# An event ID as an agent passes it: one optional leading "$", then this.
EVENT_ID = re.compile(r"\$?([A-Za-z0-9_-]+)")


def log(state: Path, line: str) -> None:
    """Append one timestamped line to the account's log; a failure is ignored."""
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        with open(state / "log", "a", encoding="utf-8") as f:
            f.write(f"{stamp} pid={os.getpid()} {line}\n")
    except OSError:
        pass


def log_auth_once(state: Path, account: str, exc: AuthError) -> None:
    """Log a 401 once per token file version, not on every hook."""
    marker = state / "auth-failed"
    try:
        token = config_dir() / f"{localpart(account)}.token"
        version = str(token.stat().st_mtime_ns)
    except (OSError, AgentChatError):
        version = "missing"
    try:
        if marker.read_text(encoding="utf-8") == version:
            return
    except OSError:
        pass
    log(state, f"hook-wait: {account} was refused ({exc}); listening stops")
    try:
        marker.write_text(version, encoding="utf-8")
    except OSError:
        pass


def _setup(tool: str) -> tuple[Config, str, Client]:
    cfg = load_config()
    account = cfg.account(tool)
    return cfg, account, Client(cfg.homeserver, read_token(account))


def message_content(body: str, to: list[str], server_name: str) -> dict[str, Any]:
    """Build the ``m.room.message`` content: the mention prefix and ``m.mentions``.

    The prefix names an account on ``server_name`` as ``@localpart`` and any
    other account by its full ID; ``m.mentions`` always holds the full IDs.
    """
    short = [u.removesuffix(f":{server_name}") for u in to]
    prefix = " ".join(short) + ": " if to else ""
    return {"msgtype": "m.text", "body": prefix + body, "m.mentions": {"user_ids": to}}


def thread_id(value: str) -> str:
    """Return ``value`` as a full event ID; refuse a malformed one with exit 2."""
    m = EVENT_ID.fullmatch(value)
    if m is None:
        raise AgentChatError(
            f"--thread {value!r} is not an event ID (letters, digits, _ and -, "
            "with or without one leading $); nothing was sent",
            2,
        )
    return "$" + m.group(1)


def _relation(event: dict[str, Any] | None, event_id: str) -> dict[str, Any]:
    """Return the ``m.relates_to`` of a message that may be in a thread.

    Refuses an unknown event, a non-message, a redacted or empty one, and any
    relation but none, a rich reply (``m.in_reply_to`` only) or ``m.thread``.
    """
    what = f"--thread {bare(event_id)}"
    if event is None:
        raise AgentChatError(f"{what}: no such event in the room; nothing was sent")
    content = event.get("content")
    unsigned = event.get("unsigned")
    redacted = isinstance(unsigned, dict) and "redacted_because" in unsigned
    if event.get("type") != "m.room.message":
        raise AgentChatError(f"{what}: not a message; nothing was sent")
    if redacted or not isinstance(content, dict) or not content:
        raise AgentChatError(f"{what}: redacted or empty; nothing was sent")
    rel = content.get("m.relates_to")
    if rel is None:
        return {}
    kind = rel.get("rel_type") if isinstance(rel, dict) else "malformed"
    if kind is None or kind == "m.thread":
        return rel
    raise AgentChatError(f"{what}: a relation ({kind}); nothing was sent")


def thread_root(client: Client, room: str, event_id: str, deadline: float) -> str:
    """Return the root of the thread ``event_id`` starts or belongs to.

    The homeserver does not check thread roots, so this does: a thread child
    leads to its root, which must itself be a message outside any thread.
    """
    rel = _relation(client.event(room, event_id, deadline), event_id)
    if rel.get("rel_type") != "m.thread":
        return event_id
    root = rel.get("event_id")
    if not isinstance(root, str) or EVENT_ID.fullmatch(root) is None:
        raise AgentChatError(
            f"--thread {bare(event_id)}: its thread root is malformed; nothing was sent"
        )
    if _relation(client.event(room, root, deadline), root).get("rel_type"):
        raise AgentChatError(
            f"--thread {bare(event_id)}: its root {bare(root)} is not a top-level "
            "message; nothing was sent"
        )
    return root


def thread_relation(
    client: Client, room: str, event_id: str, deadline: float
) -> dict[str, Any]:
    """Return the ``m.relates_to`` that posts into ``event_id``'s thread.

    ``m.in_reply_to`` names the thread's latest message, or the root while the
    thread has no replies: the fallback for clients without threads.
    """
    root = thread_root(client, room, event_id, deadline)
    latest = client.thread_latest(room, root, deadline) or root
    return {
        "rel_type": "m.thread",
        "event_id": root,
        "is_falling_back": True,
        "m.in_reply_to": {"event_id": latest},
    }


def cmd_send(a: argparse.Namespace) -> int:
    """Post stdin, or a prepared message file, into the project's room.

    A prepared file is removed once the homeserver has confirmed the post;
    after a failure it stays, so the same send can run again.
    """
    if a.message_file is None:
        prepared, body = None, sys.stdin.read()
        empty = "the message on stdin is empty; nothing was sent"
    else:
        prepared, body = outbox.read_message(a.message_file)
        empty = f"the prepared message {a.message_file} is empty; nothing was sent"
    if not body.strip():
        raise AgentChatError(empty, 2)
    thread = None if a.thread is None else thread_id(a.thread)
    cfg, account, client = _setup(a.as_)
    to = list(dict.fromkeys(cfg.user_id(t) for t in a.to or []))
    content = message_content(body.rstrip("\n"), to, cfg.server_name)
    deadline = time.monotonic() + SEND_SECONDS
    alias = project_alias(cfg)
    rooms = Rooms(client, cfg, state_dir(account))
    txn = f"{time.time_ns()}-{secrets.token_hex(6)}"
    for attempt in (1, 2):
        room = rooms.room_id(alias, deadline, refresh=attempt == 2)
        if room is None:
            raise AgentChatError(
                f"this project has no room {alias} (not onboarded); nothing was sent"
            )
        try:
            if thread is not None:
                rel = thread_relation(client, room, thread, deadline)
                content["m.relates_to"] = rel
            event = client.send_message(room, txn, content, deadline)
            break
        except AuthError:
            raise
        except MatrixError as exc:
            if attempt == 2 or exc.status not in (403, 404):
                raise
            rooms.forget(alias)  # the cached room was rejected: resolve once more
    if prepared is not None:
        prepared.unlink(missing_ok=True)
    where = "" if thread is None else f" in thread {bare(rel['event_id'])}"
    print(f"sent to {alias} as {account}{where}: {bare(event)}")
    return 0


def cmd_prepare_message(a: argparse.Namespace) -> int:
    """Create an empty private message file and print its absolute path."""
    print(outbox.prepare_message(a.name))
    return 0


def cmd_watch_codex(a: argparse.Namespace) -> int:
    """Deliver mail for the Codex account with ``codex queue`` until stopped."""
    thread = None if a.thread is None else watch.check_thread(a.thread)
    cfg, account, client = _setup("codex")
    state = state_dir(account)
    alias = None if thread is None else project_alias(cfg)

    def say(line: str) -> None:
        log(state, f"watch-codex: {line}")
        print(f"agent-chat watch-codex: {line}", file=sys.stderr, flush=True)

    w = watch.CodexWatcher(client, cfg, account, state, say, thread, alias)
    try:
        return _serve(w, state)
    except AuthError as exc:
        say(f"{account} was refused ({exc}); stopping")
        return 1
    except Exception as exc:  # noqa: BLE001 - logged here, reported by main()
        why = exc if isinstance(exc, AgentChatError) else repr(exc)
        log(state, f"watch-codex: {why}")
        raise


def _serve(w: watch.CodexWatcher, state: Path) -> int:
    """Run ``w`` under its lock, with SIGTERM and SIGINT handled, until it stops."""
    lock = WaitLock(state, w.lock_name)
    if not lock.try_acquire():
        raise AgentChatError(f"another watch-codex already runs ({lock.path})")
    previous = {}
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGTERM, signal.SIGINT):
            previous[sig] = signal.signal(sig, w.on_signal)
    try:
        lock.record(os.getpid())
        return w.run()
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        lock.release()


def cmd_hook_wait(a: argparse.Namespace) -> int:
    """The hooks' wait: exit 2 with mail on stderr, else 0. Never raises."""
    sys.stdin.read()  # the hook's JSON input; nothing in it is needed
    if os.environ.get(LISTEN_ENV) != "1":
        return 0
    try:
        cfg, account, client = _setup(a.as_)
        state = state_dir(account)
    except Exception:  # noqa: BLE001 - an unconfigured host has nothing to listen to
        return 0
    try:
        return _hook_wait(cfg, account, client, state, a.seconds)
    except AuthError as exc:
        log_auth_once(state, account, exc)
    except AgentChatError as exc:
        log(state, f"hook-wait: {exc}")
    except Exception:  # noqa: BLE001 - the hook must never crash
        log(state, "hook-wait crashed: " + traceback.format_exc().replace("\n", " | "))
    return 0


def _hook_wait(
    cfg: Config, account: str, client: Client, state: Path, seconds: float
) -> int:
    table = procs.system_table()
    owner = procs.claude_ancestor(table)
    if owner is None:
        return 0
    deadline = time.monotonic() + seconds
    alias = project_alias(cfg)
    lock = WaitLock(state, alias_slug(alias))
    if not lock.try_acquire():
        holder = lock.holder()
        if holder is None or procs.alive(table, holder):
            return 0  # a wait for a living Claude already listens
        # The holder's Claude is gone; it notices after its current sync.
        if not lock.acquire_within(SYNC_SECONDS + LOCK_GRACE):
            return 0

    def owner_alive() -> bool:
        return procs.alive(table, owner)

    client.keep_going = owner_alive
    try:
        lock.record(owner)
        result = Listener(client, cfg, account, state, alias).wait(
            deadline, owner_alive
        )
    finally:
        lock.release()
    if result.outcome != "mail":
        return 0
    print(render(result.messages, cfg, account, alias), file=sys.stderr)
    return 2


def cmd_status(a: argparse.Namespace) -> int:
    """Print the account, the project room and whether a wait listens."""
    cfg, account, client = _setup(a.as_)
    state = state_dir(account)
    alias = project_alias(cfg)
    room = Rooms(client, cfg, state).room_id(alias, time.monotonic() + SEND_SECONDS)
    print(f"account: {account} ({a.as_})")
    print(f"homeserver: {cfg.homeserver}")
    print(f"room: {alias} -> {room or 'not onboarded (no such alias)'}")
    print(f"{LISTEN_ENV}: {os.environ.get(LISTEN_ENV, 'unset')}")
    waiting = WaitLock(state, alias_slug(alias)).held()
    print(f"waiting: {'yes' if waiting else 'no'}")
    if a.as_ == "codex":
        locks = ("watch-codex", f"watch-codex-{alias_slug(alias)}")
        watching = any(WaitLock(state, name).held() for name in locks)
        print(f"watch-codex: {'running' if watching else 'not running'}")
    print(f"state: {state}")
    return 0


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent-chat", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("send", help="post stdin into the project's room")
    s.add_argument("--to", action="append", help="an account to address (repeatable)")
    s.add_argument(
        "--message-file",
        metavar="NAME",
        help="post the file prepare-message NAME created instead of stdin",
    )
    s.add_argument(
        "--thread",
        metavar="ID",
        help="post into the thread of this event (its ID with or without the $)",
    )
    s.set_defaults(func=cmd_send)

    m = sub.add_parser("prepare-message", help="create an empty private message file")
    m.add_argument("name", help="a fresh name: letters, digits, _ . -")
    m.set_defaults(func=cmd_prepare_message)

    w = sub.add_parser(
        "watch-codex", help="queue mail for the Codex account to a Codex thread"
    )
    w.add_argument(
        "--thread",
        help="queue to this thread, for the working directory's room only",
    )
    w.set_defaults(func=cmd_watch_codex)

    h = sub.add_parser("hook-wait", help="the plugin hooks' wait (asyncRewake)")
    h.add_argument("--seconds", type=float, default=HOOK_WAIT_SECONDS)
    h.set_defaults(func=cmd_hook_wait)

    t = sub.add_parser("status", help="show the account, the room and the wait")
    t.set_defaults(func=cmd_status)

    for c in (s, h, t):
        c.add_argument(
            "--as", dest="as_", default="claude", choices=("claude", "codex")
        )
    return p


def main(argv: Sequence[str] | None = None) -> int:
    """Run one agent-chat command; return its exit code."""
    a = _parser().parse_args(argv)
    try:
        return a.func(a)
    except AgentChatError as exc:
        print(f"agent-chat: {exc}".splitlines()[0], file=sys.stderr)
        return exc.code
    except Exception as exc:  # noqa: BLE001 - one line, not a traceback
        print(
            f"agent-chat: {type(exc).__name__}: {exc}".splitlines()[0], file=sys.stderr
        )
        return 1
