"""Studio-preset architecture diagrams as native, editable PPTX shapes.

A port of the arch-drawio studio preset to python-pptx. The slide is a
1280x720 px canvas and 1 px is 9525 EMU, so draw.io geometry (10px grid,
40/30px gaps, sizes, radii) carries over unchanged. Strokes and font sizes
are given in px, as in the preset, and converted to points (1 px = 0.75 pt).

Typical build script::

    from studio_pptx import Diagram

    d = Diagram()
    d.title(40, 30, 600, "Order flow")
    z = d.zone(40, 80, 600, 300, "INTERNAL", kind="internal")
    a = d.box(80, 140, 200, 60, "Orders API", sub="REST")
    b = d.store(380, 130, 160, 80, "orders", sub="PostgreSQL")
    d.edge([a.right(), b.left()], label="writes")
    for issue in d.qa():
        print(issue)
    d.save("order-flow.pptx")
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

# --- tokens -----------------------------------------------------------------

TOKENS: dict[str, str] = {
    "panel": "#ffffff",
    "fg": "#18202b",
    "muted": "#5a6575",
    "line": "#c3ccd7",
    "ext": "#eaf0f8",
    "int": "#e9f4ec",
    "repo": "#f1efe9",
    "deny": "#b3362b",
    "gate": "#a8681a",
    "ok": "#2c7a4b",
    "bg": "#f4f6f8",
}

SANS = "IBM Plex Sans"
MONO = "IBM Plex Mono"
CONDENSED = "IBM Plex Sans Condensed"

CANVAS_W = 1280
CANVAS_H = 720
GRID = 10
EMU_PER_PX = 9525

# --- per-kind specs: (fill, stroke, stroke px, dash, radius px) ---------------

ZONES: dict[str, tuple[str | None, str, float, str | None]] = {
    "external": ("ext", "line", 1, "5 4"),
    "internal": ("int", "ok", 1, None),
    "repo": ("repo", "line", 1, None),
    "fence": (None, "gate", 1, "3 4"),
}
BOXES: dict[str, tuple[str, float]] = {
    "plain": ("line", 1.2),
    "secret": ("deny", 1.6),
    "deny": ("deny", 1.6),
    "gate": ("gate", 2),
}
STORES: dict[str, tuple[str, float]] = {
    "plain": ("line", 1.2),
    "secret": ("deny", 1.6),
}
CHIPS: dict[str, str] = {"plain": "muted", "deny": "deny"}
EDGES: dict[str, tuple[str, float]] = {
    "default": ("fg", 1.5),
    "deny": ("deny", 1.6),
    "ok": ("ok", 1.6),
    "gate": ("gate", 1.6),
}
ASYNC_DASH = "4 3"

ZONE_RADIUS = 10
GROUP_RADIUS = 8
BOX_RADIUS = 6
CHIP_RADIUS = 4
CHIP_H = 30
STORE_CAP = 20  # height of the cylinder's top ellipse (draw.io size=10)

LABEL_PX = 10.5
LABEL_SPACING_EM = 0.08
TITLE_PX = 13
SUB_PX = 11.5
CODE_PX = 11
EDGE_LABEL_PX = 11.5
HEADING_PX = 18
INSET = 16
LABEL_INSET_V = 13

# Arrowhead size relative to the stroke width (sm/med/lg = 2/3/5x).
ARROW_W = "lg"
ARROW_LEN = "lg"

# Average glyph width in em, used by qa() to flag text that may not fit.
AVG_GLYPH_EM = {SANS: 0.56, MONO: 0.6, CONDENSED: 0.48}


# --- conversions --------------------------------------------------------------


def px(value: float) -> Emu:
    """Convert canvas px to EMU (1 px = 9525 EMU)."""
    return Emu(round(value * EMU_PER_PX))


def px_to_pt(value: float) -> float:
    """Convert px to points (1 px = 0.75 pt at 96 dpi)."""
    return value * 0.75


def font_size(value: float) -> Pt:
    """Return a python-pptx font size for a size given in px."""
    return Pt(px_to_pt(value))


def rgb(token: str) -> RGBColor:
    """Return the RGBColor of a palette token (or a literal ``#rrggbb``)."""
    value = TOKENS.get(token, token)
    if not value.startswith("#") or len(value) != 7:
        raise ValueError(f"unknown colour token {token!r}; use one of {list(TOKENS)}")
    return RGBColor.from_string(value[1:].upper())


def dash_xml(pattern: str) -> etree._Element:
    """Return an ``a:custDash`` element for a draw.io ``dashPattern``.

    Both draw.io and DrawingML count dashes in stroke widths; DrawingML
    stores them in 1/1000 of a percent, so ``"5 4"`` becomes ``d=500000``,
    ``sp=400000``.
    """
    dash, space = (float(v) for v in pattern.split())
    cust = etree.SubElement(etree.Element(qn("a:ln")), qn("a:custDash"))
    ds = etree.SubElement(cust, qn("a:ds"))
    ds.set("d", str(round(dash * 100000)))
    ds.set("sp", str(round(space * 100000)))
    return cust


# --- geometry -----------------------------------------------------------------

Point = tuple[float, float]


@dataclass
class Node:
    """A placed element: its kind, px geometry and python-pptx shape."""

    kind: str
    x: float
    y: float
    w: float
    h: float
    shape: object = None
    role: str = "node"  # node | container | fence | text | label | inner
    text: list[tuple[str, float, str]] = field(default_factory=list)

    def at(self, fx: float, fy: float) -> Point:
        """Return the point at fractions ``fx``, ``fy`` of the bounding box."""
        return (self.x + self.w * fx, self.y + self.h * fy)

    def left(self, f: float = 0.5) -> Point:
        """Point on the left side, ``f`` of the way down."""
        return self.at(0, f)

    def right(self, f: float = 0.5) -> Point:
        """Point on the right side, ``f`` of the way down."""
        return self.at(1, f)

    def top(self, f: float = 0.5) -> Point:
        """Point on the top side, ``f`` of the way across."""
        return self.at(f, 0)

    def bottom(self, f: float = 0.5) -> Point:
        """Point on the bottom side, ``f`` of the way across."""
        return self.at(f, 1)

    @property
    def box(self) -> tuple[float, float, float, float]:
        """Bounding box as (x0, y0, x1, y1)."""
        return (self.x, self.y, self.x + self.w, self.y + self.h)


@dataclass
class Edge:
    """A placed edge: kind, px waypoints and the python-pptx shape."""

    kind: str
    points: list[Point]
    shape: object = None
    label: Node | None = None


# --- low-level shape styling ----------------------------------------------------


def _strip_style(shape: object) -> None:
    """Drop the theme ``p:style`` so no theme fill, line or shadow leaks in."""
    sp = shape._element  # type: ignore[attr-defined]
    style = sp.find(qn("p:style"))
    if style is not None:
        sp.remove(style)


def _style_line(
    shape: object,
    color: str | None,
    width_px: float = 1,
    dash: str | None = None,
    head: bool = False,
    tail: bool = False,
) -> None:
    """Set stroke colour, width, dash and arrowheads on a shape's ``a:ln``."""
    line = shape.line  # type: ignore[attr-defined]
    if color is None:
        line.fill.background()
        return
    line.color.rgb = rgb(color)
    line.width = px(width_px)
    ln = line._get_or_add_ln()
    for tag in ("a:prstDash", "a:custDash", "a:headEnd", "a:tailEnd"):
        for old in ln.findall(qn(tag)):
            ln.remove(old)
    if dash:
        ln.find(qn("a:solidFill")).addnext(dash_xml(dash))
    for flag, tag in ((head, "a:headEnd"), (tail, "a:tailEnd")):
        if flag:
            end = etree.SubElement(ln, qn(tag))
            end.set("type", "triangle")
            end.set("w", ARROW_W)
            end.set("len", ARROW_LEN)


def _style_fill(shape: object, color: str | None) -> None:
    """Solid fill in a palette colour, or no fill for ``None``."""
    fill = shape.fill  # type: ignore[attr-defined]
    if color is None:
        fill.background()
    else:
        fill.solid()
        fill.fore_color.rgb = rgb(color)


@dataclass
class Run:
    """One run of text: its string, px size, colour token and font."""

    text: str
    size: float
    color: str
    font: str = SANS
    bold: bool = False
    spacing_em: float = 0.0


def _write_text(
    shape: object,
    paragraphs: Sequence[Run],
    align: str = "left",
    anchor: str = "middle",
    inset: tuple[float, float, float, float] = (0, 0, 0, 0),
    wrap: bool = True,
) -> None:
    """Write one paragraph per run into a shape's text frame.

    ``inset`` is (left, top, right, bottom) in px.
    """
    tf = shape.text_frame  # type: ignore[attr-defined]
    tf.word_wrap = wrap
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = {
        "top": MSO_ANCHOR.TOP,
        "middle": MSO_ANCHOR.MIDDLE,
        "bottom": MSO_ANCHOR.BOTTOM,
    }[anchor]
    left, top, right, bottom = inset
    tf.margin_left, tf.margin_top = px(left), px(top)
    tf.margin_right, tf.margin_bottom = px(right), px(bottom)
    for i, spec in enumerate(paragraphs):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = {
            "left": PP_ALIGN.LEFT,
            "center": PP_ALIGN.CENTER,
            "right": PP_ALIGN.RIGHT,
        }[align]
        run = para.add_run()
        run.text = spec.text
        run.font.size = font_size(spec.size)
        run.font.name = spec.font
        run.font.bold = spec.bold
        run.font.color.rgb = rgb(spec.color)
        if spec.spacing_em:
            spc = round(px_to_pt(spec.size * spec.spacing_em) * 100)
            run._r.get_or_add_rPr().set("spc", str(spc))


def _round_adj(radius_px: float, w: float, h: float) -> float:
    """roundRect adjustment for a corner radius: radius / min(w, h)."""
    return min(0.5, radius_px / min(w, h))


def _zone_label(text: str) -> Run:
    """Zone and group label: 10.5px semibold muted, letter-spacing .08em."""
    return Run(text, LABEL_PX, "muted", bold=True, spacing_em=LABEL_SPACING_EM)


def _title_runs(title: str, sub: str | None) -> list[Run]:
    """Box title (13px bold fg) and an optional subtitle (11.5px muted)."""
    runs = [Run(title, TITLE_PX, "fg", bold=True)]
    if sub:
        runs.append(Run(sub, SUB_PX, "muted"))
    return runs


def _label_width(text: str, size: float, font: str) -> float:
    """Estimated rendered width of one line of text, in px."""
    return len(text) * size * AVG_GLYPH_EM[font]


def _snap_up(value: float) -> float:
    """Round up to the next grid step."""
    return -(-value // GRID) * GRID


# --- the diagram ----------------------------------------------------------------


class Diagram:
    """A deck of studio-preset diagram slides on a 1280x720 px canvas.

    Every method takes px coordinates and returns the placed ``Node`` (or
    ``Edge``) so later calls can anchor edges to it.
    """

    def __init__(self, background: str = "panel") -> None:
        """Create a 16:9 deck with one blank slide.

        Args:
            background: palette token for the slide background, ``panel``
                (white) or ``bg`` when the slide stands on its own.
        """
        self.prs = Presentation()
        self.prs.slide_width = px(CANVAS_W)
        self.prs.slide_height = px(CANVAS_H)
        self.background = background
        self.pages: list[list[Node | Edge]] = []
        self.slide = None
        self.new_slide()

    @property
    def items(self) -> list[Node | Edge]:
        """Elements placed on the current slide."""
        return self.pages[-1]

    def new_slide(self) -> object:
        """Add a blank slide with the diagram background and make it current."""
        self.slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        fill = self.slide.background.fill
        fill.solid()
        fill.fore_color.rgb = rgb(self.background)
        self.pages.append([])
        return self.slide

    def save(self, path: str | Path) -> Path:
        """Write the deck and return its path."""
        path = Path(path)
        self.prs.save(str(path))
        return path

    # -- shapes --

    def _rect(
        self,
        kind: str,
        x: float,
        y: float,
        w: float,
        h: float,
        radius: float,
        role: str = "node",
        shape_type: MSO_SHAPE = MSO_SHAPE.ROUNDED_RECTANGLE,
    ) -> Node:
        shape = self.slide.shapes.add_shape(shape_type, px(x), px(y), px(w), px(h))
        _strip_style(shape)
        if shape_type == MSO_SHAPE.ROUNDED_RECTANGLE:
            shape.adjustments[0] = _round_adj(radius, w, h)
        shape.name = f"{kind} {len(self.items) + 1}"
        node = Node(kind, x, y, w, h, shape, role)
        self.items.append(node)
        return node

    def _text(
        self,
        kind: str,
        x: float,
        y: float,
        w: float,
        h: float,
        runs: Sequence[Run],
        role: str = "text",
        **fmt: object,
    ) -> Node:
        shape = self.slide.shapes.add_textbox(px(x), px(y), px(w), px(h))
        shape.name = f"{kind} {len(self.items) + 1}"
        _write_text(shape, runs, **fmt)  # type: ignore[arg-type]
        node = Node(kind, x, y, w, h, shape, role)
        node.text = [(r.text, r.size, r.font) for r in runs]
        self.items.append(node)
        return node

    def zone(
        self, x: float, y: float, w: float, h: float, label: str, kind: str = "external"
    ) -> Node:
        """Tinted zone (external, internal, repo) or an unfilled gate fence.

        The label is upper-cased and set top-left, 16px in and 13px down;
        a fence puts it bottom-left. Draw a fence after the zones it crosses.
        """
        fill, stroke, width, dash = ZONES[kind]
        role = "fence" if kind == "fence" else "container"
        node = self._rect(f"zone-{kind}", x, y, w, h, ZONE_RADIUS, role)
        _style_fill(node.shape, fill)
        _style_line(node.shape, stroke, width, dash)
        anchor = "bottom" if kind == "fence" else "top"
        inset = (
            (INSET, 0, 8, LABEL_INSET_V)
            if kind == "fence"
            else (INSET, LABEL_INSET_V, 8, 0)
        )
        _write_text(
            node.shape, [_zone_label(label.upper())], anchor=anchor, inset=inset
        )
        node.text = [(label.upper(), LABEL_PX, SANS)]
        return node

    def group(self, x: float, y: float, w: float, h: float, label: str) -> Node:
        """White group inside a zone (a cluster, a namespace), 8px radius."""
        node = self._rect("group", x, y, w, h, GROUP_RADIUS, "container")
        _style_fill(node.shape, "panel")
        _style_line(node.shape, "line", 1)
        _write_text(
            node.shape,
            [_zone_label(label.upper())],
            anchor="top",
            inset=(INSET, LABEL_INSET_V, 8, 0),
        )
        node.text = [(label.upper(), LABEL_PX, SANS)]
        return node

    def box(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        sub: str | None = None,
        code: str | None = None,
        kind: str = "plain",
    ) -> Node:
        """Component box (plain, secret/deny, gate), 6px radius, text 16px in.

        Give either ``sub`` (a muted subtitle under the title) or ``code``
        (a Mono line 30px below the box top; the title moves to the top).
        """
        stroke, width = BOXES[kind]
        node = self._rect(f"box-{kind}", x, y, w, h, BOX_RADIUS)
        _style_fill(node.shape, "panel")
        _style_line(node.shape, stroke, width)
        if code is None:
            runs = _title_runs(title, sub)
            _write_text(node.shape, runs, inset=(INSET, 0, 8, 0))
        else:
            runs = _title_runs(title, None)
            _write_text(node.shape, runs, anchor="top", inset=(INSET, 12, 8, 0))
            self._text(
                "code",
                x,
                y + 30,
                w,
                20,
                [Run(code, CODE_PX, "muted", MONO)],
                role="inner",
                inset=(INSET, 0, 8, 0),
                wrap=False,
            )
        node.text = [(r.text, r.size, r.font) for r in runs]
        return node

    def chip(
        self, x: float, y: float, w: float, label: str, kind: str = "plain"
    ) -> Node:
        """Topic / queue chip: 30px high, 4px radius, 11px Mono, centred."""
        color = CHIPS[kind]
        node = self._rect(f"chip-{kind}", x, y, w, CHIP_H, CHIP_RADIUS)
        _style_fill(node.shape, "panel")
        _style_line(node.shape, "line" if kind == "plain" else color, 1)
        runs = [Run(label, CODE_PX, color, MONO)]
        _write_text(node.shape, runs, align="center", inset=(4, 0, 4, 0), wrap=False)
        node.text = [(label, CODE_PX, MONO)]
        return node

    def store(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        sub: str | None = None,
        kind: str = "plain",
    ) -> Node:
        """Data store cylinder (plain or secret), title and subtitle centred."""
        stroke, width = STORES[kind]
        node = self._rect(f"store-{kind}", x, y, w, h, 0, shape_type=MSO_SHAPE.CAN)
        node.shape.adjustments[0] = min(0.5, STORE_CAP / min(w, h))
        _style_fill(node.shape, "panel")
        _style_line(node.shape, stroke, width)
        runs = _title_runs(title, sub)
        _write_text(node.shape, runs, align="center", inset=(8, 0, 8, 0))
        node.text = [(r.text, r.size, r.font) for r in runs]
        return node

    def person(
        self, x: float, y: float, w: float, h: float, title: str, sub: str | None = None
    ) -> Node:
        """User or role as a pill (C4 person), title and subtitle centred."""
        node = self._rect("person", x, y, w, h, min(w, h) / 2)
        _style_fill(node.shape, "panel")
        _style_line(node.shape, "line", 1.2)
        runs = _title_runs(title, sub)
        _write_text(node.shape, runs, align="center", inset=(h / 4, 0, h / 4, 0))
        node.text = [(r.text, r.size, r.font) for r in runs]
        return node

    def title(self, x: float, y: float, w: float, text: str, h: float = 30) -> Node:
        """Diagram title: 18px IBM Plex Sans Condensed, bold, fg."""
        runs = [Run(text, HEADING_PX, "fg", CONDENSED, bold=True)]
        return self._text("title", x, y, w, h, runs, wrap=False)

    def note(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        text: str,
        color: str = "gate",
        mono: bool = False,
        align: str = "left",
    ) -> Node:
        """Free note: 11.5px Sans in ``color``, or 11px Mono muted when ``mono``."""
        run = Run(text, CODE_PX, "muted", MONO) if mono else Run(text, SUB_PX, color)
        return self._text("note", x, y, w, h, [run], align=align)

    # -- edges --

    def edge(
        self,
        points: Sequence[Point],
        kind: str = "default",
        is_async: bool = False,
        two_way: bool = False,
        label: str | None = None,
        label_at: Point | None = None,
        label_segment: int = 0,
        mono_label: bool = False,
    ) -> Edge:
        """Straight or orthogonal edge through explicit px waypoints.

        The arrowhead sits on the last point; ``two_way`` adds one on the
        first. ``is_async`` dashes the line 4 3. There is no routing: give
        the anchor points (``node.right()`` etc.) and every corner.

        The label is a text box in the edge colour: above the middle of
        ``label_segment`` when it is horizontal, 6px to the right when it
        is vertical, or with its top-left at ``label_at``.
        """
        if len(points) < 2:
            raise ValueError("an edge needs at least two points")
        if label and not 0 <= label_segment < len(points) - 1:
            raise ValueError(
                f"label_segment {label_segment} out of range "
                f"for {len(points) - 1} segments"
            )
        color, width = EDGES[kind]
        shape = self._polyline(points)
        _style_fill(shape, None)
        _style_line(
            shape, color, width, ASYNC_DASH if is_async else None, two_way, True
        )
        shape.name = f"edge-{kind} {len(self.items) + 1}"
        edge = Edge(kind, [tuple(p) for p in points], shape)
        self.items.append(edge)
        if label:
            edge.label = self._edge_label(
                points, label, color, label_at, label_segment, mono_label
            )
        return edge

    def _polyline(self, points: Sequence[Point]) -> object:
        x0, y0 = points[0]
        builder = self.slide.shapes.build_freeform(px(x0), px(y0), scale=1.0)
        builder.add_line_segments([(px(x), px(y)) for x, y in points[1:]], close=False)
        shape = builder.convert_to_shape()
        _strip_style(shape)
        return shape

    def _edge_label(
        self,
        points: Sequence[Point],
        text: str,
        color: str,
        label_at: Point | None,
        segment: int,
        mono: bool,
    ) -> Node:
        run = (
            Run(text, CODE_PX, "muted", MONO)
            if mono
            else Run(text, EDGE_LABEL_PX, color)
        )
        w = _snap_up(_label_width(text, run.size, run.font) + 4)
        h = 16.0
        (ax, ay), (bx, by) = points[segment], points[segment + 1]
        if label_at is not None:
            x, y = label_at
            align = "left"
        elif ay == by:
            x, y, align = (ax + bx) / 2 - w / 2, ay - 2 - h, "center"
        else:
            x, y, align = ax + 6, (ay + by) / 2 - h / 2, "left"
        return self._text(
            "edge-label",
            x,
            y,
            w,
            h,
            [run],
            role="label",
            align=align,
            anchor="bottom",
            wrap=False,
        )

    # -- fallback --

    def add_png(self, path: str | Path, new_slide: bool = True) -> object:
        """Place a PNG (e.g. a 2x draw.io export) full-bleed on a slide.

        A 16:9 image fills the slide edge to edge; another aspect ratio is
        fitted inside and centred, on the slide background.
        """
        if new_slide and self.items:
            self.new_slide()
        pic = self.slide.shapes.add_picture(str(path), 0, 0)
        iw, ih = pic.image.size
        sw, sh = self.prs.slide_width, self.prs.slide_height
        if abs(iw / ih - sw / sh) < 0.01:
            pic.width, pic.height = sw, sh
        else:
            scale = min(sw / iw, sh / ih)
            pic.width, pic.height = Emu(round(iw * scale)), Emu(round(ih * scale))
            pic.left = Emu((sw - pic.width) // 2)
            pic.top = Emu((sh - pic.height) // 2)
        self.items.append(Node("png", 0, 0, CANVAS_W, CANVAS_H, pic, "image"))
        return pic

    # -- QA --

    def qa(self, page: int = -1) -> list[str]:
        """Return layout problems on a slide; an empty list means clean.

        Checks the grid, the canvas bounds, overlapping boxes, text over
        boxes, boxes cut by a zone border, edges through boxes and text
        that probably does not fit. It complements, not replaces, a look
        at the rendered PNG.
        """
        return run_checks(self.pages[page])


# --- QA checks --------------------------------------------------------------------


def _overlap(a: tuple, b: tuple) -> bool:
    """True when two (x0, y0, x1, y1) boxes share interior area."""
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _inside(inner: tuple, outer: tuple) -> bool:
    return (
        inner[0] >= outer[0]
        and inner[1] >= outer[1]
        and inner[2] <= outer[2]
        and inner[3] <= outer[3]
    )


def _segment_hits(p: Point, q: Point, box: tuple) -> bool:
    """True when an axis-parallel or diagonal segment enters a box's interior."""
    x0, y0, x1, y1 = box
    steps = max(2, int(max(abs(q[0] - p[0]), abs(q[1] - p[1]))))
    for i in range(1, steps):
        t = i / steps
        x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        if x0 < x < x1 and y0 < y < y1:
            return True
    return False


def _name(node: Node) -> str:
    label = node.text[0][0] if node.text else ""
    return f"{node.kind} {label!r}" if label else node.kind


def _check_grid(items: Sequence[Node | Edge]) -> list[str]:
    issues = []
    for item in items:
        if isinstance(item, Edge):
            # The end points sit on shape anchors (a chip centre is 15px down).
            inner = item.points[1:-1]
            off = [p for p in inner if p[0] % GRID or p[1] % GRID]
            if off:
                issues.append(
                    f"edge-{item.kind}: waypoints off the {GRID}px grid {off}"
                )
        elif item.role not in ("label", "inner", "image") and any(
            v % GRID for v in (item.x, item.y, item.w, item.h)
        ):
            issues.append(f"{_name(item)}: geometry off the {GRID}px grid")
    return issues


def _check_bounds(items: Sequence[Node | Edge]) -> list[str]:
    issues = []
    canvas = (0, 0, CANVAS_W, CANVAS_H)
    for item in items:
        if isinstance(item, Edge):
            pts = item.points
            box = (
                min(p[0] for p in pts),
                min(p[1] for p in pts),
                max(p[0] for p in pts),
                max(p[1] for p in pts),
            )
            name = f"edge-{item.kind}"
        else:
            box, name = item.box, _name(item)
        if not _inside(box, canvas):
            issues.append(f"{name}: outside the {CANVAS_W}x{CANVAS_H} canvas")
    return issues


def _check_overlaps(nodes: Sequence[Node]) -> list[str]:
    issues = []
    solid = [n for n in nodes if n.role == "node"]
    texts = [n for n in nodes if n.role in ("text", "label")]
    for i, a in enumerate(solid):
        for b in solid[i + 1 :]:
            if _overlap(a.box, b.box):
                issues.append(f"{_name(a)} overlaps {_name(b)}")
    for t in texts:
        for n in solid:
            if _overlap(t.box, n.box):
                issues.append(f"{_name(t)} overlaps {_name(n)}")
    for i, a in enumerate(texts):
        for b in texts[i + 1 :]:
            if _overlap(a.box, b.box):
                issues.append(f"{_name(a)} overlaps {_name(b)}")
    return issues


def _label_band(node: Node) -> tuple[float, float, float, float]:
    """Box taken by a zone or group label (bottom-left for a fence)."""
    text, size, font = node.text[0]
    x1 = node.x + INSET + _label_width(text, size, font)
    if node.role == "fence":
        return (node.x, node.y + node.h - 30, x1, node.y + node.h)
    return (node.x, node.y, x1, node.y + 30)


def _check_containers(nodes: Sequence[Node]) -> list[str]:
    issues = []
    walls = [n for n in nodes if n.role in ("container", "fence")]
    for n in nodes:
        if n.role in ("inner", "image"):
            continue
        for c in walls:
            if c is n or (c.role == "fence" and n.role in ("node", "container")):
                continue
            if (
                _overlap(n.box, c.box)
                and not _inside(n.box, c.box)
                and not _inside(c.box, n.box)
            ):
                issues.append(f"{_name(n)} is cut by the border of {_name(c)}")
    for c in walls:
        if not c.text:
            continue
        band = _label_band(c)
        for n in nodes:
            if (
                n is not c
                and n.role in ("node", "container", "text", "label")
                and _overlap(band, n.box)
                and not _inside(c.box, n.box)
            ):
                issues.append(f"{_name(n)} covers the label of {_name(c)}")
    return issues


def _check_edges(items: Sequence[Node | Edge]) -> list[str]:
    issues = []
    solid = [n for n in items if isinstance(n, Node) and n.role == "node"]
    for edge in (e for e in items if isinstance(e, Edge)):
        for p, q in zip(edge.points, edge.points[1:]):
            for n in solid:
                if _segment_hits(p, q, n.box):
                    issues.append(f"edge-{edge.kind} {p}->{q} runs through {_name(n)}")
    return issues


def _text_room(node: Node) -> float:
    """Width available to text inside a node, after its insets."""
    if node.kind.startswith("chip"):
        return node.w - 8
    if node.kind == "person":
        return node.w - node.h / 2
    if node.kind.startswith("store"):
        return node.w - 16
    if node.role in ("text", "label"):
        return node.w
    return node.w - INSET - 8


def _check_text_fit(nodes: Sequence[Node]) -> list[str]:
    issues = []
    for n in nodes:
        if n.role == "image":
            continue
        room = _text_room(n)
        for text, size, font in n.text:
            need = _label_width(text, size, font)
            if need > room:
                issues.append(
                    f"{_name(n)}: {text!r} needs ~{need:.0f}px, has {room:.0f}px"
                )
    return issues


def run_checks(items: Sequence[Node | Edge]) -> list[str]:
    """Run every layout check over one slide's elements."""
    nodes = [i for i in items if isinstance(i, Node)]
    return [
        *_check_grid(items),
        *_check_bounds(items),
        *_check_overlaps(nodes),
        *_check_containers(nodes),
        *_check_edges(items),
        *_check_text_fit(nodes),
    ]
