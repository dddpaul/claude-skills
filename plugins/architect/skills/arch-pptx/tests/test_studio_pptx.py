"""Verify the arch-pptx helper reproduces the studio preset in PPTX.

Hermetic: python-pptx only, no LibreOffice and no fonts needed. Covers
the eleven tokens (against both the arch-drawio source of truth and this
skill's reference), px -> EMU/pt conversions, per-kind shape properties,
the ``custDash`` / ``tailEnd`` XML, the QA checks, ``add_png`` and a
build-and-reopen of the sample diagram.
"""

from __future__ import annotations

import importlib.util
import re
import struct
import sys
import zlib
from pathlib import Path

import pytest
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

HERE = Path(__file__).parent
SKILL = HERE.parent
SCRIPTS = SKILL / "scripts"
DRAWIO_REF = SKILL.parent / "arch-drawio" / "references" / "style-studio.md"
PPTX_REF = SKILL / "references" / "style-studio-pptx.md"


def _load(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sp = _load("studio_pptx")
sample = _load("sample_diagram")


def _palette(path: Path) -> dict[str, str]:
    rows = re.findall(r"^\| (\w+) \| (#[0-9a-f]{6}) \|", path.read_text(), re.M)
    return dict(rows)


def _ln(shape):
    return shape._element.spPr.find(qn("a:ln"))


def _png(width: int, height: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    raw = b"".join(b"\x00" + b"\xff\xff\xff" * width for _ in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


# --- tokens and conversions ---------------------------------------------------


def test_eleven_tokens_match_the_drawio_preset() -> None:
    assert len(sp.TOKENS) == 11
    assert sp.TOKENS == _palette(DRAWIO_REF)


def test_reference_lists_the_same_eleven_tokens() -> None:
    assert _palette(PPTX_REF) == sp.TOKENS


@pytest.mark.parametrize(
    ("px", "emu"), [(1, 9525), (10, 95250), (1280, 12192000), (720, 6858000)]
)
def test_px_to_emu(px: float, emu: int) -> None:
    assert sp.px(px) == emu


@pytest.mark.parametrize(
    ("px", "pt"),
    [
        (1.2, 0.9),
        (1.5, 1.125),
        (1.6, 1.2),
        (2, 1.5),
        (13, 9.75),
        (11.5, 8.625),
        (11, 8.25),
        (10.5, 7.875),
        (18, 13.5),
    ],
)
def test_px_to_pt(px: float, pt: float) -> None:
    assert sp.px_to_pt(px) == pytest.approx(pt)


def test_canvas_is_1280_by_720_px() -> None:
    d = sp.Diagram()
    assert (d.prs.slide_width, d.prs.slide_height) == (12192000, 6858000)


def test_unknown_token_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown colour token"):
        sp.rgb("blue")


# --- per-kind shape properties ------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "fill", "stroke", "dash"),
    [
        ("external", "EAF0F8", "C3CCD7", ("500000", "400000")),
        ("internal", "E9F4EC", "2C7A4B", None),
        ("repo", "F1EFE9", "C3CCD7", None),
        ("fence", None, "A8681A", ("300000", "400000")),
    ],
)
def test_zone_kinds(kind, fill, stroke, dash) -> None:
    d = sp.Diagram()
    z = d.zone(40, 40, 400, 200, "Zone", kind=kind)
    shape = z.shape
    assert shape.auto_shape_type == MSO_SHAPE.ROUNDED_RECTANGLE
    assert shape.adjustments[0] == pytest.approx(10 / 200, abs=1e-5)
    if fill is None:
        assert shape._element.spPr.find(qn("a:noFill")) is not None
    else:
        assert str(shape.fill.fore_color.rgb) == fill
    assert str(shape.line.color.rgb) == stroke
    assert shape.line.width == 9525
    ds = _ln(shape).find(qn("a:custDash") + "/" + qn("a:ds"))
    assert (None if ds is None else (ds.get("d"), ds.get("sp"))) == dash
    run = shape.text_frame.paragraphs[0].runs[0]
    assert run.text == "ZONE"
    assert run.font.bold and run.font.size.pt == pytest.approx(7.875, abs=0.01)
    assert run._r.rPr.get("spc") == "63"
    assert str(run.font.color.rgb) == "5A6575"
    anchor = "b" if kind == "fence" else "t"
    assert shape.text_frame._bodyPr.get("anchor") == anchor


@pytest.mark.parametrize(
    ("kind", "stroke", "width_px"),
    [("plain", "C3CCD7", 1.2), ("secret", "B3362B", 1.6), ("gate", "A8681A", 2)],
)
def test_box_kinds(kind, stroke, width_px) -> None:
    d = sp.Diagram()
    b = d.box(40, 40, 200, 60, "Title", sub="sub", kind=kind)
    assert b.shape.adjustments[0] == pytest.approx(6 / 60, abs=1e-5)
    assert str(b.shape.fill.fore_color.rgb) == "FFFFFF"
    assert str(b.shape.line.color.rgb) == stroke
    assert b.shape.line.width == round(width_px * 9525)
    tf = b.shape.text_frame
    assert tf.margin_left == 16 * 9525
    title, sub = (p.runs[0] for p in tf.paragraphs)
    assert (title.font.name, title.font.bold, title.font.size.pt) == (
        "IBM Plex Sans",
        True,
        9.75,
    )
    assert str(title.font.color.rgb) == "18202B"
    assert sub.font.size.pt == pytest.approx(8.625, abs=0.01)
    assert str(sub.font.color.rgb) == "5A6575"


def test_box_with_code_line_is_top_aligned_with_a_mono_line() -> None:
    d = sp.Diagram()
    b = d.box(40, 40, 200, 60, "Svc", code="svc --flag")
    assert b.shape.text_frame._bodyPr.get("anchor") == "t"
    code = d.items[-1]
    assert (code.y, code.h, code.role) == (70, 20, "inner")
    run = code.shape.text_frame.paragraphs[0].runs[0]
    assert (run.font.name, run.font.size.pt) == ("IBM Plex Mono", 8.25)


def test_chip_store_person_group_title_note() -> None:
    d = sp.Diagram()
    chip = d.chip(40, 40, 120, "topic", kind="deny")
    assert chip.h == 30 and chip.shape.adjustments[0] == pytest.approx(4 / 30, abs=1e-5)
    run = chip.shape.text_frame.paragraphs[0].runs[0]
    assert (run.font.name, str(run.font.color.rgb)) == ("IBM Plex Mono", "B3362B")
    assert str(chip.shape.line.color.rgb) == "B3362B"

    store = d.store(40, 100, 140, 80, "db", kind="secret")
    assert store.shape.auto_shape_type == MSO_SHAPE.CAN
    assert store.shape.line.width == round(1.6 * 9525)

    person = d.person(40, 200, 140, 60, "User")
    assert person.shape.adjustments[0] == pytest.approx(0.5, abs=1e-5)

    group = d.group(200, 40, 300, 200, "cluster")
    assert group.shape.adjustments[0] == pytest.approx(8 / 200, abs=1e-5)
    assert group.shape.line.width == 9525

    title = d.title(40, 300, 400, "Heading")
    run = title.shape.text_frame.paragraphs[0].runs[0]
    assert (run.font.name, run.font.size.pt, run.font.bold) == (
        "IBM Plex Sans Condensed",
        13.5,
        True,
    )

    note = d.note(40, 340, 200, 20, "masked")
    assert str(note.shape.text_frame.paragraphs[0].runs[0].font.color.rgb) == "A8681A"


def test_shapes_carry_no_theme_style() -> None:
    d = sp.Diagram()
    a = d.box(40, 40, 200, 60, "A")
    e = d.edge([(240, 70), (400, 70)])
    for shape in (a.shape, e.shape):
        assert shape._element.find(qn("p:style")) is None


# --- edges ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "color", "width_px"),
    [
        ("default", "18202B", 1.5),
        ("deny", "B3362B", 1.6),
        ("ok", "2C7A4B", 1.6),
        ("gate", "A8681A", 1.6),
    ],
)
def test_edge_kinds(kind, color, width_px) -> None:
    d = sp.Diagram()
    e = d.edge([(40, 40), (200, 40), (200, 200)], kind=kind, label="lbl")
    ln = _ln(e.shape)
    assert str(e.shape.line.color.rgb) == color
    assert e.shape.line.width == round(width_px * 9525)
    tail = ln.find(qn("a:tailEnd"))
    assert tail is not None and tail.get("type") == "triangle"
    assert ln.find(qn("a:headEnd")) is None
    assert ln.find(qn("a:custDash")) is None
    assert e.shape._element.spPr.find(qn("a:noFill")) is not None
    label = e.label.shape.text_frame.paragraphs[0].runs[0]
    assert str(label.font.color.rgb) == color
    assert e.label.y + e.label.h == 38  # just above the horizontal run


def test_async_and_two_way_modifiers() -> None:
    d = sp.Diagram()
    e = d.edge([(40, 40), (200, 40)], is_async=True, two_way=True)
    ln = _ln(e.shape)
    ds = ln.find(qn("a:custDash") + "/" + qn("a:ds"))
    assert (ds.get("d"), ds.get("sp")) == ("400000", "300000")
    assert ln.find(qn("a:headEnd")).get("type") == "triangle"
    children = [c.tag for c in ln]
    assert children.index(qn("a:custDash")) == children.index(qn("a:solidFill")) + 1
    assert children[-2:] == [qn("a:headEnd"), qn("a:tailEnd")]


def test_edge_label_on_a_vertical_run_sits_to_the_right() -> None:
    d = sp.Diagram()
    e = d.edge([(100, 40), (100, 200)], label="down")
    assert e.label.x == 106


def test_edge_needs_two_points() -> None:
    with pytest.raises(ValueError):
        sp.Diagram().edge([(0, 0)])


# --- QA checks ------------------------------------------------------------------


def test_qa_flags_overlap_grid_and_edge_through_box() -> None:
    d = sp.Diagram()
    a = d.box(40, 40, 200, 60, "A")
    d.box(200, 80, 200, 60, "B")
    d.box(41, 300, 200, 60, "C")
    d.box(500, 40, 100, 60, "Mid")
    d.edge([a.right(), (700, 70)])
    issues = "\n".join(d.qa())
    assert "overlaps box-plain 'B'" in issues
    assert "box-plain 'C': geometry off the 10px grid" in issues
    assert "runs through box-plain 'Mid'" in issues


def test_qa_flags_text_over_a_zone_border_and_label() -> None:
    d = sp.Diagram()
    d.zone(100, 100, 400, 200, "Zone", kind="internal")
    d.box(110, 110, 200, 60, "Covers label")
    d.edge([(40, 200), (140, 200)], label="crossing")
    issues = "\n".join(d.qa())
    assert "covers the label of zone-internal 'ZONE'" in issues
    assert "edge-label 'crossing' is cut by the border" in issues


def test_qa_flags_text_that_does_not_fit() -> None:
    d = sp.Diagram()
    d.box(40, 40, 80, 60, "A very long component name")
    assert any("needs ~" in i for i in d.qa())


# --- fallback and smoke build -------------------------------------------------


def test_add_png_fills_the_slide(tmp_path: Path) -> None:
    png = tmp_path / "diagram.png"
    png.write_bytes(_png(64, 36))
    d = sp.Diagram()
    pic = d.add_png(png)
    assert (pic.left, pic.top) == (0, 0)
    assert (pic.width, pic.height) == (d.prs.slide_width, d.prs.slide_height)
    assert len(d.prs.slides) == 1


def test_add_png_fits_another_aspect_and_adds_a_slide(tmp_path: Path) -> None:
    png = tmp_path / "square.png"
    png.write_bytes(_png(40, 40))
    d = sp.Diagram()
    d.box(40, 40, 200, 60, "A")
    pic = d.add_png(png)
    assert len(d.prs.slides) == 2
    assert pic.height == d.prs.slide_height
    assert pic.left == (d.prs.slide_width - pic.width) // 2


def test_sample_builds_clean_and_reopens(tmp_path: Path) -> None:
    d = sample.build()
    assert d.qa() == []
    kinds = {i.kind for i in d.items}
    assert {
        "zone-internal",
        "zone-external",
        "zone-repo",
        "zone-fence",
        "group",
        "box-plain",
        "box-gate",
        "box-secret",
        "chip-plain",
        "chip-deny",
        "store-plain",
        "person",
        "title",
    } <= kinds
    edges = [i for i in d.items if isinstance(i, sp.Edge)]
    assert {e.kind for e in edges} == {"default", "deny", "ok", "gate"}
    out = d.save(tmp_path / "sample.pptx")
    reopened = Presentation(str(out))
    assert len(reopened.slides) == 1
    assert len(reopened.slides[0].shapes) == len(d.slide.shapes)
