---
id: TASK-45
title: 'Compare paragraphs on their coalesced runs, not by raw position'
status: To Do
assignee: []
created_date: '2026-09-03 17:46'
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
- [ ] #1 A paragraph split at a different point than the reference, but character-identical, reports no per-run difference
- [ ] #2 A genuine per-run formatting difference is still reported when the splits differ
- [ ] #3 A regression test covers the bold-label/split-value case from the description
- [ ] #4 uv run pytest on plugins/presentation/skills/pptx-compare passes green
- [ ] #5 uv run ruff check . passes green
- [ ] #6 The SKILL.md caveat paragraph under 'Folding engine artefacts' is removed
- [ ] #7 version in plugins/presentation/.claude-plugin/plugin.json is bumped per the SemVer rule in CLAUDE.md
<!-- AC:END -->
