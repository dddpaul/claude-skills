---
id: TASK-23
title: >-
  pptx-arch-style-validation follow-ups: off-palette warn rule, size scale
  reconciliation, scripts/tests Node placement
status: In Progress
assignee: []
created_date: '2026-06-20 14:42'
updated_date: '2026-06-20 14:48'
labels:
  - 'feature:pptx-arch-style-validation'
dependencies: []
priority: medium
ordinal: 23000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Three follow-ups from the feature review of pptx-arch-style-validation (design/pptx-arch-style-validation-review-2026-06-20.md). One is a real partial implementation of an ask-user decision (BR-7); two are placement/consistency drifts that don't affect linter behavior but should be cleaned up before another iteration extends rules.yaml or adds another Node-using skill.

## Scope

In scope:
- Add a fill_color rule with severity: warning that scans every shape fill in the deck against the Color Palette allowlist drawn from SKILL.md (Red brand, neutrals, accents). Off-palette hits emit a warning, not an error, so generators see them without blocking publishing. Use the existing exit-code-2 path in lint.py (currently dead code under the all-error ruleset).
- Reconcile rules.yaml font_spec sizes_pt with SKILL.md Size Scale. Pick one direction and apply consistently: either add 7/28/32 pt to the SKILL.md Size Scale with a one-line note for each (protocol labels = 7pt per Diagram Conventions; stat-callout big numbers = 28/32pt), or remove them from rules.yaml and add narrow per-role exception rules.
- Move package.json and package-lock.json from repo root to plugins/presentation/skills/pptx-arch-style/scripts/tests/ so future Node-using skills in other plugins don't collide. Update .gitignore accordingly (remove root-level node_modules entry, add scoped one).
- Regenerate fixtures from gen_fixtures.js at the new path to confirm the move doesn't break anything; run test_lint.py.

Out of scope:
- Any new rule type beyond fill_color (severity: warning).
- Any changes to SKILL.md beyond the Size Scale row reconciliation (no broader spec edits).
- Auto-fix mode for off-palette colors (warn-only per the original ask-user decision).
- Validation against real Alfa decks (covered by handoff TASK-57 in stacks).

## Files

- `plugins/presentation/skills/pptx-arch-style/references/rules.yaml` (exists) — add palette-fill-warning rule; possibly amend font_spec.sizes_pt
- `plugins/presentation/skills/pptx-arch-style/scripts/lint.py` (exists) — add fill iteration logic against palette allowlist if not already covered by generic fill_color handler
- `plugins/presentation/skills/pptx-arch-style/SKILL.md` (exists) — Size Scale row only, if reconciliation direction is 'extend spec'
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/gen_fixtures.js` (exists) — may need a violator fixture with off-palette hex (e.g. Material Design #2196F3 fill) to test the new warning rule
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/test_lint.py` (exists) — add test asserting exit code 2 on the off-palette fixture
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/package.json` (to-create) — moved from repo root
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/package-lock.json` (to-create) — moved from repo root
- `package.json`, `package-lock.json` (to-delete at repo root)
- `.gitignore` (exists) — replace root node_modules entry with scoped path

## Source

Source review doc: design/pptx-arch-style-validation-review-2026-06-20.md (drift list + BR-7 partial)
Source brainstorm: design/pptx-arch-style-validation-brainstorm.md (original locked decision: warn + remap for off-palette colors)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 rules.yaml contains a rule with severity: warning that fails any shape fill hex not in the SKILL.md Color Palette allowlist; spec_ref points to the Color Palette section
- [x] #2 scripts/tests/fixtures/ includes a new violator deck containing an off-palette fill (e.g. #2196F3); lint.py exits 2 (not 1) when run against it; existing golden.pptx still exits 0
- [x] #3 rules.yaml font_spec.sizes_pt and SKILL.md Size Scale list the same set of approved sizes; whichever direction is chosen is documented in the task notes
- [x] #4 package.json and package-lock.json live under plugins/presentation/skills/pptx-arch-style/scripts/tests/; repo root has no package*.json; .gitignore scopes node_modules to that path
- [x] #5 uv run pytest plugins/presentation/skills/pptx-arch-style/scripts/tests/ passes; uv run ruff check . passes
- [x] #6 node gen_fixtures.js runs from the new tests/ path and regenerates every fixture deterministically
- [x] #7 plugin.json version bumped per SemVer: patch if Size Scale unchanged, minor if Size Scale extended
- [ ] #8 task-reviewer agent run on git diff master..HEAD returns APPROVED before merge
<!-- AC:END -->



## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan:
- Direction for Size Scale: EXTEND SKILL.md Size Scale to add 7, 28, 32 pt (rather than remove from rules.yaml). 7pt is the protocol-label size (Diagram Conventions section); 28pt and 32pt are stat-callout big-number sizes (already used in fixtures and documented in Component Styles). Removing them would mean a conformant deck with a stat-callout big number would fail lint. Therefore: minor version bump.
- Add palette-fill-warning rule in rules.yaml as a new 'fill_color' variant with palette_not_in allowlist and severity: warning. Extend _eval_fill_color to handle palette_not_in OR add a new rule type 'palette_warn'.
- Reading SKILL.md, the palette allowlist includes: Primary (F12D16, 595959, 000000, FFFFFF), Accent (176451, D3EAC9, B6D7A8, 93C47D), Semantic shape fills (E8F5E9, FFF8E1, F5F7FA + borders 82B366, D6B656, FF0000), Content box fills (D9EAD3, D9D9D9, 065A82, F3F3F3), Funnel callouts (065A82, C0392B, 595959), Diagram (DAEAF5, 9CC3E5, FFF2CC, D6B656, D9EAD3, 82B366, 595959, FF0000), grays (333333, 666666, 999999, CCCCCC), text colors (2E7D32, 8D6E00, 434343, B0D0E8, F0C0BC, B0B0B0, 7A7A7A, 888888, EFEFEF, E0E0E0, E8E8E8, F0F0F0, 21295C).
- Move package.json files; scope .gitignore node_modules to plugins/.../scripts/tests/.
- Add violator fixture with off-palette MD blue fill 2196F3 → lint should exit 2.
- Bump presentation plugin version 0.3.0 → 0.4.0 (minor).
<!-- SECTION:NOTES:END -->
