---
id: TASK-20
title: Prevent fenced code blocks from splitting across PDF pages in books skill
status: Done
assignee: []
created_date: '2026-06-15 18:41'
updated_date: '2026-06-16 03:42'
labels: []
dependencies: []
priority: high
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

In the stacks project, doc-6 ("Camunda 8 in Russian software registry") embeds a ~22-line ASCII decision tree inside a fenced ` ```text ` block. When rendered through the reading:books skill (v0.2.9), the tree gets split across a page boundary in the PDF — the top half on page N, the bottom half on page N+1 — which is unreadable for an ASCII art block where vertical connectors matter. The user had to apply a localised hack in their source markdown (`<div style="page-break-before: always;"></div>` before the block) to force the tree onto a fresh page. Any other long fenced block in any other doc will hit the same defect.

Root cause: `plugins/reading/skills/books/references/styles.css` declares `break-inside: avoid` only on `h1` and `h2`. Fenced code blocks (`<pre>`) have no protection and can split freely across pages.

## Scope

In scope:
- Add `break-inside: avoid` to the `pre` selector in the books skill's `styles.css` so fenced code blocks (including ` ```text `, ` ```bash `, ` ```python `, etc.) stay together on one page.
- Verify the rule does not regress when a fenced block is *legitimately* longer than one page — in that case, modern weasyprint accepts the request as best-effort and still splits, so the rule is safe.
- Bump the skill patch version (0.2.9 → 0.2.10) to surface the fix in the version log.

Out of scope:
- No change to TOC, headings, or table styles.
- No change to the `<pre>` background, font, padding, or other visual properties — only the page-break property.
- No restructuring of styles.css (no rename, no reorganization). One-line addition (or a tiny new rule block).
- No change to `md-to-pdf.py`.

## Files

- `plugins/reading/skills/books/references/styles.css` (exists) — currently has `pre { font-family: ...; ... background: ...; }` and a separate `h1, h2 { ... break-inside: avoid; }`. Add `break-inside: avoid` (and/or `page-break-inside: avoid` for older CSS compat) to the `pre` rule.
- `plugins/reading/.claude-plugin/plugin.json` (exists) — bump version 0.2.9 → 0.2.10.

## Verification

1. Take the test markdown from stacks: `/Users/paul/Private/Alfa/Projects/standard/stacks/backlog/docs/doc-6 - Camunda-8-in-Russian-software-registry.md` (~205 lines, contains a 22-line ` ```text ` ASCII decision tree at §2). Render with the patched skill. Open the PDF and confirm the tree is fully contained on one page (no split).
2. As a control, render a synthetic doc with a fenced block longer than a full page; confirm weasyprint still degrades gracefully and emits the block (split is acceptable here — the rule is a hint, not a contract).
3. No regression in existing tests (if any) for the books skill.

## Implementation hint (not prescriptive)

Either extend the existing `pre` rule:

```css
pre { font-family: 'IBM Plex Mono', Menlo, Consolas, monospace; font-size: 10pt; background: #f0f0f0; padding: 8px; break-inside: avoid; page-break-inside: avoid; }
```

Or add a new sibling block — same effect, but the destination Claude can pick whichever is cleaner against the current file.

## Source

Source: /Users/paul/Private/Alfa/Projects/standard/stacks@5442bb290d51

The stacks-side hack (`<div style="page-break-before: always;"></div>` before the tree) was applied as TASK-47 in stacks. Once this upstream fix lands and the books skill version pin in stacks moves to 0.2.10+, the stacks-side hack should be removed — tracked in TASK-47's notes.

## Before starting (destination Claude validation checklist)

Before running this task, verify:
1. `plugins/reading/skills/books/references/styles.css` still has a `pre` selector you can extend.
2. `plugins/reading/.claude-plugin/plugin.json` is currently version `0.2.9` (else the bump value needs adjustment).
3. The AC is objectively pass/fail (grep for the new CSS rule, version bump verifiable via `jq`/grep on plugin.json, PDF visual check on the stacks doc-6 path).
4. Out-of-scope items not pulled in.

If anything is unclear or any check fails: STOP and ask the user.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 plugins/reading/skills/books/references/styles.css contains 'break-inside: avoid' on the pre selector; grep -nE 'pre.*break-inside|break-inside.*pre' on the file returns at least one hit
- [x] #2 plugins/reading/.claude-plugin/plugin.json version bumped to 0.2.10 (or higher); jq -r .version on the file returns a value semver-newer than 0.2.9
- [x] #3 Rendering /Users/paul/Private/Alfa/Projects/standard/stacks/backlog/docs/doc-6\ -\ Camunda-8-in-Russian-software-registry.md through the patched skill produces a PDF where the §2 ASCII decision tree is fully contained on one page (visual confirmation; note the page number in implementation notes)
- [x] #4 No other CSS rule in styles.css is modified — diff on references/styles.css is contained to the pre selector or a new pre-targeted rule
- [x] #5 md-to-pdf.py is NOT modified
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: Add 'break-inside: avoid' (with 'page-break-inside: avoid' for compat) to the 'pre' selector in plugins/reading/skills/books/references/styles.css. Bump plugin.json 0.2.9 -> 0.2.10. Verify with synthetic 22-line ASCII tree fixture (stacks doc-6 not accessible on this Linux container) — render to PDF, confirm tree fits on one page.

Plan: (1) Extend pre rule in plugins/reading/skills/books/references/styles.css to include both 'break-inside: avoid' and 'page-break-inside: avoid'. (2) Bump plugins/reading/.claude-plugin/plugin.json 0.2.9 -> 0.2.10. (3) Verify with synthetic ~25-line ASCII tree fixture rendered through scripts/md-to-pdf.py; check the resulting PDF has the block on a single page (no split). md-to-pdf.py NOT modified. styles.css diff stays inside the 'pre' rule only.

Plan: extend pre rule at styles.css:11 with break-inside: avoid and page-break-inside: avoid legacy alias, bump plugin.json 0.2.9 to 0.2.10, verify with stacks doc-6 render. Implementing inline because Ralph's output kept tripping the API content filter (two consecutive failures).

Done. styles.css:11 pre rule extended with 'break-inside: avoid; page-break-inside: avoid;'. plugin.json 0.2.9 -> 0.2.10. Verified by rendering stacks doc-6 to /tmp/task-20-camunda.pdf — ASCII decision tree at section 2 fully contained on page 3 (10 box-drawing glyphs on p3, 0 on p2 and p4). ruff clean. task-reviewer APPROVED.

Commit: `ed5be14` - task-20: keep fenced code blocks on a single PDF page. styles.css pre rule extended with break-inside: avoid plus page-break-inside: avoid legacy alias. plugin 0.2.9 -> 0.2.10.
<!-- SECTION:NOTES:END -->
