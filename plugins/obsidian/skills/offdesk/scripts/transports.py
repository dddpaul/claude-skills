"""Trigger phrase → transport routing + transport root resolution.

The offdesk skill copies markdown into an Obsidian vault that some
sync mechanism carries to a phone or tablet. Which mechanism that is —
Syncthing over P2P, or iCloud Drive — is the *transport*. Both
transports use the identical layout
``<vault-root>/<project-slug>/<filename>.md``; only the root differs.

Routing rules live here, not in prose, so they can be regression-tested.
The module mirrors the shape of the publish skill's
``scripts/providers.py``: one env var per transport, a literal-or-glob
default root, and a glob contract that hard-fails rather than guessing.

Two things differ from ``providers.py`` on purpose:

* **There is a default.** publish returns a needs-disambiguation sentinel
  because its providers are peers. offdesk has an installed base — the
  Syncthing vault and its project folders predate this module — so a push
  phrase that names no transport routes to ``syncthing`` and every
  pre-existing phrase keeps its meaning. ``icloud`` is opt-in per push.
* **Pull spans both transports.** An annotation is made away from the
  desk, and which device it was left on is exactly the detail the skill
  exists to spare the user. ``resolve_pull_scope`` therefore returns both
  transports unless the phrase names one.

``syncthing`` also honours a legacy env var, ``OFFDESK_OBSIDIAN_VAULT``,
which was the skill's only knob before transports existed. It is a
supported alias, not a deprecation: it sits between the transport-scoped
var and the literal default, and setting it keeps working silently.
"""

from __future__ import annotations

import glob
import os
import re
from pathlib import Path

DEFAULT_TRANSPORT = "syncthing"


class TransportResolutionError(RuntimeError):
    """Raised when a transport's vault root cannot be resolved."""


class Transport:
    """A sync transport known to the offdesk skill."""

    def __init__(
        self,
        name: str,
        env_var: str,
        triggers: tuple[str, ...],
        markers: tuple[str, ...],
        pull_triggers: tuple[str, ...],
        default_root: str | None = None,
        default_root_glob: str | None = None,
        legacy_env_var: str | None = None,
    ) -> None:
        if (default_root is None) == (default_root_glob is None):
            raise ValueError(
                "exactly one of default_root or default_root_glob must be set"
            )
        self.name = name
        self.env_var = env_var
        self.triggers = triggers
        self.markers = markers
        self.pull_triggers = pull_triggers
        self.default_root = default_root
        self.default_root_glob = default_root_glob
        self.legacy_env_var = legacy_env_var

    @property
    def env_vars(self) -> tuple[str, ...]:
        """Env vars consulted for this transport, highest precedence first."""
        if self.legacy_env_var is None:
            return (self.env_var,)
        return (self.env_var, self.legacy_env_var)


SYNCTHING = Transport(
    name="syncthing",
    env_var="OFFDESK_SYNCTHING_VAULT",
    legacy_env_var="OFFDESK_OBSIDIAN_VAULT",
    default_root="~/Obsidian/offdesk",
    triggers=(
        "send to offdesk",
        "send to phone for review",
        "review later",
        "check later",
        "положи это в offdesk",
        "положи это в оффдеск",
        "посмотрю позже",
        "проверю позже",
    ),
    markers=("syncthing", "синктинг"),
    pull_triggers=(
        "check offdesk syncthing",
        "review my offdesk syncthing notes",
        "проверь оффдеск синктинг",
        "посмотри оффдеск синктинг фидбэк",
    ),
)

ICLOUD = Transport(
    name="icloud",
    env_var="OFFDESK_ICLOUD_VAULT",
    default_root_glob="~/Library/Mobile Documents/iCloud~md~obsidian/Documents/*",
    triggers=(
        "send to offdesk icloud",
        "offdesk icloud",
        "offdesk on icloud",
        "положи в offdesk icloud",
        "положи в оффдеск айклауд",
        "оффдеск айклауд",
    ),
    markers=("icloud", "айклауд"),
    pull_triggers=(
        "check offdesk icloud",
        "review my offdesk icloud notes",
        "проверь оффдеск айклауд",
        "посмотри оффдеск айклауд фидбэк",
    ),
)

TRANSPORTS: dict[str, Transport] = {
    SYNCTHING.name: SYNCTHING,
    ICLOUD.name: ICLOUD,
}

#: Pull phrases that name no transport — they scan every vault.
PULL_TRIGGERS: tuple[str, ...] = (
    "review my offdesk notes",
    "check offdesk feedback",
    "посмотри оффдеск фидбэк",
    "проверь оффдеск",
)

