# Feature Review: pptx-arch-style-validation

Generated 2026-06-20 by ralph-reviewer agent.

In-scope tasks: TASK-21 (Done, merge 634d1c5), TASK-22 (Done, merge 93f6dc7).
Diff range: a1c713e..HEAD — 28 files, 2033 insertions.
Design documents: brainstorm only (no PRD).

---

## Verdict: Aligned (with one notable partial decision and a few minor gaps)

**Passes run:** 1, 3, 5
**Passes skipped:** 2 (no PRD — design is brainstorm-only, no Non-Goals section in PRD sense), 4 (no PRD/Success-Metrics section)

Note on Pass 5: although there is no PRD, the brainstorm exists, so Pass 5 (out-of-scope creep against brainstorm + task ACs) ran normally.

## Intent → Implementation Matrix

Brainstorm requirements treated as the requirement IDs.

| ID | Requirement (from brainstorm / locked decisions) | Status | Evidence |
|---|---|---|---|
| BR-1 | Two-phase sequencing: spec audit (Phase 1) before linter (Phase 2) | Delivered | TASK-21 merged at 634d1c5 before TASK-22 work began; TASK-22's `dependencies: TASK-21` |
| BR-2 | Phase 1 produces `design/pptx-arch-style-audit.md` with three-bucket routing | Delivered | `design/pptx-arch-style-audit.md` — 41+1 findings, all marked auto-fill / from-deck / ask-user |
| BR-3 | Pass A structural read-through of SKILL.md, all `~`, "approximately", numeric ranges, and missing attributes flagged | Delivered | Audit rows #1–#33 (Pass A) cover tildes, "0.65–0.70", "9-10pt", "100-115%", "thin", etc.; AC#2 of TASK-21 verifies absence post-merge |
| BR-4 | Pass B cross-references real Alfa decks (newest-first, stop on saturation) | Delivered (with caveat) | 2 of 7 decks inspected (channels-definition-arch, equation/core/doc-3). Audit explicitly states "saturation NOT reached"; decision documented as deliberate early-stop |
| BR-5 | ask-user batch in a single message, decisions captured verbatim | Delivered | Audit doc "Ask-user batch — RESOLVED (2026-06-20)" section enumerates the 4 decisions verbatim |
| BR-6 | Ask-user resolution #1: Rule #11 weakened to bgPr-only | Delivered | SKILL.md line 528 rewrites Rule #11 ("slide background MUST carry `<a:effectLst/>` inside `<p:bgPr>` … per-shape NOT required"); rules.yaml `background-effectLst-override` checks `<p:bgPr>` only via `bg_has_effectLst()` in lint.py |
| BR-7 | Ask-user resolution #2: off-palette colors WARN + remap | **Partial** | SKILL.md "Colors outside the palette" section documents the warn-and-remap policy and includes the remap table; **but** rules.yaml ships no rule that emits `severity: warning` for non-palette colors. All 10 rules are `severity: error`. The exit-code-2 path exists in lint.py but is dead code under the current ruleset. The only color rule (`brand-red-must-use-F12D16`) is error-severity and matches only 4 hard-coded near-red hexes on the red-line shape — not a general palette check |
| BR-8 | Ask-user resolution #3: size scale extended with 13/16/20/36, 5pt forbidden | Delivered | SKILL.md Size Scale line 84: "8, 9, 10, 10.5, 11, 12, **13**, 14, 15, **16**, **20**, 24, **36**, 40.5, 52"; rules.yaml `text-runs-use-approved-font-and-size` `sizes_pt` list contains those values. (Linter list additionally includes 7, 28, 32 — see drift list.) |
| BR-9 | Ask-user resolution #4: tree connectors 1.0pt (parity with flow) | Delivered | SKILL.md Decision Tree section line 411: `Line: 1.0pt solid #595959 (parity with flow arrows)` |
| BR-10 | Slide classification via explicit speaker-notes tag, never heuristic | Delivered | `KIND_RE = re.compile(r"<!--\s*arch-style:(content\|title\|section)\s*-->")` in lint.py; `slide_kind()` reads notes only; SKILL.md Validation step 4 mandates the tag; untagged slides flagged as hard error |
| BR-11 | Linter is output-level (.pptx), one tool for pptxgenjs + python-pptx | Delivered | lint.py reads with `Presentation()` from python-pptx; no source-AST inspection anywhere |
| BR-12 | 8 rule types each represented in rules.yaml with `spec_ref` | Delivered | `test_every_rule_type_has_at_least_one_rule` and `test_every_rule_has_spec_ref` enforce both; 10 rules, all 8 types covered, all carry spec_ref |
| BR-13 | YAML rules separate from code, hand-editable, inches not EMU | Delivered | `references/rules.yaml`; lint.py converts via `EMU_PER_INCH`; default `coord_tolerance_in: 0.005` |
| BR-14 | CLI `uv run scripts/lint.py deck.pptx` with exit 0/1/2 and `--json` | Delivered | `main()` in lint.py supports `--json`, `--rules`, returns 0/1/2 per `exit_code()` |
| BR-15 | Text report grouped by slide with rule id / expected / actual / spec ref | Delivered | `format_text()` produces exactly the brainstormed structure |
| BR-16 | Validation gate added to SKILL.md as final section, 4-step protocol | Delivered | SKILL.md lines 530–549 — last section in document, contains all 4 steps as specified |
| BR-17 | Fixtures are regenerable, not opaque blobs — committed gen script | Delivered | `gen_fixtures.js` (419 lines) reproduces every fixture from source; reviewer can audit |
| BR-18 | Golden + violators + edge tolerance fixtures | Delivered | 1 golden + 11 violators + 2 edge = 14 fixtures, matches the brainstorm's three buckets |
| BR-19 | `plugin.json` minor bump per task | Delivered (over-bumped) | `presentation/.claude-plugin/plugin.json` went `0.1.1 → 0.3.0`. Two minor bumps would have landed at `0.3.0` only if each bump was minor; checks out (`0.1.1 → 0.2.0` after TASK-21, `0.2.0 → 0.3.0` after TASK-22). Consistent with CLAUDE.md SemVer rule "minor for new skills or broadened triggers" — broadened spec coverage + new linter feature |
| BR-20 | ruff + pytest green; task-reviewer APPROVED before merge | Delivered | Both tasks have APPROVED notes; AC#7/#8 checked off; merge commits 634d1c5 and (per TASK-22 notes) 04a020f |

