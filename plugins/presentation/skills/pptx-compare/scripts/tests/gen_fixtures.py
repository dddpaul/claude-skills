#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "python-pptx>=1.0.2",
# ]
# ///
"""Regenerate the fixture decks under ``fixtures/``.

Two one-slide decks that are identical apart from three deliberately planted
discrepancies, so ``test_compare_decks.py`` can assert the parse finds exactly
those and nothing else:

1. the title is 28pt in ref and 24pt in gen — a formatting delta;
2. the rectangle sits 0.10in further right in gen — a coordinate delta, chosen
   to fall outside the 0.04in default tolerance but inside a 0.25in one, so the
   same pair of fixtures exercises the ``--pos-tol`` flag both ways;
3. gen carries an extra textbox that ref does not have — an unmatched shape.

Both decks are built with python-pptx rather than the JS generator the sibling
``pptx-arch-style`` skill uses for its fixtures: python-pptx is already a dev
dependency of this repository, so the tests need neither Node nor a vendored
``node_modules``.

Usage:
    uv run gen_fixtures.py
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"

TITLE_TEXT = "Structural comparison"
RECT_X_IN = 0.60
GEN_RECT_X_IN = 0.70  # planted delta 2: 0.10in right of ref


def build(path: Path, *, title_size_pt: int, rect_x_in: float, extra: bool) -> None:
    """Write a one-slide deck with the given planted variations."""
    presentation = Presentation()
    presentation.slide_width = Inches(10)
    presentation.slide_height = Inches(5.625)
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])

    title = slide.shapes.add_textbox(Inches(0.75), Inches(0.20), Inches(8.5), Inches(0.6))
    title.name = "title"
    run = title.text_frame.paragraphs[0].add_run()
    run.text = TITLE_TEXT
    run.font.name = "Arial"
    run.font.size = Pt(title_size_pt)
    run.font.bold = True

    from pptx.enum.shapes import MSO_SHAPE

    rect = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(rect_x_in), Inches(1.20), Inches(3.0), Inches(1.0)
    )
    rect.name = "body-box"

    if extra:
        box = slide.shapes.add_textbox(
            Inches(6.00), Inches(1.20), Inches(3.0), Inches(0.5)
        )
        box.name = "extra-note"
        box.text_frame.paragraphs[0].add_run().text = "only in gen"

    presentation.save(str(path))


def main() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    build(FIXTURES / "ref.pptx", title_size_pt=28, rect_x_in=RECT_X_IN, extra=False)
    build(FIXTURES / "gen.pptx", title_size_pt=24, rect_x_in=GEN_RECT_X_IN, extra=True)
    print(f"wrote ref.pptx and gen.pptx to {FIXTURES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
