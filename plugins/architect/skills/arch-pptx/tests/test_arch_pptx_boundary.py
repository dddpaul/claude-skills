"""Guard arch-pptx's boundary against its bank-adjacent neighbours.

The SKILL.md description must fence ``abs-slide``, ``abs-puml``,
``ak-style`` and ``arch-drawio`` by name, and no file of the skill may
carry a bank host, an internal repo URL or layer-model vocabulary: this
repository is public. Forbidden terms are assembled from parts so this
file does not itself contain them.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL = Path(__file__).parent.parent
SKILL_MD = SKILL / "SKILL.md"
REFERENCE = SKILL / "references" / "style-studio-pptx.md"
TEXT_SUFFIXES = {".md", ".py"}

FORBIDDEN = [
    "al" + "fa",  # the bank's host / marketplace name
    "service-to-" + "layer",
    "channel " + "band",
    "block " + "status",
    "block " + "mark",
    "ABS " + "2030",
    ".slide." + "yaml",
    "layer " + "model",
]


def _skill_files() -> list[Path]:
    return [
        p
        for p in SKILL.rglob("*")
        if p.suffix in TEXT_SUFFIXES and "__pycache__" not in p.parts
    ]


def _description() -> str:
    match = re.search(r"^description: (.+)$", SKILL_MD.read_text(), re.M)
    assert match, "SKILL.md has no description line"
    return match.group(1)


@pytest.mark.parametrize(
    "neighbour", ["abs-slide", "abs-puml", "ak-style", "arch-drawio"]
)
def test_description_fences_each_neighbour(neighbour: str) -> None:
    assert neighbour in _description()


def test_description_routes_bank_slides_to_abs_slide_even_for_studio() -> None:
    description = _description()
    assert "AS IS / TO BE" in description
    assert 'routes to abs-slide even when the user says "studio"' in description


def test_body_has_the_bank_standard_deliverables_note() -> None:
    body = SKILL_MD.read_text().split("---", 2)[2]
    assert "not a bank standard: a bank AK deliverable uses `ak-style` or" in body


def test_body_lists_the_font_precondition() -> None:
    body = SKILL_MD.read_text()
    for family in ("IBM Plex Sans", "IBM Plex Mono", "IBM Plex Sans Condensed"):
        assert family in body


@pytest.mark.parametrize("term", FORBIDDEN)
def test_no_bank_vocabulary_in_skill_files(term: str) -> None:
    hits = [
        str(p.relative_to(SKILL))
        for p in _skill_files()
        if term.lower() in p.read_text().lower()
    ]
    assert hits == [], f"{term!r} found in {hits}"


def test_no_urls_in_skill_files() -> None:
    hits = [
        str(p.relative_to(SKILL))
        for p in _skill_files()
        if re.search(r"https?://", p.read_text())
    ]
    assert hits == []


def test_reference_carries_no_abs_tokens() -> None:
    text = REFERENCE.read_text()
    assert not re.search(r"\bABS\b", text)
    assert "layer" not in text.lower()
