---
title: Books PDF restyle — design
date: 2026-06-14
status: ready-for-tasks
---

# Books PDF restyle — design

## Problem

The `reading/books` skill renders Markdown → PDF via weasyprint with a minimal CSS
in `plugins/reading/skills/books/references/styles.css`. Two concrete issues
surfaced when reading a real document:

1. A wide table overflows the page right margin.
2. The visual style is bare — full grid table borders, gray header fill, no
   page numbers, no TOC. The user provided a reference PDF
   (`~/Downloads/doc_6_*.pdf`) showing a cleaner academic look with horizontal
   table rules, justified body, footer page numbers, and a TOC with dot
   leaders and page references.

## Scope of this redesign

Land an end-to-end restyle in one task:

- **Page geometry**: margin `15mm 15mm 15mm 20mm` (T/R/B/L), centered footer
  page number via `@bottom-center { content: counter(page); }`.
- **Body**: `text-align: justify`.
- **Tables**: drop full grid borders, keep only top + header-underline + bottom
  rules; drop header gray fill; bump cell padding to `6px 10px`; add
  `font-size: 10pt` and `overflow-wrap: break-word` so long tables fit.
- **TOC**: auto-injected `<nav class="toc">` listing H1 + H2 with dot leaders
  and target page numbers. Hardcoded heading label "Contents". Flows
  naturally (no forced page break). Always emitted (no opt-in).
- **Heading numbering**: NOT auto-numbered — markdown text is rendered verbatim
  so manually-numbered headings (e.g. "1. Контекст") stay as authored.

Out of scope:

- Re-rendering existing books. User will re-render manually when next reading.
- Author-facing TOC opt-out (always on).
- Localized "Contents" label (always English).

## Implementation outline

### `plugins/reading/skills/books/scripts/md-to-pdf.py`

Switch from a single `markdown.markdown(...)` call to a `markdown.Markdown`
instance so we can read `.toc` after conversion:

```python
md = markdown.Markdown(extensions=["fenced_code", "tables", "toc"])
html_body = md.convert(raw)
toc_html = md.toc  # populated by the toc extension; includes anchors to heading ids
```

The `toc` extension adds an `id` to each heading and exposes a nested `<ul>`
in `md.toc`. We don't use the extension's default markup as-is — we want
only H1 + H2 levels, no H3+. Configure with `toc_depth="1-2"` (extension
supports this kwarg as `toc_depth` since markdown 3.0).

Inject the TOC at the top of the body:

```python
toc_section = (
    f'<nav class="toc"><h2 class="toc-title">Contents</h2>{toc_html}</nav>'
    if toc_html else ""
)
html_doc = (
    '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
    f'<body>{toc_section}{html_body}</body></html>'
)
```

Note: `md.toc` already wraps in `<div class="toc">…</div>` by default. We
strip or override that by setting `toc_class=""` and our own outer `<nav>`,
or simpler — just keep the div, target via `nav.toc div.toc` in CSS. Final
decision deferred to implementer; either works.

### `plugins/reading/skills/books/references/styles.css`

Final file:

```css
@page {
  size: A4 portrait;
  margin: 15mm 15mm 15mm 20mm;
  @bottom-center { content: counter(page); font-family: Georgia, serif; font-size: 10pt; }
}
body { font-family: Georgia, 'Times New Roman', serif; font-size: 12pt; line-height: 1.4; text-align: justify; }
h1 { font-size: 18pt; page-break-before: auto; break-inside: avoid; }
h2 { font-size: 15pt; page-break-before: auto; break-inside: avoid; }
h3 { font-size: 13pt; break-inside: avoid; }
code, pre { font-family: Menlo, Consolas, monospace; font-size: 10pt; background: #f0f0f0; }
pre { padding: 8px; }
a { color: black; text-decoration: underline; }
img { max-width: 100%; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 10pt; border-top: 1px solid #333; border-bottom: 1px solid #333; }
th, td { padding: 6px 10px; text-align: left; vertical-align: top; overflow-wrap: break-word; }
th { border-bottom: 1px solid #333; font-weight: bold; }

nav.toc { margin: 0 0 16pt 0; }
nav.toc .toc-title { font-size: 15pt; margin: 0 0 8pt 0; }
nav.toc ul { list-style: none; padding-left: 0; margin: 0; }
nav.toc ul ul { padding-left: 16pt; }
nav.toc li { display: flex; align-items: baseline; gap: 4pt; }
nav.toc li a { text-decoration: none; color: black; flex: 0 1 auto; }
nav.toc li::after {
  content: target-counter(attr(data-href url), page);
  margin-left: auto;
}
nav.toc li {
  background-image: radial-gradient(circle, currentColor 0.4pt, transparent 0.4pt);
  background-position: bottom 3pt left;
  background-size: 4pt 4pt;
  background-repeat: repeat-x;
}
```

#### Dot-leader technique

Two viable approaches:

1. `content: leader('.') target-counter(...)` — clean, but weasyprint's
   `leader()` support is partial; falls back to a literal `'.'` token in
   some cases.
