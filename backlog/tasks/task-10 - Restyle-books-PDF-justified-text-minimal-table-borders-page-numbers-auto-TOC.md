---
id: TASK-10
title: >-
  Restyle books PDF: justified text, minimal table borders, page numbers, auto
  TOC
status: To Do
assignee: []
created_date: '2026-06-14 17:57'
updated_date: '2026-06-14 18:06'
labels: []
dependencies: []
priority: high
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The books skill (plugins/reading/skills/books) renders Markdown to PDF via weasyprint. Current output has overflowing tables, full grid borders, no page numbers, and no TOC. Bring it closer to a clean academic style: justified body, minimal table rules, footer page numbers, auto-injected TOC with dot leaders + page references. Also strip the Obsidian community plugin TOC placeholder fenced block (a code fence whose language is `table-of-contents`) so it does not render as a literal code block in the PDF.

## Files to change

- `plugins/reading/skills/books/scripts/md-to-pdf.py`
- `plugins/reading/skills/books/references/styles.css`
- `plugins/reading/.claude-plugin/plugin.json`

## Change 1 — md-to-pdf.py preprocessing

Add a second `re.sub` pass right after the existing frontmatter strip and before the markdown converter is called. It removes fenced code blocks whose language identifier is `table-of-contents`. Use the following regex (apply with `flags=re.DOTALL | re.MULTILINE`):

    pattern: ^```table-of-contents\b.*?^```\s*\n?
    replacement: empty string

Implement as a Python `re.sub` call exactly equivalent to the above, operating on the `raw` source string.

## Change 2 — md-to-pdf.py renderer + TOC injection

Replace the current single `markdown.markdown(raw, extensions=["fenced_code", "tables"])` call with a `markdown.Markdown` instance that also enables the `toc` extension, configured to depth `1-2`:

    md = markdown.Markdown(
        extensions=["fenced_code", "tables", "toc"],
        extension_configs={"toc": {"toc_depth": "1-2"}},
    )
    html_body = md.convert(raw)
    toc_html = md.toc or ""

Then rewrite the generated toc HTML so every `<li>` carries a `data-href` mirroring its child anchor's `href` (the CSS `target-counter()` needs the URL on the `<li>` for the page-number pseudo-element):

    toc_html = re.sub(
        r'<li><a href="([^"]+)">',
        r'<li data-href="\1"><a href="\1">',
        toc_html,
    )

Wrap the rewritten toc HTML in a `<nav class="toc">` block (only if it is non-empty) and inject it at the top of the body:

    toc_section = (
        f'<nav class="toc"><h2 class="toc-title">Contents</h2>{toc_html}</nav>'
        if toc_html else ""
    )
    html_doc = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        f'<body>{toc_section}{html_body}</body></html>'
    )

## Change 3 — styles.css

Replace the entire file with exactly the following contents:

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
    nav.toc .toc-title { font-size: 15pt; margin: 0 0 8pt 0; font-weight: bold; }
    nav.toc ul { list-style: none; padding-left: 0; margin: 0; }
    nav.toc ul ul { padding-left: 16pt; }
    nav.toc li {
      display: flex;
      align-items: baseline;
      gap: 4pt;
      margin: 2pt 0;
      page-break-inside: avoid;
    }
    nav.toc li a {
      text-decoration: none;
      color: black;
      flex: 0 0 auto;
      order: 1;
    }
    nav.toc li::before {
      content: "";
      flex: 1 1 auto;
      order: 2;
      border-bottom: 1pt dotted #666;
      margin-bottom: 4pt;
      align-self: end;
    }
    nav.toc li::after {
      content: target-counter(attr(data-href, url), page);
      flex: 0 0 auto;
      order: 3;
    }

## Change 4 — plugin.json version

Bump `plugins/reading/.claude-plugin/plugin.json` `version` field by one **minor** level (per project SemVer rule: minor for new feature surface — auto TOC + restyle).

## Verification

Create a temporary sample markdown at the path shown below containing:

    /tmp/books-render-check.md

- Three or more H1 sections and at least two H2 subsections under one of them.
- One wide table (5+ columns or a column with long unbroken text) that would have overflowed previously.
- A Russian paragraph (at least one sentence) to exercise justified Cyrillic.
- A fenced code block with language `table-of-contents` somewhere in the body (this is what gets stripped).
- Enough total content to produce 3+ pages.

Render with:

    uv run plugins/reading/skills/books/scripts/md-to-pdf.py /tmp/books-render-check.md /tmp/books-render-check.pdf

Open the PDF and confirm:

- TOC at the top labelled "Contents", listing each H1 (and indented H2s underneath), with dotted leader and the correct page number on each line.
- No literal "table-of-contents" string anywhere in the PDF body.
- Body paragraphs are justified (clean right edge).
- The wide table fits within the page width — no overflow into the right margin.
- Tables render with only top/header-underline/bottom rules; no vertical gridlines, no gray header fill.
- Every page has a centered page number in the bottom margin.

## Quality gates

- `uv run ruff check .` passes.
- `uv run pytest` passes.
- task-reviewer agent verdict is APPROVED before marking Done and merging.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 md-to-pdf.py strips fenced code blocks with language 'table-of-contents' before passing source to markdown.markdown
- [ ] #2 md-to-pdf.py uses a markdown.Markdown instance with extensions fenced_code, tables, and toc, and toc_depth configured to '1-2'
- [ ] #3 md-to-pdf.py rewrites every <li><a href="X"> in the toc HTML to <li data-href="X"><a href="X"> before injection
- [ ] #4 md-to-pdf.py wraps the toc HTML in <nav class="toc"><h2 class="toc-title">Contents</h2>...</nav> and injects it at the top of the body when toc HTML is non-empty
- [ ] #5 styles.css @page rule has 'margin: 15mm 15mm 15mm 20mm' and an @bottom-center sub-rule with 'content: counter(page)'
- [ ] #6 styles.css body rule includes 'text-align: justify'
- [ ] #7 styles.css table rule includes 'font-size: 10pt' plus 'border-top' and 'border-bottom' declarations; the 'border: 1px solid #999' previously on th/td is removed
- [ ] #8 styles.css th, td rule includes 'overflow-wrap: break-word' and has no per-cell border declaration
- [ ] #9 styles.css th rule has 'border-bottom' and 'font-weight: bold' and no 'background: #f0f0f0'
- [ ] #10 styles.css contains a nav.toc block including 'target-counter(attr(data-href, url), page)' for the page number and a dotted-leader pseudo-element (border-bottom: 1pt dotted)
- [ ] #11 plugins/reading/.claude-plugin/plugin.json version field is bumped by one minor level from its prior value
- [ ] #12 Rendering the verification sample described in the task body produces a PDF where: TOC heading reads 'Contents', H1 and H2 entries appear with dot leaders and page numbers, no literal 'table-of-contents' string is present, the wide table fits the page, paragraphs are justified, and every page has a centered footer page number
- [ ] #13 uv run ruff check . passes from repo root
- [ ] #14 uv run pytest passes from repo root
- [ ] #15 task-reviewer agent verdict on git diff master..HEAD is APPROVED
<!-- AC:END -->
