---
id: TASK-44
title: Add an engine-artefact folding flag to pptx-compare
status: Done
assignee: []
created_date: '2026-09-03 17:19'
updated_date: '2026-09-03 17:46'
labels: []
dependencies:
  - TASK-43
priority: medium
ordinal: 44000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

When the comparison harness was ported into a skill (TASK-43), its behaviour changed from the source: run coalescing is now printed as a finding tagged "engine artefact if the text above matches — see engine-differences.md," whereas the original script folded it silently. Measured on the same pair of decks: source — `Total differences: 73`, skill — `Total: 145 discrepancies over 22 slides`.

Showing is more honest than hiding, and the default should not change. But folding also removed a single-signal convergence check: previously the loop that aligns a generator against a manual deck ran until the "zero differences" line, and zero meant "converged." Now a fully-aligned deck still prints several dozen lines, and "done" has to be judged by eye, line by line.

The flag brings that mode back without hiding anything by default: without the flag — the full honest diff; with the flag — only what the engine pair does not explain, and zero as the convergence signal.

## Scope

In scope:

- A flag on `scripts/compare_decks.py` (name at your discretion, e.g. `--fold-engine-artefacts`) that suppresses the findings the tool itself already marks as an engine artefact — i.e. the lines it currently annotates with "engine artefact ... see engine-differences.md."
- With the flag on, the total line counts only the remaining findings, so a deck that differs solely by engine artefacts reports zero.
- A section in `SKILL.md`: what the flag does, and when it fits — the generator-convergence loop versus the discrepancy diff. The default stays as-is, and that must be stated explicitly.
- A test on fixtures: a pair of decks differing only by run coalescing yields findings without the flag and zero with it; plus a test pinning that, without the flag, the finding count is unchanged.
- Bump the `presentation` plugin version per the rule in CLAUDE.md.

Out of scope:

- Changing the default behaviour — the full diff stays the default.
- Touching the detection logic for the other engine discrepancies, or shape matching at all.
- The `pptx-arch-style` and `pptx-core-style` skills.
- Anything in the stacks project.

## How to reproduce the measurement

In the stacks project (read-only; note these files will soon be deleted by a separate task — that is exactly why the numbers above are frozen here):

```sh
cd /Users/paul/Private/Alfa/Projects/standard/stacks
REF=presentations/cross-product/reference/manual-target.pptx
GEN=presentations/cross-product/output/cross-product-mechanisms.pptx
uv run presentations/cross-product/compare/compare-decks.py "$REF" "$GEN" | head -1
uv run plugins/presentation/skills/pptx-compare/scripts/compare_decks.py "$REF" "$GEN" | tail -1
```

## Files

- `plugins/presentation/skills/pptx-compare/scripts/compare_decks.py` (exists) — the flag, finding filtering, total recount
- `plugins/presentation/skills/pptx-compare/scripts/tests/` (exists) — fixtures and tests
- `plugins/presentation/skills/pptx-compare/SKILL.md` (exists) — the flag section; next to "Reading the output"
- `plugins/presentation/.claude-plugin/plugin.json` (exists) — version

## Source

Source: /Users/paul/Private/Alfa/Projects/standard/stacks@0cef7d3728e9

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
- [x] #1 uv run plugins/presentation/skills/pptx-compare/scripts/compare_decks.py --help lists the engine-artefact folding flag
- [x] #2 with the flag, lines tagged as an engine artefact are not printed
- [x] #3 with the flag, the total line counts only the remaining findings: on a fixture pair differing solely by run coalescing, the total is zero
- [x] #4 without the flag the output is unchanged: a test pins the prior finding count on the prior fixture pair
- [x] #5 SKILL.md describes the flag, names the convergence-loop scenario, and states explicitly that the default is unchanged
- [x] #6 uv run pytest on plugins/presentation/skills/pptx-compare passes green
- [x] #7 uv run ruff check . passes green
- [x] #8 version in plugins/presentation/.claude-plugin/plugin.json is bumped per the SemVer rule in CLAUDE.md
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
SemVer pick (per user, 2026-09-03): bump plugins/presentation/.claude-plugin/plugin.json 0.10.0 -> 0.10.1 (PATCH). Rationale: CLAUDE.md grants MINOR only for a new skill or broadened triggers; a new opt-in CLI flag on an existing skill is neither, so it falls under 'patch for content tweaks'. Default behaviour is unchanged, which reinforces patch. Do NOT bump minor.

Plan: (1) Thread a keyword-only `fold_engine_artefacts` flag through diff_runs -> diff_shape -> compare_decks, and store it on Report. diff_runs is where the sole engine-artefact finding is emitted (the run-count line); when folding, it suppresses that line ONLY when the paragraph texts match, which is exactly the condition the existing annotation hedges on ('engine artefact if the text above matches'). No string-sniffing of formatted lines. (2) Because folded findings are never appended, report.diff_count and the 'Total:' line count only the remaining findings for free, and report.ok/exit-code 0 becomes the single-signal convergence check the task asks for. (3) format_report prints a note when folding is on, so a filtered report says so rather than silently hiding. (4) New CLI flag --fold-engine-artefacts (British spelling, matching the repo). (5) New fixture pair coalesced-ref.pptx / coalesced-gen.pptx from gen_fixtures.py: identical one-slide decks whose only difference is 1 run vs 3 identically-formatted runs. (6) Tests: fold->zero on the new pair, no-flag output unchanged on the old pair (pinning 3 findings), --help lists the flag. (7) SKILL.md section next to 'Reading the output'. (8) plugin.json 0.10.0 -> 0.10.1 per the recorded SemVer pick.

