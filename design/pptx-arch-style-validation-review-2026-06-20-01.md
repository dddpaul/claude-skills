# Feature Review: pptx-arch-style-validation

Generated 2026-06-20 by ralph-reviewer agent (second cumulative review, now covering TASK-21 + TASK-22 + TASK-23).

In-scope tasks: TASK-21 (Done), TASK-22 (Done), TASK-23 (Done).
Diff range: a1c713e..HEAD — 31 files, 2314 insertions, 82 deletions.
Design documents: brainstorm only (no PRD).

Prior review (TASK-21 + TASK-22 only): `design/pptx-arch-style-validation-review-2026-06-20.md`.

---

## Verdict: Aligned

**Passes run:** 1 (brainstorm-derived intent matrix), 3 (brainstorm scope cuts), 5 (out-of-scope creep)
**Passes skipped:** 2 (no PRD — no Non-Goals section), 4 (no PRD — no Success Metrics section)

## Intent → Implementation Matrix

Requirement IDs are derived from the brainstorm's locked decisions and the prior review's `BR-*` numbering, extended to cover the TASK-23 follow-up scope (FU-*).

| ID | Requirement (brainstorm / locked decision / follow-up) | Status | Evidence |
|----|---|---|---|
| BR-1 | Two-phase sequencing: spec audit before linter | Delivered | TASK-21 merged at `634d1c5` before TASK-22 began; `dependencies: TASK-21` on TASK-22 |
| BR-2 | Phase 1 produces `design/pptx-arch-style-audit.md` with three-bucket routing | Delivered | `design/pptx-arch-style-audit.md` — 42 findings, all bucketed (35 auto-fill / 3 from-deck / 4 ask-user) |
| BR-3 | Pass A: structural read-through, all `~`/"approximately"/numeric ranges/missing attributes flagged | Delivered | TASK-21 AC#2 checked; SKILL.md contains no remaining tildes/ranges in visual attributes (verified by `9208751` reviewer-fix commit) |
| BR-4 | Pass B: cross-reference real Alfa decks newest-first, stop on saturation | Delivered (with documented caveat) | 2 of 7 decks inspected; audit doc explicitly states "saturation NOT reached" — early stop justified as "sufficient for ask-user decisions". AC#5 only required ≥1 deck (satisfied) |
| BR-5 | ask-user batch in a single message, decisions captured verbatim | Delivered | "Ask-user batch — RESOLVED (2026-06-20)" section in audit doc enumerates 4 decisions verbatim |
| BR-6 | Ask-user #1: Rule #11 weakened to bgPr-only | Delivered | `SKILL.md` Rule #11 rewritten; rules.yaml `background-effectLst-override` checks `<p:bgPr>` only via `bg_has_effectLst()` in lint.py |
| BR-7 | Ask-user #2: off-palette colors WARN + remap | **Delivered** (closed by TASK-23) | `palette-fill-warning` rule in rules.yaml with `severity: warning` and `fill_not_in: [40+ palette hexes]`; `palette-fill-warning.pptx` fixture; verified exit code 2 (per TASK-23 reviewer note). SKILL.md "Colors outside the palette" remap table also present |
| BR-8 | Ask-user #3: extend Size Scale with 13/16/20/36; 5pt forbidden | Delivered | SKILL.md Size Scale line includes 7, 8, 9, 10, 10.5, 11, 12, 13, 14, 15, 16, 20, 24, 28, 32, 36, 40.5, 52 with role-specific carve-outs for 7/28/32. rules.yaml `sizes_pt` matches exactly |
| BR-9 | Ask-user #4: tree connectors 1.0pt parity with flow | Delivered | SKILL.md Decision Tree → `Line: 1.0pt solid #595959 (parity with flow arrows)` |
| BR-10 | Slide classification via explicit speaker-notes tag, never heuristic | Delivered | `KIND_RE = re.compile(r"<!--\s*arch-style:(content\|title\|section)\s*-->")` in lint.py; untagged slides → hard error; SKILL.md Validation step 4 mandates tag |
| BR-11 | Linter is output-level (.pptx), one tool for pptxgenjs + python-pptx | Delivered | lint.py uses `Presentation()` from python-pptx; no source-level AST inspection |
| BR-12 | 8 rule types each represented with `spec_ref` | Delivered | 11 rules in rules.yaml, all 8 types covered, every rule has `spec_ref`; meta-tests in `test_lint.py` enforce both |
| BR-13 | YAML rules separate from code, hand-editable, inches not EMU | Delivered | `references/rules.yaml`; lint.py converts via `EMU_PER_INCH`; default `coord_tolerance_in: 0.005` |
| BR-14 | CLI `uv run scripts/lint.py deck.pptx`, exit 0/1/2, `--json` | Delivered | `main()` supports `--json`, `--rules`, `exit_code()` returns 0/1/2 correctly. Exit-code-2 path is no longer dead — exercised by `palette-fill-warning.pptx` |
| BR-15 | Text report grouped by slide with rule id / expected / actual / spec ref | Delivered | `format_text()` produces brainstormed structure |
| BR-16 | Validation gate added as final SKILL.md section, 4-step protocol | Delivered | SKILL.md ends with "Validation" section containing all 4 steps |
| BR-17 | Fixtures regenerable from committed gen script | Delivered | `gen_fixtures.js` (~444 lines); TASK-23 AC#6 verifies it still works after move to `scripts/tests/` |
| BR-18 | Golden + violators + edge tolerance fixtures | Delivered | 1 golden + 11 violators (one per rule + untagged) + 2 edge = 14 fixtures |
| BR-19 | `plugin.json` minor bump per task | Delivered | `0.1.1 → 0.2.0` (TASK-21), `→ 0.3.0` (TASK-22), `→ 0.4.0` (TASK-23 — minor because Size Scale extended) |
| BR-20 | ruff + pytest green; task-reviewer APPROVED before each merge | Delivered | All three tasks have APPROVED notes; AC#7/#8 checked off per task |
| FU-1 (TASK-23) | Off-palette warn rule shipped (closes BR-7 partial from prior review) | Delivered | See BR-7 above — `palette-fill-warning` rule + fixture + exit-code-2 path |
| FU-2 (TASK-23) | rules.yaml `sizes_pt` reconciled with SKILL.md Size Scale | Delivered | Both contain identical superset `{7, 8, 9, 10, 10.5, 11, 12, 13, 14, 15, 16, 20, 24, 28, 32, 36, 40.5, 52}`; role carve-outs documented in SKILL.md |
| FU-3 (TASK-23) | `package.json`/`package-lock.json` moved out of repo root | Delivered | Both now under `plugins/presentation/skills/pptx-arch-style/scripts/tests/`; root has no `package*.json`; `.gitignore` scopes `node_modules/` to that subpath |

