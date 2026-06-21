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

Some providers (e.g. ``google-drive``) install under a path that contains
the account email, so the default root is a glob rather than a literal
path. For those providers, ``resolve_root`` expands the glob and hard-fails
with a message naming the env var when 0 or >1 directories match — the
caller is expected to set the env var explicitly to disambiguate.
"""

from __future__ import annotations

import glob
import os
from pathlib import Path


NEEDS_DISAMBIGUATION = "needs-disambiguation"


class ProviderResolutionError(RuntimeError):
    """Raised when a provider's root cannot be resolved unambiguously."""


class Provider:
    """A transport provider known to the publish skill."""

    def __init__(
        self,
        name: str,
        env_var: str,
        triggers: tuple[str, ...],
        default_root: Path | None = None,
        default_root_glob: str | None = None,
    ) -> None:
        if (default_root is None) == (default_root_glob is None):
            raise ValueError(
                "exactly one of default_root or default_root_glob must be set"
            )
        self.name = name
        self.env_var = env_var
        self.triggers = triggers
        self.default_root = default_root
        self.default_root_glob = default_root_glob


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

GOOGLE_DRIVE = Provider(
    name="google-drive",
    env_var="PUBLISH_GOOGLE_DRIVE_DIR",
    default_root_glob="~/Library/CloudStorage/GoogleDrive-*/My Drive/Reading",
    triggers=(
        "send to gdrive",
        "send to google drive",
        "read on gdrive",
        "read on drive",
        "положи в gdrive",
        "положи в гугл драйв",
        "отправь на драйв",
    ),
)

PROVIDERS: dict[str, Provider] = {
    ICLOUD.name: ICLOUD,
    GOOGLE_DRIVE.name: GOOGLE_DRIVE,
}


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

    For providers whose default root is a glob (e.g. ``google-drive``), the
    env var still wins verbatim when set. When unset, the glob is expanded
    against the filesystem; 0 or >1 matches raise
    ``ProviderResolutionError`` naming the env var as the disambiguator.
    """
    provider = PROVIDERS[provider_name]
    source = os.environ if env is None else env
    override = source.get(provider.env_var, "").strip()
    if override:
        return Path(override.rstrip("/")).expanduser()
    if provider.default_root is not None:
        return Path(str(provider.default_root).rstrip("/")).expanduser()
    return _resolve_from_glob(provider)


def _resolve_from_glob(provider: Provider) -> Path:
    pattern = os.path.expanduser(provider.default_root_glob or "")
    matches = sorted(glob.glob(pattern))
    if len(matches) == 1:
        return Path(matches[0].rstrip("/"))
    hint = (
        f"set {provider.env_var} to the absolute path of the "
        f"{provider.name} root"
    )
    if not matches:
        raise ProviderResolutionError(
            f"no directory matched {pattern!r} for provider "
            f"{provider.name!r}; {hint}."
        )
    raise ProviderResolutionError(
        f"{len(matches)} directories matched {pattern!r} for provider "
        f"{provider.name!r} (multi-account); {hint}. Matches: {matches}"
    )
