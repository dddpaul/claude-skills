---
name: pptx-compare
description: Compare two PPTX decks — structurally (shape by shape, with exact EMU/point numbers), by rendered pixels, or by dumping a single slide. Apply when aligning a deck generator against a hand-made reference, when checking a rebuilt deck against the previously committed one for regressions, or when reading exact values off someone else's slide. Triggers on requests to compare, diff or verify presentations, or when told to use "pptx-compare".
---

# PPTX Deck Comparison

Three scripts that measure the gap between two decks. They are diagnostic and opinion-free: they parse
any two `.pptx` files and consider neither of them correct. Nothing here encodes a house style — for
that, see the sibling `pptx-arch-style` skill.

## When to apply

1. **Aligning a generator against a manual reference.** Someone hand-built a deck in PowerPoint and you
   are writing code to reproduce it. Run the structural comparison after every generator change to see
   what still differs, and `dump_slide.py` on the reference to read the exact numbers to encode.
2. **Regression-checking a rebuild.** Compare the previously committed `.pptx` against a freshly built
   one. Anything the comparison reports that you did not intend to change is a regression.
3. **Reading exact values off a foreign slide.** `dump_slide.py` prints one slide as frames, fills,
   lines, wrap and text by run, in EMU and inches — faster and more exact than clicking through the
   PowerPoint inspector.

## Boundary: this skill measures, it does not fix

The comparison reports the gap between two decks. It **does not edit the generator, rewrite a deck, or
propose a patch** — closing the loop is the caller's job. The scripts read both files and write only
their report and, with `--render`, their images. Expect to run compare → change the generator → rebuild
→ compare again, several times; the skill is the measuring instrument in that loop, not the loop.

## Skill independence

**The plugin's skills are mutually independent; the consumer does the wiring.** `pptx-compare` must not
call `lint.py` or `postprocess-effectlst.py` from `pptx-arch-style`, and `pptx-arch-style` must not call
anything here. A build pipeline that wants generate → post-process → lint → compare assembles those
four steps itself.

The temptation is to have the comparison run the style check too, "for completeness". Resist it: that
would tie the two skills' versions together and stop the plugin from updating them piecemeal. The two
differ in nature — `pptx-arch-style` is **normative** (`references/rules.yaml` plus a conformance
check, with a verdict), `pptx-compare` is **diagnostic** (two decks in, a list of differences out, no
verdict).

## Scripts

### `scripts/compare_decks.py` — structural comparison

```
uv run scripts/compare_decks.py REF.pptx GEN.pptx [--pos-tol INCHES]
                                [--render] [--dpi N] [--outdir DIR] [--report FILE]
```

For every slide it captures each shape — text by run, font face, size, weight/style, colour, fill,
outline, alignment, indents, and the x/y/w/h frame in EMU — matches the shapes of the two decks by a
pair cost (text similarity, geometric distance, shape kind), and prints the discrepancies per slide.
Shapes that match nothing on the other side are reported as `only in ref` / `only in gen` rather than
force-fitted into a misleading diff.

- `--pos-tol INCHES` — coordinate slack; x/y/w/h deltas at or below it are not reported. Default
  0.040in. A different generator pair needs a different value: widen it until engine rounding stops
  showing, then leave it there so real drift still surfaces.
- `--render` — additionally rasterise both decks (see below).
- `--report FILE` — write the same text to a file as well as stdout.

Exit codes: `0` decks match within tolerance, `1` at least one discrepancy, `2` not comparable (slide
counts differ, or a render failed).

### `scripts/dump_slide.py` — read one slide

```
uv run scripts/dump_slide.py DECK.pptx N
```

`N` is 1-based, matching PowerPoint's own numbering. Prints frame, fill, line, wrap and text by run for
every shape, each dimension in both EMU and inches. It imports `compare_decks` as a plain module and
shares its shape model, so what you read here is exactly what the comparison compares.

### `scripts/pixel_diff.py` — compare renders

```
uv run scripts/pixel_diff.py REF_DIR GEN_DIR --outdir DIR
                             [--threshold N] [--max-diff FRACTION]
                             [--zoom N:LEFT,TOP,RIGHT,BOTTOM]
```

Takes two folders of PNGs, reports the fraction of differing pixels per page, writes an overlay with
the differing pixels highlighted in red, and tiles those overlays into one contact sheet.
`--zoom N:LEFT,TOP,RIGHT,BOTTOM` crops page `N` of ref, gen and overlay to a region for a close look.

This script knows nothing about pptx — it works on any two folders of identically-sized images. Feed it
the output of `compare_decks.py --render`, which puts both decks through one shared dpi so the pages
line up.

## External dependencies

| Tool | Needed for | Notes |
|------|-----------|-------|
| `soffice` (LibreOffice) | `compare_decks.py --render` | `.pptx` → `.pdf`; nothing else uses it |
| `pdftoppm` (poppler-utils) | `compare_decks.py --render` | `.pdf` → one PNG per page at `--dpi` |
| `pillow` | `pixel_diff.py` | declared in the script's PEP 723 header |
| `python-pptx` | `compare_decks.py`, `dump_slide.py` | declared in the scripts' PEP 723 headers |

The structural comparison and the slide dump need **only** `python-pptx` — no LibreOffice, no Node. If
`soffice` or `pdftoppm` is missing, `--render` fails with a clear message and the structural comparison
still runs.

## Sandbox caveat

`--render` shells out to LibreOffice, which writes a user profile and temporary files. Under a sandbox
that only permits writes inside the repository, point `--outdir` at a directory **inside the repository**
(and git-ignore it) or disable the sandbox for that command. `--outdir` has no default beside the
script — the skill lives in a read-only plugin cache — and falls back to `./_compare_out` under the
current working directory.

## Reading the output

Not every reported discrepancy is a defect. When the two decks come from different engines — a
PowerPoint-authored reference against a pptxgenjs-generated deck — some differences are structural
artefacts of the engine pair and will never go away, no matter how the generator is written. Before
chasing a discrepancy, check it against `references/engine-differences.md`, which lists the four known
ones.

## Known limitation: groups are opaque

**A grouped shape is compared as one shape; its contents are not inspected.** The parse walks the
top-level shape tree of each slide, so a `p:grpSp` contributes its own name and frame and nothing else —
two decks whose groups hold entirely different text can still be reported as `OK`. Grouping is idiomatic
in hand-built PowerPoint decks, which is exactly use case 1 above, so **do not read a clean structural
report as proof that two decks match** until you know neither contains groups.

Two ways round it: ungroup in the reference before comparing, or fall back on `--render` plus
`pixel_diff.py`, which sees the rendered result and so is blind to how shapes are nested.

## Typical loop

```
uv run scripts/compare_decks.py ref.pptx gen.pptx --report compare.md
# fix the generator, rebuild gen.pptx, repeat until only known engine artefacts remain

uv run scripts/compare_decks.py ref.pptx gen.pptx --render --dpi 144 --outdir ./_cmp
uv run scripts/pixel_diff.py ./_cmp/ref ./_cmp/gen --outdir ./_cmp/diff
# open ./_cmp/diff/contact-sheet.png, then --zoom into whatever looks wrong
```

Fixture decks under `scripts/tests/fixtures/` are regenerable with
`uv run scripts/tests/gen_fixtures.py`.