2. `background: radial-gradient(...)` repeating bottom-aligned dots, with
   `a` and `::after` floated to opposite sides. Slightly verbose but renders
   consistently in current weasyprint.

The CSS above uses approach 2 as the safer default. If `leader()` proves
clean during the verification render, the implementer may swap to approach 1.

#### The `data-href` hack

`target-counter()` requires a URL reference. The markdown `toc` extension
emits `<a href="#slug">` — but CSS `attr(href, url)` from a child element
isn't accessible to a parent's `::after`. Two workarounds:

- Move the `::after` onto the `<a>` itself: `nav.toc a::after { content: target-counter(attr(href, url), page); }`.
  Simplest and standards-correct. Preferred.
- Duplicate the href onto the `<li data-href="#slug">` (requires HTML
  rewrite in md-to-pdf.py to walk the toc HTML and copy hrefs up).

**Preferred**: put `::after` on the anchor. Update the CSS block accordingly
during implementation — the design doc's draft above used the `data-href`
form for layout reasons (so the dot row sits on the `<li>` not the `<a>`);
the implementer should reconcile by either keeping dots on `<li>` (need
data-href copy) or moving everything to `<a>` (no copy needed, but dot
background lives on the anchor).

### `plugins/reading/.claude-plugin/plugin.json`

Bump `version` field one minor level — this adds a new feature (TOC) plus
broadens the rendering surface, so per the CLAUDE.md rule "minor for new
skills or broadened triggers" minor is appropriate. (Patch would also be
defensible since the skill itself isn't new; minor errs on the side of
"clearly noticeable visual change for users".)

## Verification

Render a markdown file containing:

- Multiple H1 and H2 sections (verify TOC entries appear and link).
- One wide table that previously overflowed (verify it now fits within the
  page width).
- At least 3 pages of content (verify footer page numbers increment).
- A Russian paragraph (verify justified text doesn't mangle Cyrillic).

Inspect the resulting PDF visually and confirm:

- TOC heading reads "Contents", H1+H2 entries present, dot leaders
  visible, page numbers correct.
- Body paragraphs are right-aligned (justified).
- Tables show only horizontal rules.
- Bottom-center page number on every page.

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| weasyprint `target-counter()` doesn't resolve | low | Documented & supported feature; if it fails, fallback is hardcoded page numbers via Python post-render (much worse, but possible). |
| `leader()` not supported → ugly dots | medium | Design specifies the radial-gradient fallback up front. |
| `toc` extension emits H3+ even when `toc_depth="1-2"` | low | Filter in Python after `md.convert()` if needed. |
| Justified body causes ugly word spacing in narrow columns | low | Body is full width; columns aren't used. |
| Existing book PDFs in `~/iCloud Drive/.../reading/` look inconsistent until re-rendered | acknowledged | Out of scope per Phase-1 decision; user re-renders manually. |

## Hand-off

Single task. Self-contained spec inlined in the task body (do NOT reference
this design doc from inside the task — see feedback memory
`feedback_ralph_task_self_contained.md`). Task includes:

- Exact final `styles.css` content as a code block.
- Exact change set for `md-to-pdf.py` as before/after code blocks.
- Version bump rule for `plugin.json`.
- Verification steps (sample render + visual checks).
- ACs covering every concrete change + lint + tests + task-reviewer APPROVED.

Run on a `task-*` branch; merge after `task-reviewer` APPROVED.

---

## Addendum 1 — 2026-06-14: strip Obsidian-plugin TOC fences

Some markdown sources already contain an auto-generated TOC placeholder used by
the Obsidian community plugin
[`obsidian-automatic-table-of-contents`](https://github.com/johansatge/obsidian-automatic-table-of-contents).
It takes the form of a fenced code block with language `table-of-contents`:

````
```table-of-contents
```
````

…optionally with config keys inside the fence (e.g. `title:`, `style:`,
`minLevel:`, `maxLevel:`). Obsidian renders the block as a live TOC; weasyprint
sees only a literal code block and would emit the raw fence contents as junk in
the PDF.

Since md-to-pdf.py now injects its own `<nav class="toc">` from the document's
headings, the Obsidian-plugin placeholder is redundant and must be **stripped**
during preprocessing.

### Implementation

Add a second `re.sub` pass alongside the existing frontmatter strip in
`md-to-pdf.py`. Match the full fence span, multi-line, including the optional
config body and trailing newline:

```python
raw = re.sub(
    r"^```table-of-contents\b.*?^```\s*\n?",
    "",
    raw,
    flags=re.DOTALL | re.MULTILINE,
)
```

Place this immediately after the frontmatter strip and before
`markdown.Markdown(...).convert(raw)`.

### Verification

Add to the verification sample md (Phase 3 → Verification section): include a
` ```table-of-contents``` ` block somewhere in the body and confirm the
resulting PDF shows no literal "table-of-contents" text anywhere.

### Risk

Low. Regex is anchored to the exact language fence; conflict only if a real
code block authored in markdown uses the language identifier `table-of-contents`
(extremely unlikely).
