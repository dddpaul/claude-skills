---
id: TASK-30
title: Fix four internal contradictions in pptx-arch-style SKILL.md (v0.8.2 patch)
status: Done
assignee: []
created_date: '2026-06-21 05:31'
updated_date: '2026-06-21 05:36'
labels:
  - 'feature:pptx-arch-style-validation'
dependencies: []
priority: medium
ordinal: 30000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Self-audit of `plugins/presentation/skills/pptx-arch-style/` surfaced four small internal contradictions across SKILL.md and references/rules.yaml. All are one-line spec edits; bundling them into a single patch task because each is too small to merit its own iteration.

## Items

### Item 1: Rule #4 over-claims title-slide title is centered
- **SKILL.md:702** Rule #4 currently reads: 'Left-align all body text; center only slide titles on title/section slides'
- **SKILL.md:162** Title slide spec: 'Main title: Roboto Condensed 52pt bold, #F3F3F3, left-aligned'
- Title slide title is in fact left-aligned, not centered. Only section divider (SKILL.md:174) centers its title.
- **Fix:** change Rule #4 to '… center only slide titles on **section** slides' (drop 'title/').

### Item 2: EMU arithmetic error in EMU Reference table
- **SKILL.md:691** currently reads: `0.900" = 823560 EMU (subtitle y-position from v0.7.0)`
- Actual: 0.900 × 914400 = **822960 EMU**, off by 600 from the documented 823560
- Every other row in the EMU table is arithmetically correct — this is the only typo
- **Fix:** change 823560 → 822960

### Item 3: Two-Box formula default ratio doesn't reproduce Rule #9 hardcoded widths
- **SKILL.md:707** Rule #9: 'green x=0.60 w=4.20, amber x=5.00 w=4.40, same y, h=0.85'
- **SKILL.md:641-648** formula 'For any width split ratio r (default 0.48 / 0.52)' → greenW = 8.80×0.48 - 0.10 = **4.124** (not 4.20); amberW = **4.476** (not 4.40)
- Rule #9 corresponds to r ≈ 0.488, not 0.48
- **Fix (implementer choice, decision in task notes):** either (a) change the formula's documented default to r=0.488/0.512, OR (b) change Rule #9 widths to 4.12/4.48 to match r=0.48. Pick whichever requires fewer downstream edits to consumer generators — (a) is safer if any generator already hardcodes 4.20/4.40 from Rule #9.

### Item 4 (was item 5 in audit): decision-tree-connector-orthogonal lint rule scope > spec scope
- **rules.yaml:232-243** rule forbids any LINE shape on a content slide with both w≥0.05 AND h≥0.05 — i.e., orthogonality enforced for ALL content-slide lines
- **SKILL.md:466** spec text scopes the orthogonality requirement to **decision-tree** connectors only
- A legitimate diagonal line in a non-decision-tree context would falsely fire
- **Fix:** widen the spec text — add a new sentence to the Rules section (or Diagram Conventions intro): 'Connectors on content slides MUST be orthogonal (purely horizontal w=0+h>0 OR purely vertical w>0+h=0). Diagonal LINE shapes are forbidden regardless of context.' This brings the spec in line with what the lint already enforces, rather than narrowing the lint (which would require an invasive connector-tagging mechanism).

## Files

- `plugins/presentation/skills/pptx-arch-style/SKILL.md` — items 1, 2, 3 (and item 4 spec text)
- `plugins/presentation/.claude-plugin/plugin.json` — version 0.8.1 → 0.8.2

## Out of scope

- Any change to rules.yaml or lint.py (all items are spec-side fixes)
- Other contradictions surfaced by the audit but not on this 4-item list (carve-outs not enforced by lint, arrowhead-missing rule scope, padding inconsistency, title-zone wrap messaging) — those need decisions and aren't one-line edits
- Re-rendering canary in stacks (consumer-side concern)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Item 1: SKILL.md Rule #4 (line ~702) edited so the phrase about centering titles names only 'section' slides — title-slide title's left-alignment (line 162) is no longer contradicted by Rule #4
- [x] #2 Item 2: SKILL.md EMU Reference entry for 0.900" (line ~691) shows 822960 (not 823560); 0.900 × 914400 verifies to 822960
- [x] #3 Item 3: Either Rule #9 widths OR Two-Box formula default ratio updated so the two reproduce each other (formula default × W produces Rule #9 widths within rounding). Decision and rationale recorded in task notes
- [x] #4 Item 4: SKILL.md spec text broadened to require orthogonal connectors on ALL content-slide LINE shapes (not just decision-tree); spec scope now matches the existing lint rule decision-tree-connector-orthogonal
- [x] #5 plugin.json version bumped 0.8.1 → 0.8.2 (patch — spec clarifications only, no new public surface)
- [x] #6 uv run ruff check . exits 0; uv run pytest exits 0 (no behavior change expected, but smoke-check)
- [x] #7 task-reviewer agent on git diff master..HEAD returns APPROVED before merge
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: Apply four spec edits to SKILL.md + bump plugin version.

Item 1: Drop 'title/' from Rule #4 (line ~702) — title slide is left-aligned per spec line 162.

Item 2: 0.900" = 822960 EMU (verified: 0.900 × 914400 = 822960.0, fixes typo from 823560).

Item 3: Chose option (a) — change Two-Box formula default ratio from 0.48/0.52 to 0.488/0.512. Rationale: with GAP=0.20 and W=8.80, r=0.488 reproduces Rule #9 widths exactly (8.80×0.488 − 0.10 = 4.20; 8.80×0.512 − 0.10 = 4.40). Searched workspace — NO consumer generators hardcode 4.20/4.40, so risk to (a) vs (b) is symmetric; (a) is preferable because it preserves the production-proven widths in Rule #9 rather than changing them to 4.12/4.48.

Item 4: Add a new sentence to the Rules section requiring orthogonal LINE shapes on ALL content slides (not just decision-tree) — matches existing lint rule scope in rules.yaml:232–243.

Plus: plugin.json 0.8.1 → 0.8.2 (patch). Run uv run ruff and uv run pytest as smoke checks.

Commit: `51f62f9` - task-30: fix four internal contradictions in pptx-arch-style spec (v0.8.2)

Done. Implementation commit 51f62f9. task-reviewer verdict: APPROVED (one non-blocking observation noted — 'exactly' wording could be tightened to 'within rounding' in a future patch, but well within AC #3's rounding tolerance: r=0.488 → green=4.194 vs spec 4.20 Δ=0.006in, sub-pixel at 96 DPI). Final gates: ruff 0 issues, pytest 32/32 passed.
<!-- SECTION:NOTES:END -->
