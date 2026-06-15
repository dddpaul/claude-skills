---
id: TASK-17
title: 'Shrink table cells in books PDF (9pt font, 4x8 padding)'
status: Done
assignee: []
created_date: '2026-06-15 10:59'
updated_date: '2026-06-15 11:02'
labels: []
dependencies: []
priority: medium
ordinal: 17000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

After TASK-16 fixed the TOC alignment, the user observed that table cells in the rendered Camunda doc still read as visually heavier than the surrounding body — wider columns and taller rows than needed. Tighten cell sizing globally for all tables.

## Scope

In scope:
- `plugins/reading/skills/books/references/styles.css`:
  - `table` rule: `font-size: 10pt` → `9pt`. All other declarations on the rule stay.
  - `th, td` rule: `padding: 6px 10px` → `4px 8px`. All other declarations stay.
- `plugins/reading/.claude-plugin/plugin.json` — patch bump 0.2.6 → 0.2.7.

Out of scope:
- Any other CSS rule beyond the two declarations above.
- Adding a `.table-compact` class or any author-facing opt-in mechanism.
- Changing line-height inside cells.
- Heading sizes, body font, TOC styling, page margins, emoji rule, link color, font stack, lining-nums declaration.
- md-to-pdf.py — no changes.
- SKILL.md — no changes (the documented values for body/heading sizes don't change; tables aren't enumerated in the PDF layout section).

## Files

- `plugins/reading/skills/books/references/styles.css` (exists)
- `plugins/reading/.claude-plugin/plugin.json` (exists)

## Change 1 — styles.css

In the `table { ... }` rule, change `font-size: 10pt` to `font-size: 9pt`. Leave every other declaration (border-collapse, width, margin, border-top, border-bottom) untouched.

In the `th, td { ... }` rule, change `padding: 6px 10px` to `padding: 4px 8px`. Leave every other declaration (text-align, vertical-align, overflow-wrap) untouched.

## Change 2 — plugin.json version

Bump `version` from `0.2.6` to `0.2.7` (patch — visual layout tweak, no API change).

## Verification

Re-render the Camunda doc:

    uv run plugins/reading/skills/books/scripts/md-to-pdf.py "/Users/paul/Private/Alfa/Projects/standard/stacks/backlog/docs/doc-6 - Camunda-8-in-Russian-software-registry.md" /tmp/task-17-camunda.pdf

Save artifact to `~/Downloads/task-17-camunda.pdf`. Open and visually confirm:
- Tables render at 9pt body (smaller than surrounding 11pt prose, visibly tighter).
- Cell padding is reduced; rows are shorter top-to-bottom than the prior render at 6px/10px padding.
- No regression: TOC alignment still pixel-perfect across H1/H2/H3, c8-saas image still renders on page 3.

## Quality gates

- `uv run ruff check .` passes from repo root.
- task-reviewer agent verdict on git diff master..HEAD is APPROVED.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 styles.css table rule font-size declared as 9pt (was 10pt); all other table declarations unchanged
- [x] #2 styles.css th, td rule padding declared as 4px 8px (was 6px 10px); all other th/td declarations unchanged
- [x] #3 plugins/reading/.claude-plugin/plugin.json version bumped from 0.2.6 to 0.2.7
- [x] #4 Verification render shows table cells at 9pt with tighter padding; no regression in TOC alignment or c8-saas image rendering
- [x] #5 uv run ruff check . passes from repo root
- [x] #6 task-reviewer agent verdict on git diff master..HEAD is APPROVED
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Commit: `dd9714a` - task-17: shrink table cells in books PDF — font 10pt->9pt, padding 6/10->4/8. plugin 0.2.6->0.2.7.

Implementation:
- styles.css table rule: font-size 10pt -> 9pt
- styles.css th, td rule: padding 6px 10px -> 4px 8px
- plugin.json: 0.2.6 -> 0.2.7

Verification artifact: /Users/paul/Downloads/task-17-camunda.pdf
- Tables visibly tighter at 9pt + 4/8 padding.
- The 4-column table on page 3 now sits beneath the c8-saas image AND the 3.1 heading on the same page (previously would have spilled).
- TOC alignment + image rendering unchanged (no regression).

Lint: uv run ruff check . -> All checks passed.
task-reviewer verdict: APPROVED.
<!-- SECTION:NOTES:END -->
