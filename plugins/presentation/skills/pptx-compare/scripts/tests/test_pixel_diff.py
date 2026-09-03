"""Tests for the pixel-level comparison.

The images are built in-process with pillow rather than committed: unlike the
deck fixtures there is nothing engine-specific to freeze, and generating them
keeps the differing-pixel counts exact enough to assert on.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

Image = pytest.importorskip("PIL.Image")
ImageDraw = pytest.importorskip("PIL.ImageDraw")

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import pixel_diff  # noqa: E402

SIZE = (200, 120)
BAR = (10, 10, 109, 79)  # 100 x 70 pixels of black


def _page(path: Path, shift: int) -> None:
    image = Image.new("RGB", SIZE, (255, 255, 255))
    left, top, right, bottom = BAR
    ImageDraw.Draw(image).rectangle(
        [left + shift, top, right + shift, bottom], fill=(0, 0, 0)
    )
    image.save(path)


@pytest.fixture
def folders(tmp_path):
    """Two 2-page folders; page 1 differs by a 5px shift, page 2 is identical."""
    ref_dir = tmp_path / "ref"
    gen_dir = tmp_path / "gen"
    for folder in (ref_dir, gen_dir):
        folder.mkdir()
    _page(ref_dir / "page-01.png", 0)
    _page(gen_dir / "page-01.png", 5)
    _page(ref_dir / "page-02.png", 0)
    _page(gen_dir / "page-02.png", 0)
    return ref_dir, gen_dir


def test_identical_pages_report_zero(folders, tmp_path):
    ref_dir, gen_dir = folders
    pages = pixel_diff.compare_folders(ref_dir, gen_dir, tmp_path / "out", 8)
    assert pages[1].differing == 0
    assert pages[1].fraction == 0.0


def test_shifted_page_counts_both_edge_strips(folders, tmp_path):
    ref_dir, gen_dir = folders
    pages = pixel_diff.compare_folders(ref_dir, gen_dir, tmp_path / "out", 8)
    # A 5px horizontal shift of a 70px-tall bar exposes two 5px strips.
    assert pages[0].differing == 2 * 5 * 70
    assert pages[0].total == SIZE[0] * SIZE[1]
    assert pages[0].overlay.exists()


def test_contact_sheet_tiles_every_overlay(folders, tmp_path):
    ref_dir, gen_dir = folders
    outdir = tmp_path / "out"
    pages = pixel_diff.compare_folders(ref_dir, gen_dir, outdir, 8)
    sheet = pixel_diff.contact_sheet(
        [p.overlay for p in pages], outdir / "contact-sheet.png"
    )
    assert sheet is not None and sheet.exists()
    assert Image.open(sheet).size[0] == 2 * pixel_diff.CONTACT_THUMB_WIDTH


def test_contact_sheet_of_nothing_is_none(tmp_path):
    assert pixel_diff.contact_sheet([], tmp_path / "sheet.png") is None


def test_page_count_mismatch_is_rejected(folders, tmp_path):
    ref_dir, gen_dir = folders
    (gen_dir / "page-02.png").unlink()
    with pytest.raises(ValueError, match="page count differs"):
        pixel_diff.compare_folders(ref_dir, gen_dir, tmp_path / "out", 8)


def test_size_mismatch_is_rejected(folders, tmp_path):
    ref_dir, gen_dir = folders
    Image.new("RGB", (50, 50), (255, 255, 255)).save(gen_dir / "page-01.png")
    with pytest.raises(ValueError, match="size mismatch"):
        pixel_diff.compare_folders(ref_dir, gen_dir, tmp_path / "out", 8)


@pytest.mark.parametrize(
    "spec",
    ["3", "1:1,2,3", "1:10,10,5,50", "1:10,10,50,5"],
)
def test_bad_zoom_specs_are_rejected(spec):
    with pytest.raises(ValueError):
        pixel_diff.parse_zoom(spec)


def test_zoom_spec_parses():
    assert pixel_diff.parse_zoom("2:10,20,110,220") == (2, (10, 20, 110, 220))


def test_zoom_writes_three_crops(folders, tmp_path):
    ref_dir, gen_dir = folders
    outdir = tmp_path / "out"
    pages = pixel_diff.compare_folders(ref_dir, gen_dir, outdir, 8)
    written = pixel_diff.write_zoom(pages, "1:0,0,100,60", outdir)
    assert [p.name for p in written] == [
        "zoom-01-ref.png",
        "zoom-01-gen.png",
        "zoom-01-overlay.png",
    ]
    assert all(Image.open(p).size == (100, 60) for p in written)


def test_zoom_on_an_absent_page_is_rejected(folders, tmp_path):
    ref_dir, gen_dir = folders
    outdir = tmp_path / "out"
    pages = pixel_diff.compare_folders(ref_dir, gen_dir, outdir, 8)
    with pytest.raises(ValueError, match="not among the compared pages"):
        pixel_diff.write_zoom(pages, "9:0,0,10,10", outdir)


def test_main_exit_codes(folders, tmp_path, capsys):
    ref_dir, gen_dir = folders
    argv = [str(ref_dir), str(gen_dir), "--outdir", str(tmp_path / "out")]
    assert pixel_diff.main(argv) == 1
    assert pixel_diff.main(argv + ["--max-diff", "1.0"]) == 0
    assert pixel_diff.main([str(ref_dir), str(tmp_path / "nope"), "--outdir", "x"]) == 2
    capsys.readouterr()


def test_zoom_box_outside_the_page_is_rejected(folders, tmp_path):
    """Image.crop pads silently, so an oversize box must be caught here."""
    ref_dir, gen_dir = folders
    outdir = tmp_path / "out"
    pages = pixel_diff.compare_folders(ref_dir, gen_dir, outdir, 8)
    with pytest.raises(ValueError, match="reaches outside page 1"):
        pixel_diff.write_zoom(pages, "1:0,0,9999,9999", outdir)
    assert not list(outdir.glob("zoom-*.png"))


def test_zoom_box_flush_with_the_page_edge_is_allowed(folders, tmp_path):
    ref_dir, gen_dir = folders
    outdir = tmp_path / "out"
    pages = pixel_diff.compare_folders(ref_dir, gen_dir, outdir, 8)
    written = pixel_diff.write_zoom(pages, f"1:0,0,{SIZE[0]},{SIZE[1]}", outdir)
    assert all(Image.open(p).size == SIZE for p in written)


def test_zoom_box_with_a_negative_origin_is_rejected(folders, tmp_path):
    ref_dir, gen_dir = folders
    outdir = tmp_path / "out"
    pages = pixel_diff.compare_folders(ref_dir, gen_dir, outdir, 8)
    with pytest.raises(ValueError, match="reaches outside page 1"):
        pixel_diff.write_zoom(pages, "1:-500,-500,100,60", outdir)
    assert not list(outdir.glob("zoom-*.png"))
