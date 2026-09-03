"""Tests for the single-slide dump.

The point of interest is the plain ``import compare_decks`` at the top of
``dump_slide.py``: importing this test module at all proves the two scripts
share a shape model without any file-loader indirection.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
FIXTURES = HERE / "fixtures"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import compare_decks  # noqa: E402
import dump_slide  # noqa: E402

GEN = FIXTURES / "gen.pptx"


@pytest.fixture(scope="module")
def shapes():
    return compare_decks.parse_deck(GEN)[0]


def test_dump_slide_reuses_the_comparison_shape_model():
    assert dump_slide.compare_decks is compare_decks
    assert dump_slide.Shape is compare_decks.Shape


def test_frame_is_printed_in_both_emu_and_inches(shapes):
    text = "\n".join(dump_slide.format_shape(shapes[0]))
    assert "685800 EMU (0.750in)" in text
    for axis in ("x:", "y:", "w:", "h:"):
        assert axis in text


def test_fill_line_and_wrap_are_printed(shapes):
    text = "\n".join(dump_slide.format_shape(shapes[0]))
    assert "fill:" in text
    assert "line:" in text
    assert "wrap:" in text


def test_runs_are_printed_with_their_formatting(shapes):
    text = "\n".join(dump_slide.format_shape(shapes[0]))
    assert "'Structural comparison'" in text
    assert "font='Arial'" in text
    assert "size=24.0pt" in text
    assert "bold" in text


def test_out_of_range_slide_is_rejected(capsys):
    assert dump_slide.main([str(GEN), "2"]) == 2
    assert "out of range" in capsys.readouterr().err


def test_missing_deck_is_rejected(capsys, tmp_path):
    assert dump_slide.main([str(tmp_path / "nope.pptx"), "1"]) == 2
    assert "no such deck" in capsys.readouterr().err


def test_dump_of_the_fixture_lists_every_shape(capsys):
    assert dump_slide.main([str(GEN), "1"]) == 0
    out = capsys.readouterr().out
    assert "gen.pptx slide 1/1: 3 shapes" in out
    for name in ("'title'", "'body-box'", "'extra-note'"):
        assert name in out
