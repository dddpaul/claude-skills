---
id: TASK-45
title: 'Compare paragraphs on their coalesced runs, not by raw position'
status: Done
assignee: []
created_date: '2026-09-03 17:46'
updated_date: '2026-09-03 18:49'
labels: []
dependencies:
  - TASK-44
ordinal: 45000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

`diff_runs` in `plugins/presentation/skills/pptx-compare/scripts/compare_decks.py` pairs runs with `zip(ref.runs, gen.runs)`, i.e. strictly by index. When two engines split the same paragraph at different points, that pairing straddles formatting boundaries and reports a difference that is not there.

Minimal instance (both paragraphs are character-identical):

```
ref: [("Label: ", bold), ("value", plain)]                  # PowerPoint, coalesced
gen: [("La", bold), ("bel: ", bold), ("value", plain)]      # generator fragments
-> para[0] run[1] bold: ref=False gen=True                   # spurious
```

Two consequences. In the default view it is a false finding to chase. Under `--fold-engine-artefacts` (TASK-44) the run-count line folds correctly but this line survives, so a mixed-format deck that has genuinely converged never reaches zero — which is exactly the signal that flag exists to provide.

Found during the TASK-44 review by a 300k-case property fuzz of the fold gate: of 46,700 folds that fired, 31,792 left another finding standing, nearly all of this shape. The fold itself was sound in every case — this is the adjacent defect, and it pre-dates TASK-44 (the same line is emitted on master today).

TASK-44 documents the caveat in `SKILL.md` under "Folding engine artefacts" as a stopgap; this task removes it.

## Scope

In scope:

- Pair runs by their coalesced form — `_coalesce()` already exists in `compare_decks.py` and is the right normalisation — so the per-run diff compares like with like.
- Remove the SKILL.md caveat paragraph once the behaviour it describes is gone.
- Bump the `presentation` plugin version.

Out of scope:

- The fold gate itself, which the fuzz found sound.
- Shape matching.

## Note on the default output

This CHANGES the default output: findings that master emits today will disappear. That is the point — they are false — but it means TASK-44's "default is unchanged" pin no longer applies, and `test_flag_off_pins_the_prior_finding_count_on_the_prior_fixtures` may need its expectation updated with a written justification rather than silently relaxed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A paragraph split at a different point than the reference, but character-identical, reports no per-run difference
- [x] #2 A genuine per-run formatting difference is still reported when the splits differ
- [x] #3 A regression test covers the bold-label/split-value case from the description
- [x] #4 uv run pytest on plugins/presentation/skills/pptx-compare passes green
- [x] #5 uv run ruff check . passes green
- [x] #6 The SKILL.md caveat paragraph under 'Folding engine artefacts' is removed
- [x] #7 version in plugins/presentation/.claude-plugin/plugin.json is bumped per the SemVer rule in CLAUDE.md
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
SemVer pick (2026-09-03): bump plugins/presentation/.claude-plugin/plugin.json 0.10.1 -> 0.10.2 (PATCH) — this is a bug fix (false per-run findings), which is a 'content tweak' under CLAUDE.md, not a new skill or broadened trigger. Do NOT bump minor. Also: per the task's own Note, update test_flag_off_pins_the_prior_finding_count_on_the_prior_fixtures (test_compare_decks.py:293) with a written justification comment, not a silent number change.

Plan (2026-09-03): (1) _coalesce() returns list[Run] (merged via dataclasses.replace) instead of list[tuple], so the fold gate keeps comparing the same information and the per-run loop can read fields off the merged runs. (2) diff_runs pairs the COALESCED runs instead of zip(ref.runs, gen.runs) — identical text + identical per-character formatting always coalesce to identical lists, so a paragraph split at a different point reports nothing, while a real formatting difference survives the merge and is still reported. (3) Guard the truncation hole the change would otherwise open: when the raw run counts are EQUAL but the coalesced counts differ (e.g. ref two adjacent bold runs vs gen bold+italic), the existing raw run-count line does not fire and the zip would drop the extra span silently — master inspects it today. Add an 'elif' line reporting the coalesced counts so no span is uninspected without a trace; elif, not a second unconditional line, so the common case never prints two count lines saying the same numbers. (4) Tests: split-at-a-different-point folds to nothing, genuine drift across differing splits still reported, the bold-label/split-value case from the description, plus the truncation guard. (5) Remove the SKILL.md caveat paragraph and re-word the 'stops at the shorter side' sentence to be about coalesced runs. (6) plugin.json 0.10.1 -> 0.10.2 per the pinned notes. Baseline captured: 55 passed under plugins/presentation/skills/pptx-compare; full suite 239 passed / 1 pre-existing failure (test_helper_renders_canonical_decision_tree, missing node_modules).

