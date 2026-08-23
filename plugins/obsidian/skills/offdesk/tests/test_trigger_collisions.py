"""Guard the boundary between the offdesk and publish trigger vocabularies.

Both skills reach iCloud, and both are asked for in the same breath ("send
this somewhere I can read it later"), but they have opposite contracts:
publish renders markdown to PDF and is push-only, while offdesk copies the
`.md` verbatim into an Obsidian vault and pulls annotations back. An
utterance that could mean either is unresolvable, so the vocabularies are
kept apart by construction:

* offdesk phrases are anchored on "offdesk" / "оффдеск" and never name a
  device — no `ipad`, `айпад`, `books` or `книги`.
* publish phrases never contain "offdesk" / "оффдеск".
* The two trigger sets are disjoint, and neither skill's phrase is a
  substring of the other's.

The assertions run against both the resolver modules and the phrases each
`SKILL.md` declares, so a phrase added to the docs and not to the resolver
(or the reverse) fails the suite.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

HERE = Path(__file__).parent
OFFDESK_DIR = HERE.parent
PLUGINS_DIR = OFFDESK_DIR.parents[2]

OFFDESK_TRANSPORTS_PY = OFFDESK_DIR / "scripts" / "transports.py"
OFFDESK_SKILL_MD = OFFDESK_DIR / "SKILL.md"
PUBLISH_SKILL_DIR = PLUGINS_DIR / "publish" / "skills" / "publish"
PUBLISH_PROVIDERS_PY = PUBLISH_SKILL_DIR / "scripts" / "providers.py"
PUBLISH_SKILL_MD = PUBLISH_SKILL_DIR / "SKILL.md"

FORBIDDEN_IN_OFFDESK = ("ipad", "айпад", "books", "книги")
FORBIDDEN_IN_PUBLISH = ("offdesk", "оффдеск")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _offdesk_module():
    return _load(OFFDESK_TRANSPORTS_PY, "offdesk_transports")


def _publish_module():
    return _load(PUBLISH_PROVIDERS_PY, "publish_providers")


def _offdesk_triggers() -> set[str]:
    return set(_offdesk_module().all_triggers())


def _publish_triggers() -> set[str]:
    mod = _publish_module()
    return {
        phrase
        for provider in mod.PROVIDERS.values()
        for phrase in provider.triggers
    }


def _normalized(path: Path) -> str:
    """SKILL.md text with markdown line wrapping collapsed to single spaces."""
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


def _declared_phrases(path: Path) -> set[str]:
    """Quoted phrases on a SKILL.md ``description:`` frontmatter line.

    Only the description is scanned: an offdesk body section deliberately
    quotes publish's phrases to tell the two skills apart, and that prose
    must not read as an offdesk claim.
    """
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^description:.*$", text, flags=re.MULTILINE)
    assert match, f"no description line in {path}"
    return {phrase.lower() for phrase in re.findall(r'"([^"]+)"', match.group(0))}


def test_trigger_sets_are_disjoint():
    overlap = _offdesk_triggers() & _publish_triggers()
    assert not overlap, f"offdesk and publish share trigger phrases: {overlap}"


def test_skill_md_declared_phrases_are_disjoint():
    overlap = _declared_phrases(OFFDESK_SKILL_MD) & _declared_phrases(
        PUBLISH_SKILL_MD
    )
    assert not overlap, f"SKILL.md files share trigger phrases: {overlap}"


def test_no_offdesk_phrase_names_a_device():
    offenders = {
        phrase
        for phrase in _offdesk_triggers() | _declared_phrases(OFFDESK_SKILL_MD)
        for token in FORBIDDEN_IN_OFFDESK
        if token in phrase
    }
    assert not offenders, f"offdesk phrases must not name a device: {offenders}"


def test_forbidden_token_list_matches_the_resolver():
    assert _offdesk_module().FOREIGN_TOKENS == FORBIDDEN_IN_OFFDESK


def test_no_publish_phrase_claims_offdesk():
    offenders = {
        phrase
        for phrase in _publish_triggers() | _declared_phrases(PUBLISH_SKILL_MD)
        for token in FORBIDDEN_IN_PUBLISH
        if token in phrase
    }
    assert not offenders, f"publish phrases must not claim offdesk: {offenders}"


def test_neither_skills_phrase_contains_the_others():
    offdesk = _offdesk_triggers()
    publish = _publish_triggers()
    overlaps = {
        (a, b)
        for a in offdesk
        for b in publish
        if a in b or b in a
    }
    assert not overlaps, f"phrases collide by containment: {overlaps}"


def test_every_offdesk_phrase_is_documented_in_skill_md():
    text = _normalized(OFFDESK_SKILL_MD)
    missing = {p for p in _offdesk_triggers() if p not in text}
    assert not missing, f"phrases missing from offdesk SKILL.md: {missing}"


def test_every_publish_phrase_is_documented_in_skill_md():
    text = _normalized(PUBLISH_SKILL_MD)
    missing = {p for p in _publish_triggers() if p not in text}
    assert not missing, f"phrases missing from publish SKILL.md: {missing}"


def test_offdesk_skill_md_declares_no_phrase_the_resolver_ignores():
    mod = _offdesk_module()
    # Markers are quoted in the description as words to add to a pull
    # phrase, not as phrases in their own right.
    markers = {
        marker
        for transport in mod.TRANSPORTS.values()
        for marker in transport.markers
    }
    unknown = _declared_phrases(OFFDESK_SKILL_MD) - _offdesk_triggers() - markers
    assert not unknown, f"SKILL.md declares phrases the resolver ignores: {unknown}"


def test_publish_skill_md_declares_no_phrase_the_resolver_ignores():
    unknown = _declared_phrases(PUBLISH_SKILL_MD) - _publish_triggers()
    assert not unknown, f"SKILL.md declares phrases the resolver ignores: {unknown}"
