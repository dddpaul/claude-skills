#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "python-pptx>=1.0.2",
# ]
# ///
"""Dump one slide of a .pptx as a readable list of shapes.

Where ``compare_decks.py`` answers "how do these two decks differ", this
answers "what exactly is on this slide" — the frame, fill, line, wrap and text
by run, with the numbers spelled out in both EMU and inches. Use it to read
exact values off a hand-made reference before encoding them in a generator.

The shape model is the one ``compare_decks.py`` already builds, imported here
as a plain module (the scripts are named with underscores precisely so this
import needs no loader gymnastics).

Usage:
    uv run dump_slide.py DECK.pptx N

``N`` is 1-based, matching the slide numbering shown in PowerPoint.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import compare_decks
from compare_decks import EMU_PER_INCH, Shape


def _dim(value: int | None) -> str:
    if value is None:
        return "-"
    return f"{value} EMU ({value / EMU_PER_INCH:.3f}in)"


def format_shape(shape: Shape) -> list[str]:
    """One shape as indented, human-readable lines."""
    lines = [f"[{shape.index}] {shape.kind} name={shape.name!r}"]
    if shape.geom:
        lines.append(f"    geom:  {shape.geom}")
    lines.append(f"    x:     {_dim(shape.x)}")
    lines.append(f"    y:     {_dim(shape.y)}")
    lines.append(f"    w:     {_dim(shape.w)}")
    lines.append(f"    h:     {_dim(shape.h)}")
    if shape.rotation:
        lines.append(f"    rot:   {shape.rotation}")
    lines.append(f"    fill:  {shape.fill or '-'}")
    line = shape.line or "-"
    if shape.line_width_pt is not None:
        line = f"{line} {shape.line_width_pt}pt"
    lines.append(f"    line:  {line}")
    if shape.word_wrap is not None:
        lines.append(f"    wrap:  {shape.word_wrap}")

    for i, para in enumerate(shape.paras):
        head = f"    para[{i}] level={para.level}"
        if para.alignment:
            head += f" align={para.alignment}"
        if para.margin_left_pt is not None:
            head += f" left={para.margin_left_pt}pt"
        if para.indent_pt is not None:
            head += f" indent={para.indent_pt}pt"
        if para.space_before_pt is not None:
            head += f" before={para.space_before_pt}pt"
        if para.space_after_pt is not None:
            head += f" after={para.space_after_pt}pt"
        lines.append(head)
        for j, run in enumerate(para.runs):
            attrs = [
                f"font={run.font!r}" if run.font else "",
                f"size={run.size_pt}pt" if run.size_pt is not None else "",
                "bold" if run.bold else "",
                "italic" if run.italic else "",
                "underline" if run.underline else "",
                f"color={run.color}" if run.color else "",
            ]
            suffix = " ".join(a for a in attrs if a)
            tail = f"  {suffix}" if suffix else ""
            lines.append(f"        run[{j}] {run.text!r}{tail}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dump one slide of a .pptx as a readable list of shapes.",
    )
    parser.add_argument("deck", type=Path, metavar="DECK.pptx")
    parser.add_argument("number", type=int, metavar="N", help="1-based slide number")
    args = parser.parse_args(argv)

    if not args.deck.exists():
        print(f"no such deck: {args.deck}", file=sys.stderr)
        return 2

    slides = compare_decks.parse_deck(args.deck)
    if not 1 <= args.number <= len(slides):
        print(
            f"slide {args.number} out of range: {args.deck.name} has {len(slides)}",
            file=sys.stderr,
        )
        return 2

    shapes = slides[args.number - 1]
    print(f"{args.deck.name} slide {args.number}/{len(slides)}: {len(shapes)} shapes")
    for shape in shapes:
        print()
        for line in format_shape(shape):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