## Non-Goal Violations / Scope Cut Violations

Pass 2 skipped (no PRD with explicit non-goals). Pass 3 (brainstorm scope cuts) ran.

The brainstorm's explicit scope cuts:

1. No static code linter → **respected** (lint.py reads .pptx only, no JS/Python AST anywhere).
2. No semantic checks → **respected** (no NLP, no topic checks).
3. No aesthetic checks (overlap, balance, density) → **respected** (rules are mechanical only).
4. No content QA (typos, missing sections) → **respected**.
5. No auto-fix mode in v1 → **respected** (lint.py only reports; no mutation of input deck anywhere).
6. No `pptx-core-style` coverage in this iteration → **respected** (no edits to `plugins/presentation/skills/pptx-core-style/`).

**None detected.**

## Drift List (Pass 5)

Most of the diff traces cleanly to brainstorm/audit/AC. Three items deserve flagging:

1. **`scripts/lint.py` font_spec rule list contains 7, 28, 32 pt — sizes NOT in the resolved Size Scale.** SKILL.md line 84 says the approved set is `8, 9, 10, 10.5, 11, 12, 13, 14, 15, 16, 20, 24, 36, 40.5, 52`. rules.yaml `sizes_pt: [7, 8, 9, 10, 10.5, 11, 12, 13, 14, 15, 16, 20, 24, 28, 32, 36, 40.5, 52]` extends that with 7 (protocol-label size from Diagram Conventions), 28 and 32 (stat-callout big-number sizes). Tracable: those sizes are used in fixture-conformant content (gen_fixtures big number 32pt at title slide; protocol labels 7pt in diagram spec). Not unjustified, but the SKILL.md Size Scale row should be reconciled to either (a) add 7/28/32 to the approved set, or (b) carve out an exception for stat-callout/protocol-label roles. Currently the spec and the linter disagree about whether 7/28/32 are allowed.

