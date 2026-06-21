---
name: pdf
description: Convert a markdown file to a PDF rendered with weasyprint, IBM Plex typography, and Obsidian-style heading anchors. Conversion-only — no upload, no transport. Triggers (EN) "convert to pdf", "render as pdf", "md to pdf"; triggers (RU) "сделай pdf", "сконвертируй в pdf", "из markdown в pdf".
---

# pdf

Conversion-only skill: takes a markdown file and produces a PDF next to it (or
at a caller-supplied path). Stylesheet lives in `references/styles.css` and is
applied via weasyprint. Heading ids match Obsidian's slugify convention so an
internal `[text](#anchor)` link that navigates correctly inside Obsidian
navigates correctly in the rendered PDF.

This skill is a leaf: it does **no** upload, no transport, no provider plumbing.
Sibling skills (e.g. `publish`) shell out to its script when they need a PDF.

## Interface

```bash
uv run plugins/publish/skills/pdf/scripts/md-to-pdf.py <source.md> [<target.pdf>]
```

- `<source.md>` is required. **Hard-fail if the extension is not `.md`** —
  PDF/EPUB/anything-else inputs are out of scope.
- `<target.pdf>` is optional. When omitted, the script writes
  `<source-dir>/<source-stem>.pdf` alongside the source.
- Write is atomic: the script renders to a hidden `.<target>.tmp` next to the
  final path, then `os.replace`s it into place so partial files never appear.
- The script prints the absolute target path to stdout on success.

## Triggers

- EN: "convert to pdf", "render as pdf", "md to pdf"
- RU: "сделай pdf", "сконвертируй в pdf", "из markdown в pdf"

## PDF layout

`references/styles.css` produces the default layout:

- Page size: **A4 portrait**.
- Margins: **20mm symmetric** on all sides.
- Line height: **1.25** — tight academic rhythm, room for underlines but
  not loose.
- Font: `'IBM Plex Serif', 'PT Serif', 'Apple Color Emoji', 'Times New Roman', serif`,
  11pt body, with `font-variant-numeric: lining-nums` so digits sit on the
  baseline; 18/15/13 pt for H1/H2/H3.
- Code: `'IBM Plex Mono', Menlo, Consolas, monospace`, 10pt, light-grey
  background. No syntax highlighting.
- Links: underlined, blue (`#0050b3`).
- Images: `max-width: 100%`.
- Page breaks: `h1, h2 { page-break-before: auto; break-inside: avoid; }` to
  prevent orphan headings.

CSS lives in `references/` so the user can override without touching the
script.

## Anchors

Heading anchors follow Obsidian's exact-text convention so a markdown doc that
navigates correctly in Obsidian also navigates correctly in the rendered PDF.
Both the heading `id` and the link fragment pass through a single
`obsidian_slugify` (in `scripts/md-to-pdf.py`):

- Case-folded (lowercase)
- Whitespace runs collapsed to a single `-`
- Cyrillic letters, dots, em-dashes, and slashes preserved verbatim

Authors write the link in either CommonMark spelling — bare or
angle-bracketed for fragments containing whitespace:

```markdown
[§3.2](#3.2 Camunda — соседняя ИС вне периметра ПФ)
[§3.2](<#3.2 Camunda — соседняя ИС вне периметра ПФ>)
```

Both normalize to the same id. No `{#explicit-id}` annotations on the
heading are required — the heading text alone is the anchor.

## Dependencies

The skill needs both the `markdown` and `weasyprint` Python packages, plus
their native dependencies on macOS.

Python packages — installed via `uv` in the repo root:

```bash
uv add weasyprint markdown
```

macOS system prerequisites — install via Homebrew **before** the first
conversion, or weasyprint will fail to render with a cryptic Cairo/Pango
error:

```bash
brew install cairo pango gdk-pixbuf
brew install --cask font-ibm-plex
```

The cairo/pango/gdk-pixbuf trio are runtime dependencies for weasyprint's PDF
rendering pipeline. `font-ibm-plex` installs the IBM Plex Serif / Mono families
used by the default stylesheet; without them weasyprint falls back to PT Serif
or Times New Roman.
