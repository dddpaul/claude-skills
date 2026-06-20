#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "python-pptx>=0.6.21",
#   "lxml>=4.9",
# ]
# ///
"""Insert ``<a:effectLst/>`` overrides into slide-background ``<p:bgPr>`` blocks.

Why this exists: ``pptxgenjs`` v4.0.1 emits ``slide.background = { color: ... }``
as a ``<p:bg>/<p:bgPr>/<a:solidFill>`` block without an ``<a:effectLst/>``
sibling, so the theme's shadow inherits and Rule #11 in SKILL.md fires in the
pptx-arch-style linter. Until pptxgenjs ships an ``effectOverride`` option this
script is the canonical post-process step — invoke it after every generation,
before linting.

Usage:
    uv run plugins/presentation/skills/pptx-arch-style/scripts/postprocess-effectlst.py deck.pptx

The script rewrites the file in place (the input deck is replaced).
Exit codes:
    0 — every slide background now carries ``<a:effectLst/>`` (added or already present)
    1 — at least one slide background has no ``<p:bgPr>`` to patch (caller must add one)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
A_NS = NS["a"]
EFFECT_LST_TAG = f"{{{A_NS}}}effectLst"


def ensure_effectlst(slide) -> tuple[bool, bool]:
    """Add ``<a:effectLst/>`` to ``<p:bgPr>`` if missing.

    Returns ``(had_bgpr, added)``: ``had_bgpr`` is False when the slide has no
    background-properties element at all (caller should generate one upstream),
    ``added`` is True when an empty ``<a:effectLst/>`` was inserted now.
    """
    bg_pr = slide._element.find(".//p:cSld/p:bg/p:bgPr", NS)
    if bg_pr is None:
        return False, False
    existing = bg_pr.find("a:effectLst", NS)
    if existing is not None:
        return True, False
    etree.SubElement(bg_pr, EFFECT_LST_TAG)
    return True, True


def postprocess(deck_path: Path) -> int:
    deck = Presentation(str(deck_path))
    added = 0
    missing_bg: list[int] = []
    for idx, slide in enumerate(deck.slides, start=1):
        had_bgpr, did_add = ensure_effectlst(slide)
        if not had_bgpr:
            missing_bg.append(idx)
            continue
        if did_add:
            added += 1
    deck.save(str(deck_path))

    print(f"{deck_path}: {added} slide bg(s) patched with <a:effectLst/>")
    if missing_bg:
        print(
            f"warning: {len(missing_bg)} slide(s) have no <p:bgPr> to patch: "
            f"{missing_bg}",
            file=sys.stderr,
        )
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("deck", type=Path, help="Path to .pptx file (rewritten in place)")
    args = ap.parse_args(argv)
    if not args.deck.exists():
        print(f"error: {args.deck} not found", file=sys.stderr)
        return 1
    return postprocess(args.deck)


if __name__ == "__main__":
    sys.exit(main())
