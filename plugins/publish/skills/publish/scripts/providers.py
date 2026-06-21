"""Trigger phrase → provider routing + provider root resolution.

The publish skill keeps its routing rules here so they are testable in
isolation. Trigger phrases are matched case-insensitively against the
canonical set of provider triggers. The resolver returns
``NEEDS_DISAMBIGUATION`` (rather than silently defaulting to ``icloud``) when
the phrase matches the umbrella skill but no specific provider — that
sentinel is the signal for the skill to ask the user.

Provider roots come from env vars (see ``PROVIDERS``); the legacy env var
used by the pre-v1 ``reading`` plugin is intentionally **not** consulted —
``resolve_root`` reads only the env var named on the matched provider.
"""

from __future__ import annotations

import os
from pathlib import Path

NEEDS_DISAMBIGUATION = "needs-disambiguation"


class Provider:
    """A transport provider known to the publish skill."""

    def __init__(
        self,
        name: str,
        env_var: str,
        default_root: Path,
        triggers: tuple[str, ...],
    ) -> None:
        self.name = name
        self.env_var = env_var
        self.default_root = default_root
        self.triggers = triggers


ICLOUD = Provider(
    name="icloud",
    env_var="PUBLISH_ICLOUD_DIR",
    default_root=Path(
        "~/Library/Mobile Documents/com~apple~CloudDocs/Reading"
    ).expanduser(),
    triggers=(
        "send to books",
        "read on ipad",
        "review on books",
        "send to icloud",
        "положи это в books",
        "положи это в книги",
        "почитаю на айпаде",
        "положи в icloud",
    ),
)

PROVIDERS: dict[str, Provider] = {ICLOUD.name: ICLOUD}


def resolve_provider(phrase: str) -> str:
    """Return the provider name for a trigger phrase.

    Matching is case-insensitive on the trimmed phrase. Returns
    ``NEEDS_DISAMBIGUATION`` when the phrase does not name a specific
    provider — the skill must then ask the user instead of defaulting.
    """
    needle = phrase.strip().lower()
    for provider in PROVIDERS.values():
        if needle in provider.triggers:
            return provider.name
    return NEEDS_DISAMBIGUATION


def resolve_root(provider_name: str, env: dict[str, str] | None = None) -> Path:
    """Return the absolute root directory for a provider.

    Reads the env var named in the provider definition; falls back to the
    provider's default root if it is unset or empty. Strips a trailing slash
    for consistency. ``env`` defaults to ``os.environ`` and exists so tests
    can inject an isolated mapping.
    """
    provider = PROVIDERS[provider_name]
    source = os.environ if env is None else env
    override = source.get(provider.env_var, "").strip()
    raw = override if override else str(provider.default_root)
    return Path(raw.rstrip("/")).expanduser()
