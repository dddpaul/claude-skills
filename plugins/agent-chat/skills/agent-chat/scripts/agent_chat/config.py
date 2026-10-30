"""The host's configuration, account tokens and the per-account state directory.

Provisioning writes ``~/.config/agent-chat/config.toml`` and one
``<localpart>.token`` per account; the plugin only reads them. A missing file
means the host is not configured.
"""

from __future__ import annotations

import os
import re
import stat
import tomllib
from dataclasses import dataclass
from pathlib import Path

# A Matrix localpart as it may appear in a file name: no slash, no leading dot.
_LOCALPART = re.compile(r"[a-z0-9_=.-]{1,255}")
_USER_ID = re.compile(r"@([^:\s]+):(\S+)")


class AgentChatError(Exception):
    """A failure reported to the caller as one line with a fixed exit code."""

    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


class NotConfigured(AgentChatError):
    """The host has no config or no token for the account."""


@dataclass(frozen=True)
class Config:
    """The parsed ``config.toml``."""

    homeserver: str
    server_name: str
    room_prefix: str
    human: str
    agents: tuple[str, ...]
    accounts: dict[str, str]

    def account(self, tool: str) -> str:
        """Return this host's account for ``tool`` (``claude`` or ``codex``)."""
        try:
            return self.accounts[tool]
        except KeyError as exc:
            raise NotConfigured(f"config has no account for {tool}") from exc

    def known(self) -> tuple[str, ...]:
        """Every account a message may be addressed to: the human, then agents."""
        return (self.human, *self.agents)

    def user_id(self, name: str) -> str:
        """Return the full ID for ``@localpart``, ``localpart`` or a full ID.

        Raises:
            AgentChatError: When the name is not a known account.
        """
        full = name if ":" in name else f"@{name.lstrip('@')}:{self.server_name}"
        if not full.startswith("@"):
            full = "@" + full
        if full not in self.known():
            raise AgentChatError(f"{name} is not an account in config.toml", 2)
        return full


def config_dir() -> Path:
    """Return ``${XDG_CONFIG_HOME:-~/.config}/agent-chat``."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / "agent-chat"


def load_config(path: Path | None = None) -> Config:
    """Read and check ``config.toml``.

    Raises:
        NotConfigured: When the file is missing.
        AgentChatError: When it does not parse or lacks a key.
    """
    path = path or config_dir() / "config.toml"
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NotConfigured(f"this host is not configured ({path} is missing)") from exc
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise AgentChatError(f"cannot read {path}: {exc}") from exc
    try:
        cfg = Config(
            homeserver=str(raw["homeserver"]).rstrip("/"),
            server_name=str(raw["server_name"]),
            room_prefix=str(raw["room_prefix"]),
            human=str(raw["human"]),
            agents=tuple(str(a) for a in raw["agents"]),
            accounts={str(k): str(v) for k, v in raw["accounts"].items()},
        )
    except (KeyError, TypeError, AttributeError) as exc:
        raise AgentChatError(f"{path} lacks or mistypes {exc}") from exc
    return cfg


def localpart(user_id: str) -> str:
    """Return the localpart of ``@localpart:server``, safe to use in a file name."""
    m = _USER_ID.fullmatch(user_id)
    if not m or not _LOCALPART.fullmatch(m.group(1)) or m.group(1).startswith("."):
        raise AgentChatError(f"bad account id {user_id!r}", 2)
    return m.group(1)


def read_token(user_id: str) -> str:
    """Read the account's access token from ``<localpart>.token``.

    Raises:
        NotConfigured: When the token file is missing or empty.
    """
    path = config_dir() / f"{localpart(user_id)}.token"
    try:
        token = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise NotConfigured(f"no token file for {user_id} ({path})") from exc
    except OSError as exc:
        raise AgentChatError(f"cannot read {path}: {exc}") from exc
    if not token:
        raise NotConfigured(f"the token file {path} is empty")
    return token


def state_dir(user_id: str) -> Path:
    """Return the account's state directory, mode 0700.

    That is ``${XDG_STATE_HOME:-~/.local/state}/agent-chat/<localpart>``.
    """
    base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    path = Path(base) / "agent-chat" / localpart(user_id)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    st = os.lstat(path)
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid():
        raise AgentChatError(f"{path} is not a directory of this user")
    if st.st_mode & 0o077:
        os.chmod(path, 0o700)
    return path
