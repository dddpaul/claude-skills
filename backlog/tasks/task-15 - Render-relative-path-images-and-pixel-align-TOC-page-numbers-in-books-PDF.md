---
id: TASK-15
title: Render relative-path images and pixel-align TOC page numbers in books PDF
status: Done
assignee: []
created_date: '2026-06-15 09:16'
updated_date: '2026-06-15 10:14'
labels: []
dependencies: []
priority: medium
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

After TASK-14 rendered the Camunda doc through the new TOC-depth-3 stylesheet, two real issues surfaced:

1. **Image rendering**: the source markdown references a relative-path `<img src="...c8-saas...">`, but the rendered PDF shows no image. Weasyprint's `HTML(string=...)` constructor needs a `base_url` to resolve relative paths; the current script never passes one, so every relative image silently drops.
2. **TOC page-number column alignment**: the current `nav.toc` flex layout right-aligns page numbers within each `<li>`. Because nested `<ul>` blocks inherit a 16pt left padding cumulatively, weasyprint's flex resolution can place the page-number `::after` at sub-pixel-different X positions across depths H1 / H2 / H3. Switch to a `position: absolute; right: 0` anchor on `nav.toc { position: relative }` so every page number lands at the exact same X column regardless of nesting depth.

Plus one docstring nit found in code review: the `md-to-pdf.py` module docstring still claims the TOC contains "H1 + H2" — refresh to "H1 + H2 + H3" since TASK-14 broadened it.

## Scope

In scope:
- `plugins/reading/skills/books/scripts/md-to-pdf.py` — pass `base_url=str(src.parent)` to the `HTML(string=html_doc, ...)` call so relative image paths in the source markdown resolve against the source markdown's directory. Refresh the module docstring (line ~9) to say "H1 + H2 + H3".
- `plugins/reading/skills/books/references/styles.css` — change the `nav.toc` rule to add `position: relative`, change the `nav.toc li::after` rule to use `position: absolute; right: 0; top: 0;` instead of being a flex child. Adjust the `::before` (dot leader) so it still extends from end-of-anchor to the page-number column without overlapping. The simplest robust pattern is to also give every `nav.toc li` a `padding-right` equal to the maximum expected page-number width (e.g. `padding-right: 24pt`) so leaders end at the column edge and the absolutely-positioned page numbers sit just to the right of that edge at `right: 0`.
- `plugins/reading/.claude-plugin/plugin.json` — patch bump 0.2.4 → 0.2.5.

Out of scope:
- Any other CSS rule beyond `nav.toc`, `nav.toc li`, `nav.toc li::after`, `nav.toc li::before`, and `nav.toc` immediate child ul rules that need flow adjustment for the absolute-positioned page number.
- Heading sizes, body font, margins, table styling, emoji rule, link color, font stack, lining-nums declaration.
- TOC depth (stays "1-3" from TASK-14).
- EMOJI_RE codepoint coverage or wrap pipeline.
- SKILL.md changes (none of the documented values change in this task).

## Files

- `plugins/reading/skills/books/scripts/md-to-pdf.py` (exists)
- `plugins/reading/skills/books/references/styles.css` (exists)
- `plugins/reading/.claude-plugin/plugin.json` (exists)

## Change 1 — md-to-pdf.py image base_url + docstring

In the `main()` function, the current call is:

    HTML(string=html_doc).write_pdf(
        str(tmp), stylesheets=[CSS(filename=str(css_path))]
    )

Change to:

    HTML(string=html_doc, base_url=str(src.parent)).write_pdf(
        str(tmp), stylesheets=[CSS(filename=str(css_path))]
    )

Also: in the module docstring (the triple-quoted string at the top of the file), find the phrase "An auto-generated table of contents (H1 + H2)" and change it to "An auto-generated table of contents (H1 + H2 + H3)".

## Change 2 — styles.css TOC page-number column

In the `nav.toc` rule, add `position: relative;` so it becomes a positioning context for absolutely-positioned descendants.

In the `nav.toc li` rule, add `padding-right: 24pt;` so every li reserves a fixed-width column on the right for the page number.

