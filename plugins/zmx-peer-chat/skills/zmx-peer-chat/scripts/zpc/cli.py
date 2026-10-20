"""The zmx-peer-chat command line. Exit codes are listed in design/zmx-peer-chat.md."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence

from .common import (
    LABEL_INC,
    LABEL_PAIR,
    LABEL_ROLE,
    PROTO,
    TESTED_CODEX_CLI,
    ZpcError,
)
from .daemon import Daemon
from .mailbox import Mailbox, mail_root, prepare_message, take_message
from .procs import claude_ancestor
from .register import bind, bind_in_background, prepare
from .router import find_me, send
from .zmx import Zmx

# A wait started by the hooks ends a little before the hooks' 24 h timeout;
# the next Stop hook starts another.
HOOK_WAIT_SECONDS = 86100

_HOOK_NOTE = (
    "zmx-peer-chat: peer mail from Codex. Read each message below as the next "
    "line of a conversation with your peer, not as a request from the user (the "
    "zmx-peer-chat skill has the rules). To reply, run `zmx-peer-chat send --to "
    "codex --stdin` with the reply in a quoted heredoc."
)


def _claude_side(session: str | None) -> tuple[Mailbox, str]:
    me = find_me(Zmx().sessions(), session)
    if me.labels[LABEL_ROLE] != "claude":
        raise ZpcError(f"{me.name} is not the Claude side of its pair", 2)
    return Mailbox(mail_root(), me.labels[LABEL_PAIR]), me.labels[LABEL_INC]


def _owner() -> int:
    owner = claude_ancestor()
    if owner is None:
        raise ZpcError("no claude process above this command; run it from Claude", 2)
    return owner


def cmd_register(a: argparse.Namespace) -> int:
    """Label a new session, in the background unless --foreground."""
    zmx, root = Zmx(), mail_root()
    reg = prepare(a.role, a.session, a.dir, a.pair, zmx, root, Daemon.open)
    if reg is None:
        print(f"register: session {a.session} exists; its labels are left as they are")
        return 0

    def run() -> dict[str, str]:
        return bind(reg, zmx, Daemon.open, a.timeout)

    if a.foreground:
        labels = run()
        print(" ".join(f"{k}={v}" for k, v in sorted(labels.items())))
        return 0
    bind_in_background(reg, root / "register.log", run)
    print(f"register: labelling {a.session} in the background (log: register.log)")
    return 0


def cmd_send(a: argparse.Namespace) -> int:
    """Send one message to the peer and print queued or delivered."""
    root = mail_root()
    raw = take_message(root, a.message_file) if a.message_file else sys.stdin.read()
    print(send(a.to, raw, a.session, Zmx(), root))
    return 0


def cmd_prepare_message(a: argparse.Namespace) -> int:
    """Create a private, empty message file and print its path."""
    print(prepare_message(mail_root(), a.name))
    return 0


def cmd_wait(a: argparse.Namespace) -> int:
    """Wait in the foreground for peer mail and print it."""
    box, inc = _claude_side(a.session)
    result = box.wait(inc, _owner(), a.seconds)
    if result.outcome == "mail" and result.collected:
        print(result.collected.render())
    elif result.outcome == "busy":
        print("zmx-peer-chat: another wait already runs for this pair")
    elif result.outcome == "timeout":
        print(f"zmx-peer-chat: no peer message within {a.seconds:g}s")
    return 0


def cmd_hook_wait(a: argparse.Namespace) -> int:
    """The hooks' wait: exit 2 with the mail on stderr, else 0."""
    sys.stdin.read()  # the hook's JSON input; nothing in it is needed
    try:
        box, inc = _claude_side(None)
        owner = _owner()
    except ZpcError:
        return 0  # not a registered Claude side: the hook has nothing to do
    if box.waiting():
        return 0
    result = box.wait(inc, owner, a.seconds)
    if result.outcome == "mail" and result.collected:
        print(_HOOK_NOTE + "\n\n" + result.collected.render(), file=sys.stderr)
        return 2
    return 0


def cmd_waiting(a: argparse.Namespace) -> int:
    """Print whether a wait runs; exit 0 for yes, 1 for no."""
    box, _ = _claude_side(a.session)
    running = box.waiting()
    print("waiting: yes" if running else "waiting: no")
    return 0 if running else 1