2. **`package-lock.json` and `package.json` at repo root** for `pptxgenjs` + `jszip`. These exist solely to make `node gen_fixtures.js` runnable; AC#4 requires the script run deterministically. Reasonable infra, but lives at repo root rather than under the skill — a future Node-using skill in another plugin would collide. Not a brainstorm violation, just a placement remark.

3. **`.gitignore` adds `node_modules/`** — same node infra dependency. Trivially in-scope.

No drift in SKILL.md edits — every change maps to an audit row (verified by section anchors: Color Palette, Font Pairing, Size Scale, Section Divider, Component Styles, Stat Callouts, Group Headers + Category Rows, Dashed Separator, Table Styles, Diagram Conventions, Dynamic Layout Formulas, Rule #11, and the new Validation section).

## Reviewer Notes

**One real partial: off-palette color warning is documented but not enforced (BR-7).**

The ask-user decision #2 was unambiguous: "**Warn + remap** — linter emits warning on any non-palette hex; generator must map MD colors to closest spec equivalent." TASK-22 implemented the documentation side (SKILL.md "Colors outside the palette" table) and the remap mapping table, but did not ship a rule that scans every shape's fill against the palette set and emits a `severity: warning`. The only color rule (`brand-red-must-use-F12D16`) is narrow:
- It's `severity: error`, not `warning`
- It matches only on the red-line shape (`h_max: 0.10, w_min: 9.50`)
- It only checks against 4 hard-coded near-reds (`FF0000, EE0000, F00000, FF1A1A`)

A real deck with Material-Design `#2196F3` filling a content box would lint green today. The exit-code-2 path (`warnings only`) is therefore dead code in the current ruleset. Recommend adding a `fill_color` rule of type `severity: warning` that scans all shapes for hex values not in a `palette_in: [...]` allowlist drawn from the Color Palette section. This is the one ask-user decision that did not fully materialize.

**Pass B sampled 2 of 7 decks instead of running to saturation.** The audit doc is transparent about this ("Saturation NOT reached"), and the early-stop logic is defensible — the second deck already produced a different rectRadius distribution and surfaced the ask-user issues. However, BR-4 in the brainstorm explicitly says "stop early on saturation … (no new combinations in 2 consecutive decks)." The trigger here was not saturation but "sufficient for ask-user decisions." Acceptable in spirit, but worth noting that decks #2, #3, #5, #6, #7 were not inspected, so additional spec gaps may remain unsurfaced. AC#5 only required ≥1 deck, so the AC passes; the brainstorm intent was looser.

**Consistency check on spec_ref pointers (cross-task):** all 10 `spec_ref` strings resolve to real, present anchors in the updated SKILL.md:
- `Rule #1, #2, #3, #11` — present at lines 518, 519, 520, 528
- `Color Palette (Red brand #F12D16)` — present at line 15+
- `Red Highlight Markers (2.25pt #FF0000)` — present at line 230
- `Typography (Font Pairing & Size Scale)` — present at lines 69, 83
- `Section Divider Slide (centered text)` — present at line 169
- `Validation gate (speaker-notes tagging)` — present at line 530 (referenced from untagged-slide handler in lint.py)

**No TASK-22 re-decisions of locked TASK-21 items.** rules.yaml respects every audit resolution: Rule #11 narrowed to bg only; extended size scale present; section text alignment = center matches Section Divider section. The font face list (`Arial, Roboto Condensed, Arial Narrow, Helvetica`) accepts the Helvetica fallback documented in TASK-21's Font Pairing table.

**Fixture coverage is coherent.** 14 fixtures = golden (3 slides, all kinds) + 11 violators (one per rule, plus untagged-slide as 11th since `untagged` is a control-flow path not a rule) + 2 edge (0.003in passes, 0.010in fails under 0.005 tolerance). Each violator isolates exactly one rule failure — verified by parametrized `test_violator_reports_expected_rule`. The brainstorm asked for "one .pptx per violation type" — delivered.

**Bottom line:** the feature is **Aligned** — the two-phase architecture is intact, the gate exists, the 8 rule types are present, every spec_ref resolves, fixtures are regenerable, and all but one ask-user decision was implemented end-to-end. The off-palette-color warning gap (BR-7) and the size-scale 7/28/32 reconciliation (drift #1) are the only items worth a follow-up task. Neither is a blocker for shipping the validation gate.
