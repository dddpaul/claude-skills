# Feature Review: pptx-arch-style-validation

Generated 2026-06-20 by ralph-reviewer agent (third cumulative review, now covering TASK-21 + TASK-22 + TASK-23 + TASK-24).

In-scope tasks: TASK-21 (Done), TASK-22 (Done), TASK-23 (Done), TASK-24 (Done).
Diff range: a1c713e..HEAD — 35 files, 2720 insertions, 86 deletions.
Design documents: brainstorm only (no PRD).

Prior reviews:
- `design/pptx-arch-style-validation-review-2026-06-20.md` (TASK-21+22, flagged 3 drifts)
- `design/pptx-arch-style-validation-review-2026-06-20-01.md` (TASK-21+22+23, all 3 drifts resolved, Aligned)

---

## Verdict: Aligned

**Passes run:** 1 (brainstorm-derived intent matrix), 3 (brainstorm scope cuts), 5 (out-of-scope creep)
**Passes skipped:** 2 (no PRD — no Non-Goals section), 4 (no PRD — no Success Metrics section)

This review evaluates the **cumulative state** after TASK-21 + TASK-22 + TASK-23 + TASK-24, not the trajectory. TASK-24 was a handoff absorbing three canary findings from `stacks@8c6f4b88b7bb`; the brainstorm did not anticipate them, so they are evaluated as legitimate **feature extensions** (post-canary hardening) rather than scope creep.

## Intent → Implementation Matrix

Requirement IDs come from the brainstorm's locked decisions (`BR-*`), the TASK-23 follow-ups (`FU-*`), and the TASK-24 canary findings (`CN-*`).

