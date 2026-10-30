"""Prepared message files: how Codex sends without stdin.

Codex's prefix rules cannot match a command with a heredoc, stdin,
redirection or a substitution, so Codex sends in two steps:
``prepare-message NAME`` creates an empty private file and prints its path,
Codex fills it with ``apply_patch``, and ``send --message-file NAME`` posts it.
The outbox lies under ``/tmp``, which Codex's sandbox may write, and not under
the state directory, which it may not.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path

from .config import AgentChatError

ROOT_ENV = "AGENT_CHAT_TMP"
_NAME = re.compile(r"[A-Za-z0-9_.-]{1,64}")


def _private_dir(path: Path) -> Path:
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        pass
    st = os.lstat(path)
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise AgentChatError(f"{path} is not a private directory of this user")
    return path


def outbox() -> Path:
    """Return ``<AGENT_CHAT_TMP or /tmp/agent-chat-<uid>>/outbox``, both mode 0700."""
    root = os.environ.get(ROOT_ENV) or f"/tmp/agent-chat-{os.getuid()}"
    return _private_dir(_private_dir(Path(root)) / "outbox")


def _check(name: str) -> str:
    if not _NAME.fullmatch(name) or name[0] in ".-":
        raise AgentChatError(
            f"bad message file name {name!r} (letters, digits, _ . - only)", 2
        )
    return name


def prepare_message(name: str) -> Path:
    """Create the empty message file ``name`` (mode 0600) and return its real path.

    Raises:
        AgentChatError: When the name is bad or the file already exists.
    """
    path = outbox() / _check(name)
    try:
        os.close(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
    except FileExistsError as exc:
        raise AgentChatError(
            f"message file {name} exists; choose a fresh name", 2
        ) from exc
    return Path(os.path.realpath(path))


def read_message(name: str) -> tuple[Path, str]:
    """Return the prepared file ``name`` and its text; the caller removes it.

    Raises:
        AgentChatError: When the file is missing, or not a plain file of this user.
    """
    path = outbox() / _check(name)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError as exc:
        raise AgentChatError(
            f"no prepared message {name}; run prepare-message first", 2
        ) from exc
    except OSError as exc:  # a symlink (ELOOP) or another oddity
        raise AgentChatError(
            f"prepared message {name} is not a plain file of this user", 2
        ) from exc
    st = os.fstat(fd)
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
        os.close(fd)
        raise AgentChatError(
            f"prepared message {name} is not a plain file of this user", 2
        )
    with os.fdopen(fd, "rb") as f:
        return path, f.read().decode("utf-8")