Commit: `b2d2999` - task-45: pair paragraph runs by their coalesced form, not by raw position

Commit: `e82ab6d` - task-45: note that run[N] numbers merged spans, not either deck's runs

Done (2026-09-03). _coalesce() now returns list[Run] (merged with dataclasses.replace, inputs never mutated) and a new _align_runs() walks the two coalesced lists together by the characters each run covers, splitting at the union of both sides' boundaries; diff_runs iterates those pairs instead of zip(ref.runs, gen.runs). SUPERSEDES plan step (3): the planned 'elif coalesced run count' line is NOT in the code. Step (3) existed to plug the truncation hole that the literal minimum fix — zip(_coalesce(ref.runs), _coalesce(gen.runs)) — opens; the existing test test_folding_leaves_a_run_level_difference_alone caught that hole (ref's two adjacent bold runs coalesce to one, gen's bold+italic stay two, raw counts equal so no count line fires, zip truncates and the italic run is never inspected). The character-range walk closes it without new output vocabulary and reports the field-level difference instead of a coarse count, so the extra line was dropped. THE PIN AT 3 WAS LEFT ALONE, DELIBERATELY: test_flag_off_pins_the_prior_finding_count_on_the_prior_fixtures still asserts 3 because neither committed fixture pair contains a paragraph split across a formatting boundary — the only run-level finding there is a size delta on a single-run paragraph. Proof rather than reading: the CLI's stdout+stderr+exit code was byte-compared against 'git show master:' on both fixture pairs with and without --fold-engine-artefacts, identical in all four runs (Total: 3 / exit 1 and Total: 0 / exit 0, so non-vacuous). The task's Note anticipated this test might need updating; it did not, and nothing was silently relaxed. Evidence the defect is gone: a 30,000-case property fuzz over diff_runs — every split-only difference now folds to zero and every per-character formatting mutation is reported, against 12,369 spurious per-run findings and 3,313 missed real differences from master's implementation on the same cases; end to end on the description's own deck pair, master --fold-engine-artefacts prints 'para[0] run[1] bold: ref=False gen=True' (Total: 1) and this branch prints Total: 0, exit 0, which is the convergence signal TASK-44's flag exists for. Accepted trade-offs, recorded rather than fixed: (a) run[N] now numbers the merged union segments, so it need not line up with dump_slide.py's run[N] for either deck — documented in SKILL.md under compare_decks.py; (b) one drift spanning several union segments can be reported once per segment, inflating counts on genuinely mixed drift, though each line is true of the span it covers and the fold gate is untouched; (c) a zero-width run can now produce a pair mid-paragraph, which is noise but cannot block reaching zero (equal coalesced lists walk in lockstep and emit nothing); (d) _coalesce moved onto the default path and recomputes the profile per iteration — negligible at deck scale, but it contradicts TASK-44's note that it is never called without the flag. SKILL.md: the 'One caveat on reaching zero' paragraph is removed (AC 6) and the now-false sentence about the per-run comparison stopping at the shorter side was rewritten in the same section — leaving it would have replaced one wrong caveat with another. plugin.json 0.10.1 -> 0.10.2 (PATCH, bug fix); marketplace.json carries no version fields, so there is no second manifest to sync. Verification: uv run pytest plugins/presentation/skills/pptx-compare 59 passed; full uv run pytest 243 passed with 1 pre-existing failure (test_helper_renders_canonical_decision_tree, missing node_modules, fails identically on master); uv run ruff check . clean. Reviewed by the task-reviewer agent: APPROVED, five non-blocking findings, all five addressed here (1 documented in SKILL.md, 2-4 recorded above, 5 is this note).
<!-- SECTION:NOTES:END -->
