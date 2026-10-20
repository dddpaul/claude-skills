"""Constants, errors and identifiers shared by every zmx-peer-chat command."""

from __future__ import annotations

import hashlib
import os
import re

# Bumped on any incompatible change to the labels or the message format. Both
# sides refuse a peer or a message that carries another version.
PROTO = "1"

# The codex-cli version the daemon client was tested with (design/zmx-peer-chat.md).
TESTED_CODEX_CLI = "0.163.0"

LABEL_PAIR = "zpc.pair"
LABEL_ROLE = "zpc.role"
LABEL_INC = "zpc.inc"
LABEL_PROTO = "zpc.proto"
LABEL_THREAD = "zpc.thread"

ROLES = ("claude", "codex")
SENDER_NAMES = {"claude": "Claude", "codex": "Codex"}

# zmx label values may hold only these characters; session names are held to
# the same set so they can never smuggle a path or an option.
_TOKEN = re.compile(r"[A-Za-z0-9_.-]{1,64}")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


class ZpcError(Exception):
    """A refusal or failure reported to the caller with a fixed exit code."""

    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


def check_token(value: str, what: str) -> str:
    """Return ``value`` if it is a valid label value or session name.

    Args:
        value: The candidate string.
        what: What the value names, for the error message.

    Raises:
        ZpcError: With exit code 2 when the value is not a plain token.
    """
    if not _TOKEN.fullmatch(value) or value.startswith("-"):
        raise ZpcError(f"bad {what}: {value!r} (letters, digits, _ . - only)", 2)
    return value


def is_uuid(value: str) -> bool:
    """Tell whether ``value`` is a lowercase canonical UUID."""
    return bool(_UUID.fullmatch(value))


def pair_id(directory: str, explicit: str | None = None) -> str:
    """Return the pair id for a session directory.

    The id comes from the canonical full path, never the basename: ``/a/foo``
    and ``/b/foo`` must not pair. ``explicit`` lets several pairs share one
    directory.

    Args:
        directory: The session's working directory.
        explicit: A pair id given on the command line, if any.
    """
    if explicit is not None:
        return check_token(explicit, "pair id")
    canonical = os.path.realpath(directory)
    return "d" + hashlib.sha256(canonical.encode()).hexdigest()[:16]
