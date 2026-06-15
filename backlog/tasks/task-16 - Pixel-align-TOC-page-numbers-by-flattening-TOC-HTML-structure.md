---
id: TASK-16
title: Pixel-align TOC page numbers by flattening TOC HTML structure
status: Done
assignee: []
created_date: '2026-06-15 10:47'
updated_date: '2026-06-15 10:50'
labels: []
dependencies: []
priority: medium
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

TASK-15's absolute-positioning fix did NOT actually pixel-align TOC page numbers. Each nested `<ul>` is a flex item with `flex: 0 0 100%`, and weasyprint apparently clamps that 100% to the parent li's content width (page width minus the parent's `padding-right: 24pt`). The `margin-right: -24pt` workaround intended to extend the nested ul back to the page right edge is silently ignored. Consequence: each nesting level shrinks the nested li's right edge by 24pt, so page numbers drift LEFT by 24pt per depth (visible in `~/Downloads/camunda-render.pdf` page 1).

Robust fix: do not rely on nested `<ul>` layout for indentation at all. **Flatten the TOC HTML** in `md-to-pdf.py` so every `<li>` is a direct sibling under one outer `<ul>`, stamped with a class (`toc-h1`, `toc-h2`, `toc-h3`) reflecting its original heading level. All `<li>` then share the exact same containing block — their right edges are identical, and `::after { right: 0 }` produces pixel-perfect column alignment. Indentation is expressed via class-based `padding-left` instead of structural nesting.

## Scope

In scope:
- `plugins/reading/skills/books/scripts/md-to-pdf.py` — replace the regex-based rewrite of `md.toc` with a walk of `md.toc_tokens` that emits a flat `<ul>` of `<li class="toc-hN" data-href="#slug"><a href="#slug">Title</a></li>` rows. Apply EMOJI_RE wrap to each token's `name`. Keep the existing `data-href` convention so the CSS `target-counter(attr(data-href, url), page)` still works.
- `plugins/reading/skills/books/references/styles.css`:
  - Remove `nav.toc ul ul { padding-left: 16pt; }` (no more nested ul).
  - Remove the `nav.toc li > ul { flex: 0 0 100%; order: 4; margin-top: 2pt; margin-right: -24pt; }` block entirely (no more nested ul to wrap).
  - Remove `flex-wrap: wrap` from the `nav.toc li` rule (single-line entries, no nested ul to wrap).
  - Add two rules expressing depth-based indentation:
    - `nav.toc li.toc-h2 { padding-left: 16pt; }`
    - `nav.toc li.toc-h3 { padding-left: 32pt; }`
  - Keep everything else (position: relative on li, padding-right: 24pt, ::after absolute right:0 top:0, ::before dot leader, gap, flex baseline).
- `plugins/reading/.claude-plugin/plugin.json` — patch bump 0.2.5 → 0.2.6.

Out of scope:
- Any other CSS rule beyond the four scoped changes (rule removals + the two new class rules + the flex-wrap removal from nav.toc li).
- Heading sizes, body font, margins, table styling, emoji rule baseline values, link color, font stack, lining-nums declaration — must remain identical.
- TOC depth (must stay "1-3" from TASK-14).
- The EMOJI_RE codepoint set, the image base_url change, the markdown extensions list — all stay as they are.
- SKILL.md — no changes.

## Files

- `plugins/reading/skills/books/scripts/md-to-pdf.py` (exists)
- `plugins/reading/skills/books/references/styles.css` (exists)
- `plugins/reading/.claude-plugin/plugin.json` (exists)

## Change 1 — md-to-pdf.py flatten the toc

Replace the current toc-handling block (the lines that read `md.toc`, regex-rewrite href to data-href, and assemble `toc_section`) with a recursive walk of `md.toc_tokens`. Pseudocode:

    def _flatten_toc(tokens, out):
        for t in tokens:
            out.append((t["level"], t["id"], t["name"]))
            if t.get("children"):
                _flatten_toc(t["children"], out)

    flat = []
    _flatten_toc(md.toc_tokens, flat)
    if flat:
        rows = "".join(
            f'<li class="toc-h{level}" data-href="#{tid}">'
            f'<a href="#{tid}">{EMOJI_RE.sub(r"<span class=\"emoji\">\\1</span>", name)}</a>'
            f'</li>'
            for level, tid, name in flat
        )
        toc_section = (
            f'<nav class="toc"><h2 class="toc-title">Contents</h2><ul>{rows}</ul></nav>'
        )
    else:
        toc_section = ""

The existing `html_body = EMOJI_RE.sub(...)` line for the body stays. The two regex passes that operated on the old `toc_html` (EMOJI_RE wrap + href→data-href rewrite) are removed since the new code handles both inline during the flatten step.

## Change 2 — styles.css TOC layout

Apply these changes to the `nav.toc` rule block:

- Delete the line `nav.toc ul ul { padding-left: 16pt; }`.
- Delete the entire `nav.toc li > ul { ... }` block (was 5 lines including the margin-right hack).
- In the `nav.toc li { ... }` rule, remove the `flex-wrap: wrap;` declaration. All other declarations on that rule stay.
- After the existing `nav.toc li::after { ... }` block, add:

      nav.toc li.toc-h2 { padding-left: 16pt; }
      nav.toc li.toc-h3 { padding-left: 32pt; }

Result: all `<li>` are direct siblings under one `<ul>`. Their outer right edges all coincide with the `nav.toc` content-area right edge, so `::after { right: 0 }` lands every page number at the exact same X column regardless of depth.

## Change 3 — plugin.json version

Bump `version` from `0.2.5` to `0.2.6` (patch — bug fix for TOC alignment via structural change).

## Verification

Re-render the Camunda doc:

    uv run plugins/reading/skills/books/scripts/md-to-pdf.py "/Users/paul/Private/Alfa/Projects/standard/stacks/backlog/docs/doc-6 - Camunda-8-in-Russian-software-registry.md" /tmp/task-16-camunda.pdf

Save artifact to `~/Downloads/task-16-camunda.pdf`. Open and visually confirm:
- TOC structure looks the same as before: H1 entries flush-left, H2 indented 16pt, H3 indented 32pt under their parents.
- TOC page numbers across H1, H2, H3 entries land at exactly the same right X column (use a vertical ruler / visual inspection).
- TOC dot leaders extend from end-of-anchor to the page-number column gap on every row.
- Image rendering (c8-saas-3.png) still works on page 3 (regression check).

## Quality gates

- `uv run ruff check .` passes from repo root.
- task-reviewer agent verdict on git diff master..HEAD is APPROVED.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 md-to-pdf.py builds toc HTML by walking md.toc_tokens (recursive flatten), not by regex over md.toc
- [x] #2 Each toc li carries data-href=#slug and class=toc-h{level} where level matches the original heading depth (1-3)
- [x] #3 EMOJI_RE wrap is applied to each toc entry's name text inside the new flatten step
- [x] #4 styles.css no longer contains 'nav.toc ul ul' rule or 'nav.toc li > ul' block (both removed)
- [x] #5 styles.css nav.toc li rule no longer declares flex-wrap
- [x] #6 styles.css adds 'nav.toc li.toc-h2 { padding-left: 16pt }' and 'nav.toc li.toc-h3 { padding-left: 32pt }'
- [x] #7 Verification render shows TOC page numbers pixel-aligned across H1, H2, and H3 entries (right edges at the same X column)
- [x] #8 Verification render confirms c8-saas image still appears (no regression vs TASK-15)
- [x] #9 plugins/reading/.claude-plugin/plugin.json version bumped from 0.2.5 to 0.2.6
- [x] #10 uv run ruff check . passes from repo root
- [x] #11 task-reviewer agent verdict on git diff master..HEAD is APPROVED
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Commit: `8ae4392` - task-16: pixel-align TOC page numbers by flattening TOC HTML structure. md-to-pdf.py walks md.toc_tokens to emit flat <ul> with class=toc-hN, data-href on every li. styles.css drops nested-ul rules and flex-wrap, adds class-based padding-left for depth. plugin 0.2.5->0.2.6.

Implementation:
- md-to-pdf.py: + EMOJI_SUB constant; + _flatten_toc helper (depth-first pre-order walk); rewrote main() toc handling to walk md.toc_tokens emitting flat <ul> of <li class=toc-h{level} data-href=#{id}><a href=#{id}>{name-with-emoji-wrap}</a></li>; removed the old md.toc + EMOJI_RE pass + href-to-data-href regex
- styles.css: -nav.toc ul ul, -nav.toc li > ul block, -flex-wrap on nav.toc li, +nav.toc li.toc-h2 / .toc-h3 padding-left rules
- plugin.json: 0.2.5 -> 0.2.6

Verification artifact: /Users/paul/Downloads/task-16-camunda.pdf
- TOC page numbers across H1/H2/H3 entries (1, 1, 2, 2, 3, 4, 5, 5, 6, 6, 8, 9, 9, 10) stack at the exact same right X column. Was the bug.
- c8-saas-3 image still renders on page 3 with caption (no regression vs TASK-15).

Lint: uv run ruff check . -> All checks passed.
task-reviewer verdict: APPROVED (with detailed correctness analysis of order preservation, empty-toc guard, data-href/href target identity, and class-name match).
<!-- SECTION:NOTES:END -->