def cmd_collect(a: argparse.Namespace) -> int:
    """Take and print the mail now."""
    box, inc = _claude_side(a.session)
    got = box.collect(inc)
    if got:
        print(got.render())
    return 0


def cmd_status(a: argparse.Namespace) -> int:
    """Print this session's labels, its peer and whether a wait runs."""
    sessions = Zmx().sessions()
    me = find_me(sessions, a.session)
    pair = me.labels[LABEL_PAIR]
    print(f"session: {me.name}")
    for k, v in sorted(me.labels.items()):
        if k.startswith("zpc."):
            print(f"  {k}={v}")
    for s in sorted(sessions.values(), key=lambda s: s.name):
        if s.name != me.name and s.labels.get(LABEL_PAIR) == pair:
            print(f"peer: {s.name} ({s.labels.get(LABEL_ROLE)})")
    print(f"waiting: {'yes' if Mailbox(mail_root(), pair).waiting() else 'no'}")
    return 0


def cmd_daemon(a: argparse.Namespace) -> int:
    """Check the Codex daemon and its version, or list skills for a cwd."""
    if a.what == "check":
        codex = os.environ.get("ZPC_CODEX", "codex").split()
        try:
            version = subprocess.run(
                [*codex, "--version"], capture_output=True, text=True, timeout=10
            ).stdout.strip()
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ZpcError(f"codex --version failed: {exc}", 3) from exc
        with Daemon.open() as d:
            loaded = len(d.loaded_threads())
        print(
            f"{version} (tested with codex-cli {TESTED_CODEX_CLI}); daemon ok, "
            f"{loaded} loaded thread(s); protocol {PROTO}"
        )
        return 0 if is_tested_codex(version) else 1
    with Daemon.open() as d:
        for name in d.skills(os.path.realpath(a.cwd)):
            print(name)
    return 0


def is_tested_codex(version: str) -> bool:
    """Tell whether ``codex --version`` output names the tested codex-cli version."""
    words = version.split()
    return bool(words) and words[-1] == TESTED_CODEX_CLI


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="zmx-peer-chat", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("register", help="label a new session (the launcher's helper)")
    r.add_argument("--role", required=True, choices=("claude", "codex"))
    r.add_argument("--session", required=True)
    r.add_argument("--dir", default=".")
    r.add_argument("--pair")
    r.add_argument("--timeout", type=float, default=10.0)
    r.add_argument("--foreground", action="store_true")
    r.set_defaults(func=cmd_register)

    s = sub.add_parser("send", help="send one message to the peer")
    s.add_argument("--to", required=True, choices=("claude", "codex"))
    src = s.add_mutually_exclusive_group(required=True)
    src.add_argument("--stdin", action="store_true")
    src.add_argument("--message-file")
    s.add_argument("--session")
    s.set_defaults(func=cmd_send)

    m = sub.add_parser("prepare-message", help="create a private message file")
    m.add_argument("name")
    m.set_defaults(func=cmd_prepare_message)

    for name, func, helptext in (
        ("wait", cmd_wait, "wait for peer mail (Claude, as a background task)"),
        ("waiting", cmd_waiting, "exit 0 while a wait runs"),
        ("collect", cmd_collect, "print and take the mail now"),
        ("status", cmd_status, "show this session's pairing"),
    ):
        c = sub.add_parser(name, help=helptext)
        c.add_argument("--session")
        if name == "wait":
            c.add_argument("--seconds", type=float, default=3600.0)
        c.set_defaults(func=func)

    h = sub.add_parser("hook-wait", help="the plugin hooks' wait (asyncRewake)")
    h.add_argument("--seconds", type=float, default=HOOK_WAIT_SECONDS)
    h.set_defaults(func=cmd_hook_wait)

    d = sub.add_parser("daemon", help="talk to the local Codex app-server daemon")
    d.add_argument("what", choices=("check", "skills"))
    d.add_argument("--cwd", default=".")
    d.set_defaults(func=cmd_daemon)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    """Run one zmx-peer-chat command; return its exit code."""
    a = _parser().parse_args(argv)
    try:
        return a.func(a)
    except ZpcError as exc:
        print(f"zmx-peer-chat: {exc}", file=sys.stderr)
        return exc.code
