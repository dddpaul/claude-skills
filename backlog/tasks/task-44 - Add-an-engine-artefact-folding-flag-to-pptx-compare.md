---
id: TASK-44
title: Add an engine-artefact folding flag to pptx-compare
status: In Progress
assignee: []
created_date: '2026-09-03 17:19'
updated_date: '2026-09-03 17:31'
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
<!-- SECTION:NOTES:END -->