In the `nav.toc li::after` rule, replace the flex declarations with:

    position: absolute;
    right: 0;
    top: 0;

(remove `flex: 0 0 auto; order: 3;`). Keep `content: target-counter(attr(data-href, url), page);`.

Adjust the `::before` (dot leader) rule if needed so the dots end inside the new content area (the padding-right effectively shrinks the available width for the flex children including the dot leader). No other behavioural change.

## Change 3 — plugin.json version

Bump `version` from `0.2.4` to `0.2.5` (patch — bug fix for images + visual alignment fix).

## Verification

Re-render the same Camunda source markdown TASK-14 used:

    uv run plugins/reading/skills/books/scripts/md-to-pdf.py "/Users/paul/Private/Alfa/Projects/standard/stacks/backlog/docs/doc-6 - Camunda-8-in-Russian-software-registry.md" /tmp/task-15-camunda.pdf

Open the PDF and confirm visually:
- The c8-saas (or any other) image referenced in the source markdown now appears in the PDF body at the location it appears in the source.
- TOC page numbers across H1 / H2 / H3 entries are pixel-aligned at the same right X column. Place a ruler / inspect visually that the digit "1" for an H1 row and the digit "5" for an H3 row sit in exactly the same column.

Save the verification PDF to `~/Downloads/task-15-camunda.pdf`.

## Quality gates

- `uv run ruff check .` passes from repo root.
- task-reviewer agent verdict on git diff master..HEAD is APPROVED.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 md-to-pdf.py HTML(string=html_doc) call passes base_url=str(src.parent) keyword arg
- [x] #2 md-to-pdf.py module docstring updated from 'H1 + H2' to 'H1 + H2 + H3'
- [x] #3 styles.css nav.toc li::after declares position: absolute, right: 0, and no longer declares flex or order
- [x] #4 styles.css nav.toc li declares padding-right (any value 16pt to 32pt) to reserve a column for the absolutely-positioned page number
- [x] #5 Verification render shows the c8-saas image from the Camunda source markdown rendered visibly inside the PDF body
- [x] #6 Verification render shows TOC page numbers across H1, H2, and H3 entries pixel-aligned at the same right X column
- [x] #7 plugins/reading/.claude-plugin/plugin.json version bumped from 0.2.4 to 0.2.5
- [x] #8 uv run ruff check . passes from repo root
- [x] #9 task-reviewer agent verdict on git diff master..HEAD is APPROVED
- [x] #10 styles.css nav.toc li rule declares position: relative (correct positioning context per row; the task body's literal 'nav.toc' was imprecise — see reviewer note)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Commit: `eb66292` - task-15: render relative-path images via base_url, pixel-align TOC page numbers via absolute positioning. md-to-pdf.py docstring refreshed H1+H2 -> H1+H2+H3. plugin 0.2.4->0.2.5.

Implementation:
- md-to-pdf.py: HTML(string=html_doc, base_url=str(src.parent)) for image resolution; module docstring 'H1 + H2' -> 'H1 + H2 + H3'
- styles.css nav.toc li: + position: relative, + padding-right: 24pt
- styles.css nav.toc li > ul: + margin-right: -24pt (cancels parent's padding-right so nested ul spans full width; nested li's then re-apply their own padding-right via the cascading nav.toc li rule, landing their page numbers at the same right X)
- styles.css nav.toc li::after: switched from flex (flex: 0 0 auto; order: 3) to absolute (position: absolute; right: 0; top: 0)
- plugin.json: 0.2.4 -> 0.2.5

AC#3 wording was tightened from 'nav.toc rule' to 'nav.toc li rule' because positioning context must be per row (not whole TOC) so each ::after anchors to its own row's top; reviewer confirmed.

Verification artifact: /Users/paul/Downloads/task-15-camunda.pdf
- c8-saas-3.png image renders inline on page 3 with caption (was missing before).
- TOC page numbers 1/2/3/4/5/6/8/9/10 stack at the same right X column across H1/H2/H3 entries.

Lint: uv run ruff check . -> All checks passed.
task-reviewer verdict: APPROVED.
<!-- SECTION:NOTES:END -->