Handoff checklist (Source-carrying task): GREEN with one yellow — the 'How to reproduce the measurement' paths under /Users/paul/... are not mounted in this container, so the 73-vs-145 figures are taken as given from the task body rather than re-measured. They are context, not an acceptance criterion; every AC is checkable in-repo. All (exists) paths verified present, TASK-43 is Done.

Commit: `145420e` - task-44: add --fold-engine-artefacts to compare_decks.py

Commit: `8e2d0bd` - task-44: fold a run-count mismatch only when both sides coalesce alike

Commit: `14d11c9` - task-44: show the convergence check as an exit-code test, not a spin loop

Commit: `a2fbded` - task-44: note the positional run-pairing caveat on reaching zero

Done. Implemented --fold-engine-artefacts on compare_decks.py.

Design: the flag is threaded as a keyword-only argument through diff_runs -> diff_shape -> compare_decks and recorded on Report. Folded findings are never appended to SlideDiff.lines, so diff_count, the 'Total:' line, report.ok and the process exit code all count only what is left — restoring the single-signal convergence check (exit 0 == converged) the task asked for. format_report prints a header note when folding is on, so a filtered report always says it is filtered.

Fold gate (changed during review): the first implementation folded a run-count mismatch whenever the concatenated paragraph texts matched. The task-reviewer found that unsound and I reproduced it: the per-run loop uses zip(ref.runs, gen.runs), which truncates to the shorter side, so with 1 run against 3 the formatting of the extra runs is never inspected and the run-count line is their only trace — folding it hid a word that was bold on one side only. The fix adds _format_profile() and _coalesce(), which apply PowerPoint's own merge (adjacent runs with identical formatting) to BOTH sides, and folds only when the merged forms are equal. This is exact rather than heuristic: it subsumes text equality, folds legitimately coalesced mixed-format paragraphs (which a formatting-uniformity check would refuse), and refuses every case where formatting actually differs. _format_profile derives from dataclasses.fields(Run) minus 'text', so a field added to Run later joins the profile automatically — a direction that can only make the fold stricter. _coalesce sits behind the flag's short-circuit and is never called on the default path.

Default behaviour is unchanged and this was verified byte-for-byte, not merely by finding count: stdout, stderr, exit code and --report file bytes compared against 'git show master:compare_decks.py' across all fixture permutations, self-compares and --pos-tol 0.001/0.04/5.0 — zero differences. The reviewer independently repeated this over 20 cases.

Fixtures: gen_fixtures.py gained build_run_split() and writes coalesced-ref.pptx / coalesced-gen.pptx — one-slide decks whose only difference is 1 run vs 3 identically formatted runs. ref.pptx and gen.pptx were deliberately restored after regeneration: rebuilding them changes only zip timestamps, and committing that churn would obscure the diff.

Tests: 12 added (55 in the skill's suite, up from 43). Includes the flag-off pin required by AC #4, the fold-to-zero pair, exit-code convergence, and four gate tests — text differs, run-level difference with equal counts, formatting-differing split, and mixed-format split that must still fold. The reviewer mutation-tested the gate six ways and all six mutants were killed, and ran a 300k-case property fuzz over the soundness invariant: 46,700 folds fired, 0 unsound.

Review: APPROVED by the task-reviewer agent on the second pass (CHANGES REQUESTED on the first — the unsound gate above, plus one vacuous test which was replaced with a discriminating one asserting the exact surviving line).

Handoff assumption, as flagged in the plan: the task's 'How to reproduce the measurement' block cites /Users/paul/... host paths that are not mounted in this container, so the 73-vs-145 figures are taken as given from the task body rather than re-measured. They are motivation, not an acceptance criterion; all 8 ACs are checkable in-repo and were checked.

Version: plugins/presentation/.claude-plugin/plugin.json 0.10.0 -> 0.10.1, per the SemVer pick pinned in this task's notes (patch: a new opt-in CLI flag on an existing skill is neither a new skill nor a broadened trigger, and the default is unchanged). marketplace.json carries no per-plugin version key, so it needed no bump.

Follow-up: TASK-45 records an adjacent, pre-existing defect the review's fuzz surfaced — runs are paired positionally, so a paragraph split across a formatting boundary reports a spurious per-run mismatch. It is out of TASK-44's scope (it would change default output and so break AC #4) and it over-reports rather than hides, so it cannot cause a false 'converged'. SKILL.md carries a caveat paragraph about it as a stopgap.

Test gate: full suite 239 passed / 1 failed. The failure is test_decision_tree_helper in the untouched pptx-arch-style skill, needing a vendored node_modules that is absent in this container; it fails identically on master (baseline captured before any edit: 227 passed / 1 failed, same test).
<!-- SECTION:NOTES:END -->
