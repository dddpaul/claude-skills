---
id: TASK-26
title: Default to combined shape+text in pptx-arch-style canonical snippets
status: Done
assignee: []
created_date: '2026-06-20 16:19'
updated_date: '2026-06-20 17:55'
labels:
  - 'feature:pptx-arch-style-validation'
dependencies: []
priority: medium
ordinal: 26000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Canonical examples in pptx-arch-style SKILL.md show the overlay pattern for blocks-with-text — `slide.addShape(ROUND_RECT, {x,y,w,h,fill,line})` followed by `slide.addText(label, {x,y,w,h,...})` at the same coordinates. Consumer projects (stacks's `presentations/registry/generate-doc-6-registry.js`, `presentations/workflows/generate-workflow-service-vision.js`) copied this into every block / card / badge / layer-block / decision-node. It's silly: pptxgenjs accepts text inline on the shape itself (or `addText` accepts a `shape:` option), giving you ONE combined element instead of two coincidentally-positioned overlays.

Costs of the overlay pattern:
- Double the shape count in the .pptx for every block (bigger file, slower load, slower edits in PowerPoint/Keynote/LibreOffice).
- Text position drifts independently from the container when the generator is edited — coordinates have to be kept in sync manually.
- `margin` / `align` / `valign` are properties of the text addText, with no enforcement that they fit inside the shape.

Combined form (`addText(label, { shape: ROUND_RECT, fill, line, margin: 0, align, valign, rectRadius, ... })`) eliminates all three.

The overlay pattern is legitimate ONLY when one block carries MULTIPLE labels at different positions (e.g., a card with a title in top-left AND a footer-tag in bottom-right). For single-text-per-block — which is the overwhelming majority of canonical components — combined form should be the default.

## Scope

In scope:
- Rewrite canonical snippets in SKILL.md to use combined form by default (layer-block, distribution bar, badge, card, table-cell where applicable, decision-tree node — coordinate with TASK-25 if it's in flight).
- Mark the overlay pattern explicitly as «use ONLY when 2+ labels at different positions on one block», with a one-line justification line in code comments.
- Optionally: add a lint rule (severity: info) detecting ROUND_RECT (or any block-shape) + addText at identical x,y,w,h — flags potential overlay-without-justification.
- Optionally: migration note in SKILL.md for consumers with legacy generators — they're grandfathered, refactor recommended not required.

Out of scope:
- Changing component visuals (colors, fonts, sizes, layout). This is purely about HOW the shape+text is generated, not WHAT it renders.
- Refactoring stacks-side generators. That's a consumer task after the skill convention shift ships.
- Touching the Decision tree section if TASK-25 is shipping it in parallel — coordinate via task notes if TASK-25 lands first, this task references its snippets.
- Auto-fix mode for the new lint rule (severity: info stays informational, not auto-rewritten).

## Files

- `plugins/presentation/skills/pptx-arch-style/SKILL.md` (exists) — rewrite all block+text snippets to combined form; add overlay-exception note (AC #1, #2 mandatory)
- `plugins/presentation/skills/pptx-arch-style/references/rules.yaml` (exists) — optional new rule, severity: info (AC #3)
- `plugins/presentation/skills/pptx-arch-style/scripts/lint.py` (exists) — handler for the new rule if shipped (AC #3)
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/` (exists) — fixture pair (overlay-violator vs combined-clean) if AC #3 shipped (AC #4)
- `plugins/presentation/.claude-plugin/plugin.json` (exists) — version bump per SemVer (AC #5)

## Source

Source: /Users/paul/Private/Alfa/Projects/standard/stacks@8c6f4b88b7bb
Reference of the overlay pattern in the wild: stacks repo, file `presentations/registry/generate-doc-6-registry.js` lines ~402-414 (`drawNode` helper — addShape + addText at identical coords) and similar patterns throughout `presentations/workflows/generate-workflow-service-vision.js`. Related handoffs in claude-skills: TASK-23 (Done, validation follow-ups), TASK-24 (canary spec clarifications), TASK-25 (decision-tree component recipe).

## Before starting (destination Claude validation checklist)

Before running this task, verify:
1. All `(exists)` file paths in the Files section still exist in this repo.
2. Each AC is objectively pass/fail (a grep, test invocation, build command, or visible behavior — not "works correctly").
3. All dependencies in the task's frontmatter are status=Done.
4. Out-of-scope items are not accidentally pulled in by ambiguous AC.

If anything is unclear or any check fails: STOP and ask the user. Do NOT start work blindly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 SKILL.md canonical convention statement: для блока-с-одним-текстом use combined form addText(label, { shape: ROUND_RECT, fill, line, margin: 0, align, valign, rectRadius, ... }) by default; overlay pattern (separate addShape + addText at same coords) marked explicitly as «use ONLY when 2+ labels at different positions on one block» with code-comment justification line
- [x] #2 All block+text snippets in SKILL.md (layer-block, distribution bar, badge, card, table-cell where applicable, и любые другие component examples) переписаны под combined form; overlay-examples остаются только там где >1 текст на блоке, с явным комментарием why
- [x] #3 Path (optional) lint rule: if shipped, rules.yaml contains new rule severity: info detecting block-shape (ROUND_RECT/RECTANGLE/DIAMOND) + addText at identical x,y,w,h coords — flags potential overlay-without-justification. Decision shipped/skipped recorded in task notes
- [x] #4 Если path (optional) shipped: scripts/tests/ includes fixture pair — overlay-violator (lint emits info, exit 0 because severity=info is non-blocking) и combined-clean (lint exits 0 cleanly without info messages on this rule)
- [x] #5 plugins/presentation/.claude-plugin/plugin.json version bumped per SemVer: patch (0.4.0 → 0.4.1) if only SKILL.md convention rewrite; minor (0.4.0 → 0.5.0) if new lint rule shipped. Decision recorded in task notes
- [x] #6 task-reviewer agent run on git diff master..HEAD returns APPROVED before merge
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan:
1. Add 'Shape+Text Composition' convention block to SKILL.md (after Layout System section), stating combined form addText({shape, fill, line, margin, align, valign, rectRadius}) as default; overlay only when 2+ labels per block, requires justifying comment.
2. Rewrite the canonical pptxgenjs decision-tree snippet's diamond() and terminal() helpers from addShape+addText overlay to combined addText({shape: ...}) form.
3. AC #3, #4 optional lint rule: SKIPPED for this iteration. Rationale: requires new evaluator type in lint.py (no existing rule type detects coincident shape+text pairs), new fixture pair, and is separable from the core convention rewrite. Lint rule can ship as its own follow-up task without blocking the convention change. Severity:info anyway — non-blocking.
5. Version bump: patch 0.6.0 → 0.6.1 (SKILL.md convention rewrite only, no new lint rule).

AC #1 implemented: Added 'Shape+Text Composition' section in SKILL.md before 'Component Styles' establishing combined-form addText({shape, fill, line, margin, align, valign, rectRadius}) as default; overlay form documented as exception for 2+ labels per block with required justifying code comment.

AC #2 implemented: Decision-tree canonical pptxgenjs snippet's diamond() and terminal() helpers rewritten to combined form (was: addShape+addText at same coords; now: single addText with shape: option). Other component recipes in SKILL.md describe shapes in style-guide notation (no executable overlay snippets), so the new convention block at the top now governs how consumers should generate them.

AC #3 + #4 DECISION: SKIPPED. Optional lint rule deferred — requires a new evaluator type in lint.py (none of the existing 8 types — mandatory_element/forbidden_element/shape_coordinates/fill_color/border_spec/font_spec/text_alignment/effect_override — detects coincident shape+text pairs) plus matching fixture pair. Severity:info is non-blocking anyway, so consumer migration is not gated on it. Filing as separable follow-up.

AC #5 implemented: plugins/presentation/.claude-plugin/plugin.json version 0.6.0 → 0.6.1 (patch — SKILL.md convention rewrite only, no new lint rule).

Commit: `1d95a3c` - task-26: default to combined shape+text in pptx-arch-style canonical snippets

task-reviewer verdict: APPROVED. All mandatory AC (#1, #2, #5, #6) green; optional AC #3, #4 deferred per task spec with rationale recorded. lint clean, 24 tests pass.

AC #3 satisfied by recording 'skipped' decision in earlier notes (lint rule deferred — requires new evaluator type in lint.py; severity:info is non-blocking so consumer migration is not gated).
AC #4 satisfied by being conditional on #3 — fixture pair correctly skipped because #3 was skipped.
<!-- SECTION:NOTES:END -->
