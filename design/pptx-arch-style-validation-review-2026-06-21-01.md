# Feature Review: pptx-arch-style-validation (Sixth cumulative — after TASK-30)

**Verdict: Aligned**

**Passes run:** 1, 3, 5 (PRD-derived requirements treated as brainstorm-locked intents BR-/CF-; brainstorm-cut audit; drift)
**Passes skipped:** 2 (no formal "Non-Goals" section in brainstorm beyond Scope Cuts — folded into Pass 3); 4 (brainstorm has no Success Metrics section — linter green/red is the implicit binary metric, already covered by per-task ACs)

## Carry-forward statement

Prior reviews `design/pptx-arch-style-validation-review-2026-06-20*.md` and `…-06-21.md` already established the full BR-1..BR-13 + CF-1..CF-10 matrix as **Delivered** (all 23 intents satisfied). TASK-30 is a pure spec-clarification patch within the existing surface — no new BR-/CF- coverage, no scope shift. This review only adds row **CF-11 (internal-contradiction sweep)** to that matrix and verifies the four item fixes.

## Intent → Implementation Matrix (TASK-30 incremental)

| ID | Requirement (TASK-30 item) | Status | Evidence |
|----|----------------------------|--------|----------|
| CF-11.1 | Rule #4 stops claiming title-slide title is centered | Delivered | `plugins/presentation/skills/pptx-arch-style/SKILL.md:702` — "center only slide titles on section slides" (dropped "title/"); reconciled with SKILL.md:162 left-align spec |
| CF-11.2 | EMU table: 0.900" entry shows correct value | Delivered | `SKILL.md:691` now `0.900" = 822960 EMU` (was 823560); verified 0.900 × 914400 = 822960 |
| CF-11.3 | Two-Box formula default reproduces Rule #9 widths | Delivered (option a) | `SKILL.md:641` default ratio is `0.488 / 0.512` with explanatory parenthetical "reproduces Rule #9 widths exactly given W=8.80 and GAP=0.20"; rationale documented in task notes (workspace search confirmed no consumer hardcodes 4.20/4.40 → option a chosen to preserve production-proven widths) |
| CF-11.4 | Spec scope of orthogonal-LINE requirement matches lint scope | Delivered | New Rule #12 added at `SKILL.md:710` generalizing orthogonality to ALL content-slide LINE shapes; matches `rules.yaml:232-243` which already keys on `slide_kinds: [content]` and `shape_type: line` |
| CF-11.5 | SemVer 0.8.1 → 0.8.2 | Delivered (patch appropriate) | `plugins/presentation/.claude-plugin/plugin.json` bumped; no new public surface added, all four items are spec text edits — patch correct per CLAUDE.md SemVer rules |
| CF-11.6 | Tests + lint stay green | Delivered | Task notes: ruff 0 issues, pytest 32/32 passed |

All four items fixed, with the implementer's path-choice on item 3 explicitly recorded with rationale in the task notes (including a falsifiable claim: workspace search for hardcoded 4.20/4.40 found none).

## Non-Goal Violations

None detected. TASK-30 explicitly stated "Out of scope: any change to rules.yaml or lint.py"; the diff shows zero changes to those files — only SKILL.md and plugin.json (the two stated targets).

## Scope Cut Violations

None detected. TASK-30 carved out four other contradictions surfaced by the audit (arrowhead-missing rule scope, carve-outs not enforced by lint, padding inconsistency, title-zone wrap messaging) and confirmed they remain untouched — preserved correctly as a future-iteration backlog.

## Drift List

No drift detected.

- The four-file scope (SKILL.md, plugin.json) matches the task spec exactly.
- `git show 51f62f9 --stat` reports `2 files changed, 5 insertions(+), 4 deletions(-)` — every changed line traces directly to one of the four items.
- No unrelated edits to references/rules.yaml, lint.py, fixtures, or tests.

## NEW contradictions check (TASK-30 incremental)

Cross-checked all four edits for new internal contradictions; one minor wording nit, no blockers:

| New text | Cross-reference | Verdict |
|---|---|---|
| Rule #4: "center only slide titles on **section** slides" | SKILL.md:174 (section divider title centered) + SKILL.md:162 (title slide left-aligned) | Consistent |
| EMU 0.900" = 822960 | 0.900 × 914400 = 822960.0 | Arithmetically correct |
| Default ratio 0.488/0.512 | Rule #9 widths 4.20/4.40: 8.80×0.488−0.10 = 4.194 (≈4.20); 8.80×0.512−0.10 = 4.406 (≈4.40); within sub-pixel rounding | Consistent within stated tolerance; "exactly" wording is a slight over-claim (Δ=0.006in vs 4.20) — the prior task-reviewer flagged this as a non-blocking nit, acceptable as future tightening to "within rounding" |
| Rule #12: "purely horizontal (`h=0, w>0`) or purely vertical (`w=0, h>0`)" | rules.yaml:239-240 lint floor is `w_min: 0.05` AND `h_min: 0.05` (both ≥ 0.05 = diagonal) | Functionally aligned (lint floor is a rounding tolerance, consistent with the audit's 0.005in policy); spec text is the stricter ideal, lint is the practical enforcement floor — common pattern, no contradiction |

One small observation worth a future patch-bump (optional, not a blocker): Rule #12 wording could explicitly acknowledge the 0.05in lint tolerance to fully close the literal-vs-enforced gap, e.g. "purely horizontal (`h<0.05, w>0`) or purely vertical (`w<0.05, h>0`)". Filing this as drift would be over-strict — it falls into the same "tighten to 'within rounding'" bucket the prior reviewer already noted on item 3.

## Reviewer Notes

- TASK-30 demonstrates the value of the audit-loop the feature was designed to enable: post-merge manual reading surfaced four real internal contradictions in a freshly audited spec, all fixable as one-line edits. This is exactly the Class-B leakage that the Phase 1 audit (TASK-21) was meant to prevent — finding four residuals after nine prior iterations is consistent with diminishing returns, not a process failure.
- The implementer's choice on item 3 is well-defended in task notes: workspace grep for hardcoded `4.20`/`4.40` came back empty, so options (a) and (b) are functionally symmetric on consumer risk, and (a) preserves the production-proven Rule #9 widths. This is the correct path under the task's "fewer downstream edits to consumer generators" tiebreaker.
- The Rule #4 fix is genuinely safer than it looks: section-divider titles being the *only* centered title type is now stated unambiguously, which matters for any consumer generator that might have copied "title/section" as a hint to center the title slide.
- Patch-bump (0.8.1 → 0.8.2) is the correct SemVer level — no new fields, no removed values, no API change; only spec text clarifications and an arithmetic typo fix. Rule #12 *additions* could arguably be minor (broadened scope of an existing constraint), but the lint rule it points to is unchanged, so the *enforced* surface is constant — patch is defensible.
- Cumulative feature state: 23 brainstorm-locked intents (BR-1..13 + CF-1..10) all Delivered as of prior reviews; CF-11 (internal-contradiction sweep) added and Delivered by TASK-30. No outstanding feature-level gaps; the four deferred contradictions (arrowhead-rule scope, padding inconsistency, carve-outs not lint-enforced, title-zone wrap messaging) are appropriately scoped as future work, not regressions.

Bundle path consulted: `/tmp/ralph-review-bundle.md`
Commit verified: `51f62f9` (TASK-30)
Prior reviews carry-forward base: `/Users/paul/Private/Projects/ai/claude-skills/design/pptx-arch-style-validation-review-2026-06-21.md`
