"""Verify Obsidian-style heading anchors converge between href and id.

The reading:books skill renders heading ids via a custom ``obsidian_slugify``
and rewrites raw markdown link fragments through the same function before
conversion. This test runs the production pipeline on a fixture that exercises
Cyrillic, em-dash, dot, slash, and ASCII heading text, then asserts every
internal ``#fragment`` resolves to a heading ``id`` in the same document.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

HERE = Path(__file__).parent
SCRIPT = HERE.parent / "scripts" / "md-to-pdf.py"
FIXTURE = HERE / "fixtures" / "anchors.md"


def _load_module():
    spec = importlib.util.spec_from_file_location("books_md_to_pdf", SCRIPT)
    assert spec and spec.loader, f"cannot load {SCRIPT}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract(html: str) -> tuple[list[str], set[str]]:
    hrefs = re.findall(r'href="#([^"]+)"', html)
    ids = set(re.findall(r'\sid="([^"]+)"', html))
    return hrefs, ids


def test_every_internal_href_resolves_to_a_heading_id():
    mod = _load_module()
    raw = FIXTURE.read_text(encoding="utf-8")
    html, _md = mod.md_to_html(raw)
    hrefs, ids = _extract(html)
    assert hrefs, "fixture must contain at least one internal anchor link"
    missing = [h for h in hrefs if h not in ids]
    assert not missing, (
        f"unresolved fragments: {missing}; ids present: {sorted(ids)}"
    )


def test_each_character_class_resolves():
    mod = _load_module()
    raw = FIXTURE.read_text(encoding="utf-8")
    html, _md = mod.md_to_html(raw)
    _hrefs, ids = _extract(html)
    cases = {
        "ascii": mod.obsidian_slugify("Ascii heading"),
        "cyrillic-only": mod.obsidian_slugify("Кириллица только"),
        "em-dash": mod.obsidian_slugify(
            "3.2 Camunda — соседняя ИС вне периметра ПФ"
        ),
        "dot-bearing": mod.obsidian_slugify(
            "4. Plan B: если Путь 1 не получится"
        ),
        "slash-bearing": mod.obsidian_slugify("4.2 Сводка путей 2/3/4"),
    }
    for label, expected in cases.items():
        assert expected in ids, (
            f"{label}: expected id '{expected}' not in {sorted(ids)}"
        )


def test_slugify_preserves_required_character_classes():
    mod = _load_module()
    s = mod.obsidian_slugify("3.2 Camunda — соседняя ИС вне периметра ПФ")
    assert s == "3.2-camunda-—-соседняя-ис-вне-периметра-пф"
    assert "—" in s, "em-dash must be preserved"
    assert "/" in mod.obsidian_slugify("4.2 Сводка путей 2/3/4")
    assert "." in mod.obsidian_slugify("4. Plan B")
    assert mod.obsidian_slugify("Mixed CASE Text") == "mixed-case-text"
    assert mod.obsidian_slugify("collapse   runs  of    space") == (
        "collapse-runs-of-space"
    )


def test_both_bare_and_angle_bracket_fragment_forms_normalize():
    mod = _load_module()
    bare = "[a](#3.2 Camunda — соседняя ИС вне периметра ПФ)"
    angle = "[a](<#3.2 Camunda — соседняя ИС вне периметра ПФ>)"
    expected = "[a](<#3.2-camunda-—-соседняя-ис-вне-периметра-пф>)"
    assert mod._normalize_fragments(bare) == expected
    assert mod._normalize_fragments(angle) == expected