#: Words that must never appear in an offdesk trigger: they belong to the
#: publish skill's icloud provider, which renders PDF and is push-only, so a
#: shared utterance would be unresolvable between the two skills.
FOREIGN_TOKENS: tuple[str, ...] = ("ipad", "айпад", "books", "книги")


def all_triggers() -> tuple[str, ...]:
    """Every phrase this skill claims, push and pull alike."""
    phrases: list[str] = []
    for transport in TRANSPORTS.values():
        phrases.extend(transport.triggers)
        phrases.extend(transport.pull_triggers)
    phrases.extend(PULL_TRIGGERS)
    return tuple(phrases)


def _normalize(phrase: str) -> str:
    return phrase.strip().lower()


def _has_marker(needle: str, markers: tuple[str, ...]) -> bool:
    """True when a marker appears in ``needle`` as a whole word.

    Word boundaries are ``\\w``-based, which under Python's ``re`` is
    Unicode-aware, so the Cyrillic markers behave like the Latin ones.
    """
    return any(
        re.search(rf"(?<!\w){re.escape(marker)}(?!\w)", needle)
        for marker in markers
    )


def resolve_transport(phrase: str) -> str:
    """Return the transport a push phrase routes to.

    Matching is case-insensitive on the trimmed phrase. An exact trigger
    wins; otherwise a phrase carrying a transport's marker word (e.g.
    "icloud" / "айклауд") routes to that transport, so a marked utterance
    that is not on the canonical list is never silently written to the
    wrong vault. Anything else routes to ``DEFAULT_TRANSPORT``.
    """
    needle = _normalize(phrase)
    for transport in TRANSPORTS.values():
        if needle in transport.triggers:
            return transport.name
    for transport in TRANSPORTS.values():
        if transport.name != DEFAULT_TRANSPORT and _has_marker(
            needle, transport.markers
        ):
            return transport.name
    return DEFAULT_TRANSPORT


def resolve_pull_scope(phrase: str) -> tuple[str, ...]:
    """Return the transports a pull phrase scans, in declaration order.

    A phrase that names a transport — by exact pull trigger or by marker
    word — narrows the scan to that one. Every other phrase, including the
    four transport-neutral pull triggers, scans them all. A phrase naming
    both transports scans both, which is also the default, so the two
    readings agree.
    """
    needle = _normalize(phrase)
    for transport in TRANSPORTS.values():
        if needle in transport.pull_triggers:
            return (transport.name,)
    marked = tuple(
        transport.name
        for transport in TRANSPORTS.values()
        if _has_marker(needle, transport.markers)
    )
    return marked or tuple(TRANSPORTS)


def resolve_root(transport_name: str, env: dict[str, str] | None = None) -> Path:
    """Return the absolute vault root for a transport.

    Env vars are read in ``Transport.env_vars`` order and the first set,
    non-empty one wins verbatim (trailing slash stripped); the default root
    is not consulted when one is set. ``env`` defaults to ``os.environ`` and
    exists so tests can inject an isolated mapping.

    When no env var is set, a literal default root (``syncthing``) is
    expanded and returned. A glob default root (``icloud``, whose vault
    directory is named by the user in Obsidian on iOS) is expanded against
    the filesystem; 0 or >1 matching directories raise
    ``TransportResolutionError`` naming the env var as the disambiguator.
    """
    transport = TRANSPORTS[transport_name]
    source = os.environ if env is None else env
    for var in transport.env_vars:
        override = source.get(var, "").strip()
        if override:
            return Path(override.rstrip("/")).expanduser()
    if transport.default_root is not None:
        return Path(transport.default_root.rstrip("/")).expanduser()
    return _resolve_from_glob(transport)


def _resolve_from_glob(transport: Transport) -> Path:
    pattern = os.path.expanduser(transport.default_root_glob or "")
    # Directories only: the pattern ends in a bare ``*``, so a stray file
    # beside the vaults would otherwise count as a candidate and turn a
    # single-vault machine into a spurious multi-match hard-fail.
    matches = sorted(m for m in glob.glob(pattern) if os.path.isdir(m))
    if len(matches) == 1:
        return Path(matches[0].rstrip("/"))
    hint = (
        f"set {transport.env_var} to the absolute path of the "
        f"{transport.name} vault root"
    )
    if not matches:
        raise TransportResolutionError(
            f"no directory matched {pattern!r} for transport "
            f"{transport.name!r}; {hint}."
        )
    raise TransportResolutionError(
        f"{len(matches)} directories matched {pattern!r} for transport "
        f"{transport.name!r}; {hint}. Matches: {matches}"
    )
