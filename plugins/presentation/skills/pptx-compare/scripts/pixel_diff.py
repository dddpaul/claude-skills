#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pillow>=10.0",
# ]
# ///
"""Pixel-level comparison of two folders of PNGs.

For every pair of identically-named-by-position pages it reports the fraction
of differing pixels, writes an overlay with the differing pixels highlighted in
red, and assembles a contact sheet of those overlays. ``--zoom`` crops one page
to a region so a small discrepancy can be inspected at full resolution.

This script knows nothing about pptx: it works on any two folders of
identically-sized images. Pair it with ``compare_decks.py --render``, which
drives both decks through ``soffice`` and ``pdftoppm`` at one shared dpi so the
pages line up.

Usage:
    uv run pixel_diff.py REF_DIR GEN_DIR --outdir DIR
    uv run pixel_diff.py REF_DIR GEN_DIR --outdir DIR --threshold 16
    uv run pixel_diff.py REF_DIR GEN_DIR --outdir DIR --zoom 3:100,200,900,700

Exit codes:
    0 — every page is within --max-diff
    1 — at least one page exceeds it
    2 — the folders could not be compared (page count or size mismatch)
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops

HIGHLIGHT = (255, 0, 0)
CONTACT_COLUMNS = 3
CONTACT_THUMB_WIDTH = 480


@dataclass
class PageDiff:
    """The per-page result of the pixel comparison."""

    number: int
    ref: Path
    gen: Path
    differing: int
    total: int
    overlay: Path | None = None

    @property
    def fraction(self) -> float:
        return 0.0 if not self.total else self.differing / self.total


def load_pages(folder: Path) -> list[Path]:
    """Every PNG in a folder, ordered by name so page N lines up with page N."""
    return sorted(folder.glob("*.png"))


def diff_pair(
    ref_path: Path, gen_path: Path, threshold: int
) -> tuple[Image.Image, int, int]:
    """Return (overlay, differing pixels, total pixels) for one page."""
    ref = Image.open(ref_path).convert("RGB")
    gen = Image.open(gen_path).convert("RGB")
    if ref.size != gen.size:
        raise ValueError(
            f"size mismatch: {ref_path.name} {ref.size} vs {gen_path.name} {gen.size}"
        )
    delta = ImageChops.difference(ref, gen).convert("L")
    mask = delta.point(lambda v: 255 if v > threshold else 0, mode="L")
    differing = mask.histogram()[255]
    overlay = gen.copy()
    overlay.paste(Image.new("RGB", gen.size, HIGHLIGHT), mask=mask.convert("1"))
    return overlay, differing, ref.size[0] * ref.size[1]


def contact_sheet(overlays: list[Path], destination: Path) -> Path | None:
    """Tile the overlays into one sheet so a whole deck fits on screen."""
    if not overlays:
        return None
    thumbs = []
    for path in overlays:
        image = Image.open(path).convert("RGB")
        height = round(image.height * CONTACT_THUMB_WIDTH / image.width)
        thumbs.append(image.resize((CONTACT_THUMB_WIDTH, height)))
    columns = min(CONTACT_COLUMNS, len(thumbs))
    rows = (len(thumbs) + columns - 1) // columns
    cell_h = max(t.height for t in thumbs)
    sheet = Image.new(
        "RGB", (columns * CONTACT_THUMB_WIDTH, rows * cell_h), (255, 255, 255)
    )
    for i, thumb in enumerate(thumbs):
        x = (i % columns) * CONTACT_THUMB_WIDTH
        sheet.paste(thumb, (x, (i // columns) * cell_h))
    sheet.save(destination)
    return destination


def parse_zoom(spec: str) -> tuple[int, tuple[int, int, int, int]]:
    """Parse ``N:LEFT,TOP,RIGHT,BOTTOM`` into a page number and a crop box."""
    page, _, box = spec.partition(":")
    if not box:
        raise ValueError(f"--zoom wants N:LEFT,TOP,RIGHT,BOTTOM, got {spec!r}")
    edges = [int(part) for part in box.split(",")]
    if len(edges) != 4:
        raise ValueError(f"--zoom needs exactly 4 edges, got {len(edges)} in {spec!r}")
    left, top, right, bottom = edges
    if right <= left or bottom <= top:
        raise ValueError(f"--zoom box is empty: {spec!r}")
    return int(page), (left, top, right, bottom)


def write_zoom(pages: list[PageDiff], spec: str, outdir: Path) -> list[Path]:
    """Crop ref, gen and overlay of one page to the requested region."""
    number, box = parse_zoom(spec)
    match = next((p for p in pages if p.number == number), None)
    if match is None:
        raise ValueError(f"--zoom page {number} is not among the compared pages")
    written = []
    sources = [("ref", match.ref), ("gen", match.gen)]
    if match.overlay:
        sources.append(("overlay", match.overlay))
    size = Image.open(match.ref).size
    if box[0] < 0 or box[1] < 0 or box[2] > size[0] or box[3] > size[1]:
        # Image.crop pads outside the image rather than raising, so one
        # mistyped digit would otherwise write a huge mostly-empty PNG.
        raise ValueError(
            f"--zoom box {box} reaches outside page {number}, which is "
            f"{size[0]}x{size[1]}"
        )
    for tag, source in sources:
        crop = Image.open(source).convert("RGB").crop(box)
        destination = outdir / f"zoom-{number:02d}-{tag}.png"
        crop.save(destination)
        written.append(destination)
    return written


def compare_folders(
    ref_dir: Path, gen_dir: Path, outdir: Path, threshold: int
) -> list[PageDiff]:
    """Compare two folders page by page, writing one overlay per page."""
    ref_pages = load_pages(ref_dir)
    gen_pages = load_pages(gen_dir)
    if len(ref_pages) != len(gen_pages):
        raise ValueError(
            f"page count differs: {ref_dir} has {len(ref_pages)}, "
            f"{gen_dir} has {len(gen_pages)}"
        )
    outdir.mkdir(parents=True, exist_ok=True)
    results = []
    for number, (ref_path, gen_path) in enumerate(zip(ref_pages, gen_pages), start=1):
        overlay, differing, total = diff_pair(ref_path, gen_path, threshold)
        destination = outdir / f"overlay-{number:02d}.png"
        overlay.save(destination)
        results.append(
            PageDiff(
                number=number,
                ref=ref_path,
                gen=gen_path,
                differing=differing,
                total=total,
                overlay=destination,
            )
        )
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pixel-compare two folders of identically-sized PNGs.",
    )
    parser.add_argument("ref_dir", type=Path, metavar="REF_DIR")
    parser.add_argument("gen_dir", type=Path, metavar="GEN_DIR")
    parser.add_argument(
        "--outdir",
        type=Path,
        required=True,
        metavar="DIR",
        help="where overlays, the contact sheet and any zoom crops are written",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=8,
        help="per-channel delta a pixel must exceed to count (default: %(default)s)",
    )
    parser.add_argument(
        "--max-diff",
        type=float,
        default=0.0,
        metavar="FRACTION",
        help="fraction of differing pixels tolerated per page (default: %(default)s)",
    )
    parser.add_argument(
        "--zoom",
        default=None,
        metavar="N:LEFT,TOP,RIGHT,BOTTOM",
        help="also crop page N of ref, gen and overlay to this box",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for folder in (args.ref_dir, args.gen_dir):
        if not folder.is_dir():
            print(f"no such folder: {folder}", file=sys.stderr)
            return 2

    try:
        pages = compare_folders(
            args.ref_dir, args.gen_dir, args.outdir, args.threshold
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not pages:
        print(f"no PNGs to compare in {args.ref_dir}", file=sys.stderr)
        return 2

    worst = 0.0
    for page in pages:
        worst = max(worst, page.fraction)
        print(
            f"page {page.number:>2}: {page.fraction * 100:6.3f}% differing "
            f"({page.differing}/{page.total})  -> {page.overlay}"
        )

    overlays = [p.overlay for p in pages if p.overlay]
    sheet = contact_sheet(overlays, args.outdir / "contact-sheet.png")
    if sheet:
        print(f"contact sheet: {sheet}")

    if args.zoom:
        try:
            for path in write_zoom(pages, args.zoom, args.outdir):
                print(f"zoom: {path}")
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    return 0 if worst <= args.max_diff else 1


if __name__ == "__main__":
    raise SystemExit(main())