## Non-Goal Violations

Pass 2 skipped — no PRD with explicit Non-Goals section.

## Scope Cut Violations (Pass 3)

Brainstorm's explicit scope cuts:

1. No static code linter — **respected** (lint.py reads .pptx only, no JS/Python AST inspection anywhere)
2. No semantic checks — **respected** (no NLP, no topic checks)
3. No aesthetic checks (overlap/balance/density) — **respected** (rules are mechanical only)
4. No content QA (typos, missing sections) — **respected**
5. No auto-fix mode in v1 — **respected** (lint.py reports only; no mutation of input deck; TASK-23 explicitly listed auto-fix as out-of-scope)
6. No `pptx-core-style` coverage in this iteration — **respected** (no edits to `plugins/presentation/skills/pptx-core-style/`)

**None detected.**

## Success Metric Assessment

Pass 4 skipped — no PRD with Success Metrics section.

## Drift List (Pass 5)

The prior review (`design/pptx-arch-style-validation-review-2026-06-20.md`) flagged three drifts. All three are now resolved:

1. **(was drift #1) Size-scale reconciliation 7/28/32pt** — RESOLVED by TASK-23 (FU-2). SKILL.md Size Scale row now lists the full superset with explicit role carve-outs ("7pt allowed for protocol labels … 28/32pt allowed for stat-callout big numbers only"). The linter and the spec agree.
2. **(was drift #2) `package.json`/`package-lock.json` at repo root** — RESOLVED by TASK-23 (FU-3). Both files moved under `scripts/tests/`; `.gitignore` scoped accordingly.
3. **(was drift #3) `.gitignore` adds repo-root `node_modules/`** — RESOLVED by TASK-23 (FU-3). The root entry was removed and replaced with the scoped path.

**No new drift detected** in TASK-23. The diff for TASK-23 is small and entirely traceable to its three follow-up scopes: rules.yaml addition, fixture addition, SKILL.md Size Scale row + carve-outs, file moves, and the version bump.

## Reviewer Notes

This review evaluates the **current state** of the feature after TASK-23, not the trajectory. The prior review's three drifts have all been mechanically closed, and the one real "Partial" (BR-7 off-palette warn) is now fully delivered:

- `palette-fill-warning` is a `severity: warning` `fill_color` rule applied to all three slide kinds.
- The `fill_not_in` allowlist enumerates ~40 palette hexes drawn directly from the SKILL.md Color Palette section, matching what TASK-23's plan documented.
- A dedicated `palette-fill-warning.pptx` fixture exercises the rule and the previously-dead exit-code-2 path.
- The remap table for MD blue/green/orange/purple is documented in SKILL.md's "Colors outside the palette" section, so generators have an actionable mapping when the warning fires.

**Pass B saturation caveat is unchanged but still acceptable.** TASK-21 inspected 2 of 7 curated decks; BR-4's preferred stop condition was "no new combinations in 2 consecutive decks" but the actual stop trigger was "sufficient for ask-user decisions." AC#5 only required ≥1 deck, so the AC passes; the brainstorm's looser intent remains under-served. This was not picked up as a follow-up in TASK-23 (TASK-23's "Out of scope" explicitly defers Alfa-deck validation to a handoff TASK-57 in the stacks project), which is a reasonable scope boundary.

**Consistency cross-check.** All 11 `spec_ref` pointers in rules.yaml resolve to real sections in the updated SKILL.md (Rule #1/2/3/11, Color Palette, Red Highlight Markers, Typography, Section Divider Slide, Validation gate, Color Palette → Colors outside the palette). The font-spec face list (`Arial, Roboto Condensed, Arial Narrow, Helvetica`) is consistent with TASK-21's Font Pairing table including the Helvetica fallback chain.

**Plugin versioning is consistent with CLAUDE.md SemVer rules.** Three minor bumps (0.1.1 → 0.2.0 → 0.3.0 → 0.4.0), each justified: broadened spec coverage (TASK-21), new linter skill content (TASK-22), Size Scale extension (TASK-23).

**Bottom line:** the feature is fully aligned with the brainstorm and the locked ask-user decisions. The two-phase architecture is intact, the gate is enforced, all 8 rule types are represented, the off-palette warn-and-remap policy is now both documented and enforced, fixtures are regenerable, Node infra is properly scoped, and every `spec_ref` resolves. No outstanding follow-ups are required from this review.