| ID | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| BR-1 | Two-phase sequencing: spec audit before linter | Delivered | TASK-21 merged at `634d1c5` before TASK-22 began; `dependencies: TASK-21` on TASK-22 |
| BR-2 | Phase 1 produces `design/pptx-arch-style-audit.md` with three-bucket routing | Delivered | 42 findings, all bucketed (35 auto-fill / 3 from-deck / 4 ask-user) |
| BR-3 | Pass A: structural read-through, all `~` / "approximately" / numeric ranges flagged | Delivered | TASK-21 AC#2 verified; SKILL.md contains no remaining tildes/ranges in visual attributes |
| BR-4 | Pass B: cross-reference real Alfa decks newest-first, stop on saturation | Delivered (caveat) | 2 of 7 decks inspected; audit doc explicitly states "saturation NOT reached" — early stop justified as "sufficient for ask-user decisions"; AC#5 only required ≥1 deck |
| BR-5 | ask-user batch in a single message, decisions captured verbatim | Delivered | "Ask-user batch — RESOLVED (2026-06-20)" section enumerates 4 decisions verbatim |
| BR-6 | Ask-user #1: Rule #11 weakened to bgPr-only | Delivered | SKILL.md Rule #11 rewritten; rules.yaml `background-effectLst-override` checks `<p:bgPr>` only |
| BR-7 | Ask-user #2: off-palette colors WARN + remap | Delivered (closed by TASK-23) | `palette-fill-warning` rule (severity: warning) + `palette-fill-warning.pptx` fixture; remap table in SKILL.md "Colors outside the palette" |
| BR-8 | Ask-user #3: extend Size Scale (13/16/20/36); 5pt forbidden | Delivered | SKILL.md Size Scale: `7, 8, 9, 10, 10.5, 11, 12, 13, 14, 15, 16, 20, 24, 28, 32, 36, 40.5, 52` with role carve-outs; rules.yaml matches exactly |
| BR-9 | Ask-user #4: tree connectors 1.0pt parity with flow | Delivered | SKILL.md Decision Tree: `Line: 1.0pt solid #595959 (parity with flow arrows)` |
| BR-10 | Slide classification via explicit speaker-notes tag, never heuristic | Delivered | `KIND_RE` in lint.py; untagged slides → hard error; SKILL.md Validation step 5 mandates tag |
| BR-11 | Linter is output-level (.pptx), one tool for pptxgenjs + python-pptx | Delivered | lint.py uses `Presentation()` from python-pptx; no source-level AST inspection |
| BR-12 | 8 rule types each represented with `spec_ref` | Delivered | 11 rules in rules.yaml, all 8 types covered, every rule has `spec_ref`; meta-tests enforce both |
| BR-13 | YAML rules separate from code, hand-editable, inches not EMU | Delivered | `references/rules.yaml`; lint.py converts via `EMU_PER_INCH`; default `coord_tolerance_in: 0.005` |
| BR-14 | CLI `uv run scripts/lint.py deck.pptx`, exit 0/1/2, `--json` | Delivered | `main()` supports `--json`, `--rules`; exit-code-2 path now exercised by palette-fill-warning fixture |
| BR-15 | Text report grouped by slide with rule id / expected / actual / spec ref | Delivered | `format_text()` produces brainstormed structure |
| BR-16 | Validation gate added as final SKILL.md section, 4-step protocol | Delivered (extended to 5 steps) | TASK-24 added step 1 (postprocess-effectlst.py) ahead of the original 4 — same protocol, longer pipeline |
| BR-17 | Fixtures regenerable from committed gen script | Delivered | `gen_fixtures.js`; TASK-23 verified it still works after move to `scripts/tests/` |
| BR-18 | Golden + violators + edge tolerance fixtures | Delivered | 1 golden + 11 violators + 2 edge + 1 palette-warning = 15 fixtures |
| BR-19 | `plugin.json` minor bump per task | Delivered | `0.1.1 → 0.2.0 → 0.3.0 → 0.4.0 → 0.5.0` — each bump justified |
| BR-20 | ruff + pytest green; task-reviewer APPROVED before each merge | Delivered | All four tasks have APPROVED notes; AC#7/#8 checked off |
| FU-1 (TASK-23) | Off-palette warn rule shipped | Delivered | See BR-7 |
| FU-2 (TASK-23) | rules.yaml `sizes_pt` reconciled with SKILL.md Size Scale | Delivered | Both contain identical superset; role carve-outs documented |
| FU-3 (TASK-23) | `package.json`/`package-lock.json` moved out of repo root | Delivered | Both under `scripts/tests/`; root has no `package*.json`; `.gitignore` scopes `node_modules/` |
| CN-1 (TASK-24) | Title-zone height fix for 24pt 2-line wraps (Finding #1) | Delivered | SKILL.md title text box `h=0.85`, subtitle `y=0.78`; ASCII diagram updated; EMU table adds `0.850" = 777240 EMU` and tags `0.626"` as legacy |
| CN-2 (TASK-24) | Ship canonical `postprocess-effectlst.py` (Finding #2) | Delivered | `plugins/presentation/skills/pptx-arch-style/scripts/postprocess-effectlst.py` exists (3.1 KB); SKILL.md Rule #11 and Validation step 1 reference it; 4 pytest cases in `test_postprocess_effectlst.py` |
| CN-3 (TASK-24) | 22pt migration note (Finding #3) | Delivered | SKILL.md Size Scale section: "Content slide titles MUST be 24pt, not the legacy 22pt … re-emit the title at 24pt rather than re-adding 22pt to the scale. Long titles must be split into title + subtitle to avoid a 2-line wrap" |
| CN-4 (TASK-24) | Version bump per material change | Delivered | `0.4.0 → 0.5.0` (minor — new shipped script qualifies as feature per CLAUDE.md SemVer) |

## Non-Goal Violations

Pass 2 skipped — no PRD with explicit Non-Goals section.

## Scope Cut Violations (Pass 3)

Brainstorm's explicit scope cuts re-verified against the cumulative diff:

1. No static code linter — **respected** (lint.py reads .pptx only; postprocess-effectlst.py reads/writes the .pptx package directly, never the generator source)
2. No semantic checks — **respected**
3. No aesthetic checks (overlap/balance/density) — **respected** (all rules remain mechanical)
4. No content QA — **respected**
5. No auto-fix mode in v1 — **respected with one nuance**: `postprocess-effectlst.py` *does* mutate the input deck (it adds missing `<a:effectLst/>` siblings). However, this is **not lint auto-fix** — it is a pre-lint **generator-gap shim** that compensates for a pptxgenjs v4.0.1 limitation (the spec says the override must exist; pptxgenjs cannot emit it). The script is positioned as step 1 of the Validation pipeline, *before* the linter runs, not as a linter mode. The brainstorm's "no auto-fix" cut concerned the linter; the shim does not violate it. (Worth noting in case future work blurs the boundary.)
6. No `pptx-core-style` coverage in this iteration — **respected** (no edits under `plugins/presentation/skills/pptx-core-style/`)

**None detected.**

## Success Metric Assessment

Pass 4 skipped — no PRD with Success Metrics section.

## Drift List (Pass 5)

The three drifts flagged by the first cumulative review were closed by TASK-23 (size-scale reconciliation, package.json placement, .gitignore scoping). The TASK-24 diff was scanned for new drift:

- `plugins/presentation/skills/pptx-arch-style/scripts/postprocess-effectlst.py` — traces to CN-2; in-scope
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/test_postprocess_effectlst.py` — supports CN-2; in-scope
- SKILL.md edits at lines 87, 141, 154–155, 510–511, 533–534 — trace to CN-1, CN-2, CN-3; all in-scope
- `plugins/presentation/.claude-plugin/plugin.json` 0.4.0 → 0.5.0 — CN-4

**No drift detected.** The TASK-24 diff is small and entirely traceable to the three canary findings plus the version bump.

## Reviewer Notes

**Brainstorm intent fully realized, plus a documented post-canary hardening pass.** TASK-21/22/23 delivered the two-phase architecture exactly as scoped. TASK-24 absorbed three real-world consumer findings without violating any scope cut or non-goal — the canary feedback loop the brainstorm implicitly relied on (validate via stacks consumption) closed cleanly.

**Architectural coherence of the TASK-24 additions:**

- `postprocess-effectlst.py` lives next to `lint.py` under `scripts/` (not `references/`), which matches its operational role. Its PEP-723 inline-deps header lets it run via `uv run` without project-level dep mutation. The Validation gate in SKILL.md now ties the two scripts into a single pipeline: postprocess (only when generator is pptxgenjs) → lint → visual QA.
- The 22pt migration note (CN-3) is a *guidance* edit rather than a *rule* edit — the linter still rejects 22pt via the existing `text-runs-use-approved-font-and-size` rule. SKILL.md now tells the consumer exactly why and how to remediate. This is the right level of intervention: re-admitting 22pt would have reopened the wrap problem that CN-1 fixes.
- CN-1 (title-zone h=0.85 + subtitle y=0.78) was applied consistently across the spec: prose, ASCII diagram, and the EMU reference table. The legacy 0.626" height is tagged "legacy" rather than removed, preserving traceability for hand-authored decks still using it.

**Brainstorm caveat unchanged (Pass B saturation).** TASK-21 sampled 2 of 7 curated decks; the brainstorm's stop-on-saturation rule was relaxed to "sufficient for ask-user decisions." This was acceptable in the prior reviews, remains acceptable now, and TASK-24's canary effectively retroactively validated the audit by surfacing only three additional findings (all narrow) from a real fresh consumer deck — exactly the signal the under-sampled Pass B would have hoped for.

**Versioning trajectory remains SemVer-consistent.** Four minor bumps across four merged tasks (`0.1.1 → 0.5.0`). Each step is justified per CLAUDE.md: broadened spec coverage (TASK-21), new skill content (TASK-22), Size Scale extension (TASK-23), new shipped script (TASK-24). No major bump needed — no renames or removals.

**Spec/rule consistency cross-check.** After TASK-24:
- `sizes_pt` in rules.yaml still matches SKILL.md Size Scale (no regression from CN-3, which deliberately avoided adding 22pt)
- The 5-step Validation gate in SKILL.md correctly references `postprocess-effectlst.py` by relative path
- Rule #11 in SKILL.md acknowledges the pptxgenjs gap and links forward to the Validation section — matches AC#2 of TASK-24 verbatim

**Handoff hygiene observation.** TASK-24 is properly self-contained: its description carries the three findings inline, the Source line correctly points at the upstream stacks repo + commit (not at this project's brainstorm), and the "Before starting" validation checklist is present. Consistent with the user's prior feedback on Ralph handoff hygiene.

**Bottom line.** The feature is **Aligned**. Brainstorm intent is fully delivered; the off-palette warn-and-remap policy is enforced (no longer Partial); the post-canary findings are absorbed without scope creep; the two-phase architecture, validation gate, fixture regenerability, and spec_ref traceability remain intact. No outstanding follow-ups are required from this review.
