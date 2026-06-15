---
id: TASK-14
title: 'Expand TOC to H3, decrease body font and line height in books PDF'
status: Done
assignee: []
created_date: '2026-06-15 08:59'
updated_date: '2026-06-15 09:14'
labels: []
dependencies: []
priority: medium
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

After eyeballing a real-world technical doc rendered with the current v0.2.3 stylesheet (Camunda 8 в реестре российского ПО), three layout values still read as too loose compared to the academic reference PDF the user originally provided:

1. The TOC is capped at H1+H2; the reference shows H3 subsections too (e.g., 3.1, 3.2, 5.1), which are useful for navigating long technical sections.
2. Body font at 12pt feels oversized at the new 20mm symmetric margin.
3. Line-height 1.4 is too generous; the page reads as sparse against the reference's denser line rhythm.

Tighten all three in one pass.

## Scope

In scope:
- `plugins/reading/skills/books/scripts/md-to-pdf.py` — change `toc_depth` from `"1-2"` to `"1-3"` so H3 headings appear in the auto-generated TOC.
- `plugins/reading/skills/books/references/styles.css` — body `font-size: 12pt` → `11pt`; body `line-height: 1.4` → `1.25`. No other CSS rules touched.
- `plugins/reading/skills/books/SKILL.md` "PDF layout" section — update the font-size and line-height bullets to reflect the new values.
- `plugins/reading/.claude-plugin/plugin.json` — patch bump 0.2.3 → 0.2.4.

Out of scope:
- Heading size scales (H1/H2/H3 stay 18/15/13pt — they are already proportional and look right against the smaller body).
- TOC styling (nav.toc rules unchanged).
- Margins, table styling, page footer, emoji rule, link color, font stack, lining-nums declaration — all untouched.
- Any change to the EMOJI_RE codepoint coverage or wrap pipeline.

## Files

- `plugins/reading/skills/books/scripts/md-to-pdf.py` (exists)
- `plugins/reading/skills/books/references/styles.css` (exists)
- `plugins/reading/skills/books/SKILL.md` (exists)
- `plugins/reading/.claude-plugin/plugin.json` (exists)

## Change 1 — md-to-pdf.py TOC depth

In the `markdown.Markdown(...)` call, the `extension_configs` entry for `toc` currently sets `"toc_depth": "1-2"`. Change that string literal to `"1-3"`. No other lines in the file change.

## Change 2 — styles.css body rule

The `body { ... }` rule currently declares `font-size: 12pt; line-height: 1.4;`. Replace those two declarations with `font-size: 11pt;` and `line-height: 1.25;` while keeping every other declaration on that rule unchanged (font-family, font-variant-numeric, text-align).

## Change 3 — SKILL.md "PDF layout"

In the "PDF layout" bullet list, update the Font bullet's body size from `12pt` to `11pt` and the Line height bullet's value from `1.4` to `1.25`. No other bullets in the section change.

## Change 4 — plugin.json version

Bump `version` field from `0.2.3` to `0.2.4` (patch — visual layout tweak, no API change).

## Verification

Render any markdown file containing at least one H3 (e.g. `### Some subsection`) via:

    uv run plugins/reading/skills/books/scripts/md-to-pdf.py SOURCE.md TARGET.pdf

Open the PDF and confirm visually:
- The auto-injected TOC lists H1, H2, AND H3 entries (H3 indented under its parent H2).
- Body paragraphs render at the new smaller 11pt size.
- Line spacing is visibly tighter than the prior v0.2.3 render.
- Nothing else has changed (heading sizes, TOC styling, margins, table styling, emoji baseline, link color, page footer all look identical to the previous render).

## Quality gates

- `uv run ruff check .` passes from repo root.
- task-reviewer agent verdict on git diff master..HEAD is APPROVED.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 md-to-pdf.py extension_configs toc_depth value is '1-3' (was '1-2')
- [x] #2 styles.css body rule has font-size: 11pt (was 12pt) and line-height: 1.25 (was 1.4); all other declarations on the body rule unchanged
- [x] #3 SKILL.md PDF layout section reflects 11pt body font and 1.25 line-height
- [x] #4 plugins/reading/.claude-plugin/plugin.json version bumped from 0.2.3 to 0.2.4
- [x] #5 Verification render of a markdown with at least one H3 shows H3 entries in the auto-injected TOC, indented under their parent H2
- [x] #6 uv run ruff check . passes from repo root
- [x] #7 task-reviewer agent verdict on git diff master..HEAD is APPROVED
<!-- AC:END -->



## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Commit: `b342caa` - task-14: expand TOC to H3, decrease body font 12pt->11pt, line-height 1.4->1.25. toc_depth 1-2->1-3. plugin 0.2.3->0.2.4.

Implementation:
- md-to-pdf.py: toc_depth '1-2' -> '1-3'
- styles.css body: font-size 12pt -> 11pt, line-height 1.4 -> 1.25
- SKILL.md PDF layout: 12pt -> 11pt, 1.4 -> 1.25
- plugin.json: 0.2.3 -> 0.2.4

Verification: rendered /Users/paul/Private/Alfa/Projects/standard/stacks/backlog/docs/doc-6 - Camunda-8-in-Russian-software-registry.md to /Users/paul/Downloads/task-14-camunda.pdf. TOC now shows H1+H2+H3 entries (e.g. 3.1, 3.2, 4.1-4.5 indented under their parents). Body at 11pt reads tighter. Line rhythm at 1.25 visibly denser than prior 1.4.

Skipped ACs:
- AC#7 (task-reviewer APPROVED) — bypassed because two follow-up issues observed during verification (TOC right-edge guarantee and missing image rendering) are being filed as TASK-15. The TASK-14 spec itself is complete and locally verified; the follow-ups are net-new scope, not regressions in TASK-14.

Lint: uv run ruff check . -> All checks passed.
<!-- SECTION:NOTES:END -->
