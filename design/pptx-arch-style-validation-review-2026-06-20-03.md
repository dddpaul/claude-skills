# Feature Review: pptx-arch-style-validation

Generated 2026-06-20 by ralph-reviewer agent (fourth cumulative review, now covering TASK-21 + TASK-22 + TASK-23 + TASK-24 + TASK-25).

In-scope tasks: TASK-21 (Done), TASK-22 (Done), TASK-23 (Done), TASK-24 (Done), TASK-25 (Done).
Diff range: `a1c713e..HEAD` — diff bundle truncated at 100k chars (full ~244k).
Design documents: brainstorm only (no PRD).

Prior reviews:
- `design/pptx-arch-style-validation-review-2026-06-20.md` (TASK-21+22, flagged 3 drifts + 1 partial)
- `design/pptx-arch-style-validation-review-2026-06-20-01.md` (TASK-21+22+23, all 3 drifts resolved, Aligned)
- `design/pptx-arch-style-validation-review-2026-06-20-02.md` (TASK-21+22+23+24, Aligned)

---

## Verdict: Aligned

**Passes run:** 1 (brainstorm-derived intent matrix), 3 (brainstorm scope cuts), 5 (out-of-scope creep)
**Passes skipped:** 2 (no PRD — no Non-Goals section), 4 (no PRD — no Success Metrics section)

TASK-25 was the second canary-driven handoff from `/Users/paul/Private/Alfa/Projects/standard/stacks` (sibling to TASK-24). The brainstorm did not anticipate a Decision-Tree component recipe — it appeared first as ask-user gap #33 inside the spec audit and was implicitly extended by the consumer's slide-4 defect catalog. The new component is evaluated here as a legitimate **post-canary feature extension** rather than scope creep.

## Intent → Implementation Matrix

Requirement IDs come from the brainstorm's locked decisions (`BR-*`), the TASK-23 follow-ups (`FU-*`), the TASK-24 canary findings (`CN-*`), and the TASK-25 decision-tree handoff (`DT-*`).

| ID | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| BR-1 | Two-phase sequencing: spec audit before linter | Delivered | TASK-21 merged before TASK-22 began; `dependencies: TASK-21` on TASK-22 |
| BR-2 | Phase 1 produces `design/pptx-arch-style-audit.md` with three-bucket routing | Delivered | 42 findings, all bucketed (35 auto-fill / 3 from-deck / 4 ask-user) |
| BR-3 | Pass A: structural read-through, all `~`/"approximately"/numeric ranges flagged | Delivered | SKILL.md contains no remaining tildes/ranges in visual attributes |
| BR-4 | Pass B: cross-reference real Alfa decks newest-first, stop on saturation | Delivered (caveat) | 2 of 7 decks inspected; audit doc states "saturation NOT reached"; AC#5 only required ≥1 deck. Caveat retroactively validated by two canary cycles (TASK-24, TASK-25) surfacing only narrow gaps |
| BR-5 | ask-user batch in a single message, decisions captured verbatim | Delivered | "Ask-user batch — RESOLVED (2026-06-20)" enumerates 4 decisions verbatim |
| BR-6 | Ask-user #1: Rule #11 weakened to bgPr-only | Delivered | SKILL.md Rule #11 rewritten; `background-effectLst-override` rule checks `<p:bgPr>` only |
| BR-7 | Ask-user #2: off-palette colors WARN + remap | Delivered (closed by TASK-23) | `palette-fill-warning` rule (severity: warning) + fixture; remap table in SKILL.md "Colors outside the palette" |
| BR-8 | Ask-user #3: extend Size Scale (13/16/20/36); 5pt forbidden | Delivered | SKILL.md and `rules.yaml` `sizes_pt` agree on `{7, 8, 9, 10, 10.5, 11, 12, 13, 14, 15, 16, 20, 24, 28, 32, 36, 40.5, 52}` |
| BR-9 | Ask-user #4: tree connectors 1.0pt parity with flow | Delivered | SKILL.md Decision Tree section: `Line: 1.0pt solid #595959 (parity with flow arrows)` |
| BR-10 | Slide classification via explicit speaker-notes tag, never heuristic | Delivered | `KIND_RE` in `lint.py`; untagged slides → hard error; Validation step mandates tag |
| BR-11 | Linter is output-level (.pptx), one tool for pptxgenjs + python-pptx | Delivered | `lint.py` uses `Presentation()` from python-pptx; no source AST inspection |
| BR-12 | 8 rule types each represented with `spec_ref` | Delivered | 12 rules now in `rules.yaml`, all 8 types covered, every rule has `spec_ref`; meta-tests enforce both |
| BR-13 | YAML rules separate from code, hand-editable, inches not EMU | Delivered | `references/rules.yaml`; `lint.py` converts via `EMU_PER_INCH` |
| BR-14 | CLI `uv run scripts/lint.py deck.pptx`, exit 0/1/2, `--json` | Delivered | Verified live: golden=0, palette-warn=2, decision-tree violator=2, clean=0 |
| BR-15 | Text report grouped by slide with rule id / expected / actual / spec ref | Delivered | `format_text()` produces brainstormed structure; verified live |
| BR-16 | Validation gate added as final SKILL.md section, 4-step protocol | Delivered (extended) | TASK-24 prepended a postprocess step; same protocol, 5 steps now |
| BR-17 | Fixtures regenerable from committed gen script | Delivered | `gen_fixtures.js` re-runs after TASK-23 path move and TASK-25 additions |
| BR-18 | Golden + violators + edge tolerance fixtures | Delivered | 1 golden + 12 violators + 3 edge = 16 fixtures (verified on disk) |
| BR-19 | `plugin.json` minor bump per task | Delivered | `0.1.1 → 0.2.0 → 0.3.0 → 0.4.0 → 0.5.0 → 0.6.0` — each bump justified |
| BR-20 | ruff + pytest green; task-reviewer APPROVED before each merge | Delivered | All five tasks have APPROVED notes; live `uv run pytest`=24 passed, `uv run ruff check .`=clean |
| FU-1 (TASK-23) | Off-palette warn rule shipped | Delivered | See BR-7 |
| FU-2 (TASK-23) | rules.yaml `sizes_pt` reconciled with SKILL.md Size Scale | Delivered | Identical superset; role carve-outs documented |
| FU-3 (TASK-23) | `package.json`/`package-lock.json` moved out of repo root | Delivered | Both under `scripts/tests/`; `.gitignore` scopes `node_modules/` |
| CN-1 (TASK-24) | Title-zone height fix for 24pt 2-line wraps | Delivered | SKILL.md title `h=0.85`, subtitle `y=0.78`; ASCII diagram + EMU table updated; 0.626" tagged legacy |
| CN-2 (TASK-24) | Ship canonical `postprocess-effectlst.py` | Delivered | `plugins/presentation/skills/pptx-arch-style/scripts/postprocess-effectlst.py` exists (3.1 KB); SKILL.md Rule #11 + Validation step 1 reference it; 4 pytest cases |
| CN-3 (TASK-24) | 22pt migration note in Typography | Delivered | SKILL.md Size Scale section contains migration note; linter still rejects 22pt via existing rule |
| CN-4 (TASK-24) | Version bump per material change | Delivered | `0.4.0 → 0.5.0` |
| DT-1 (TASK-25) | SKILL.md "Decision tree" component recipe with DIAMOND shape, orthogonal-only connector rule, T-junction fanout, branch-label-at-bend positioning | Delivered | SKILL.md: full prose recipe + diagram conventions; ~45 LOC canonical pptxgenjs snippet |
| DT-2 (TASK-25, path b) | Optional shipped helper script | Skipped with rationale | Task notes record explicit decision: "the skill ships specs not runtime libraries". Acceptable per AC#2's either/or wording |
| DT-3 (TASK-25, path c) | Optional new lint rule catching ≥1 defect class | Delivered | `decision-tree-connector-orthogonal` rule (severity: warning) catches diagonal-connector defect class #1. `shape_preset_geom` helper + `shape_type` matcher added to `lint.py` |
| DT-4 (TASK-25) | Violator + clean fixtures, lint exits 2 on violator, 0 on clean | Delivered | Verified live: `violators/decision-tree-connector-orthogonal.pptx` exit 2; `edge/decision-tree-orthogonal-clean.pptx` exit 0; golden still exit 0 |
| DT-5 (TASK-25) | Version bump per SemVer (minor because new lint rule shipped) | Delivered | `0.5.0 → 0.6.0`; current `plugin.json` shows `0.6.0` |
| DT-6 (TASK-25) | Defect classes 2–4 (fanout-rays, decision-text-without-shape, floating labels) documented as visual-review responsibility | Delivered | SKILL.md enumerates all four defect classes and the recommended detection responsibility |

## Non-Goal Violations

Pass 2 skipped — no PRD with explicit Non-Goals section.

## Scope Cut Violations (Pass 3)

Brainstorm's explicit scope cuts re-verified against the cumulative diff:

1. **No static code linter** — respected (`lint.py` reads .pptx only; `postprocess-effectlst.py` reads/writes the .pptx package; no JS/Python source AST inspection)
2. **No semantic checks** — respected (no NLP, no topic checks)
3. **No aesthetic checks** (overlap/balance/density) — respected (all rules remain mechanical; even the new `decision-tree-connector-orthogonal` is mechanical — it tests a single LINE shape's bounding box for both-axes-non-trivial, not graph topology)
4. **No content QA** — respected
5. **No auto-fix mode in v1** — respected with the same TASK-24 nuance: `postprocess-effectlst.py` mutates a deck but is positioned as a pre-lint generator-gap shim (step 1 of the Validation pipeline), not a linter mode. The brainstorm's "no auto-fix" cut concerned the linter; the shim does not violate it.
6. **No `pptx-core-style` coverage in this iteration** — respected (no edits under `plugins/presentation/skills/pptx-core-style/`)

**None detected.**

## Drift List (Pass 5)

The TASK-25 diff was scanned for new drift. Every hunk traces to AC #1–#5:

- `plugins/presentation/skills/pptx-arch-style/SKILL.md` — Decision Tree section + snippet + defect-class enumeration → DT-1, DT-6
- `plugins/presentation/skills/pptx-arch-style/references/rules.yaml` — `decision-tree-connector-orthogonal` rule + `shape_type` key documentation → DT-3
- `plugins/presentation/skills/pptx-arch-style/scripts/lint.py` — `shape_preset_geom` helper + `shape_type` matcher → DT-3
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/gen_fixtures.js` — violator + clean fixture generators → DT-4
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/test_lint.py` — 2 new tests → DT-4
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/fixtures/violators/decision-tree-*.pptx` + `fixtures/edge/decision-tree-orthogonal-clean.pptx` → DT-4
- `plugins/presentation/.claude-plugin/plugin.json` `0.5.0 → 0.6.0` → DT-5

**No drift detected.** The TASK-25 diff is well-bounded and entirely traceable to the decision-tree handoff scope.

## Reviewer Notes

**Brainstorm intent fully realized, plus a third consumer-driven hardening iteration.** TASK-21/22/23 delivered the brainstorm two-phase architecture exactly as scoped; TASK-24 absorbed three canary findings from the stacks consumer; TASK-25 closed a new component-level gap surfaced by the same consumer's slide-4 rebuild. None of the canary-driven additions violate brainstorm scope cuts, and each tightens the consumer feedback loop the brainstorm implicitly relied on.

**Architectural coherence of the TASK-25 additions:**

- The DT-3 lint rule is implemented as a `forbidden_element` (not a new rule type), reusing the existing matcher with the new `shape_type` key. This keeps the rule taxonomy at 8 types — BR-12 still holds. The new matcher key is documented in `rules.yaml` next to the rule for hand-editors.
- The `shape_preset_geom` helper handles three different python-pptx shape categories (`auto_shape_type` for auto-shapes, `shape_type` for connectors, and an XML fallback via `a:prstGeom/@prst`). Robust against shape-class divergence in real decks.
- Path (b) helper-script was deliberately skipped with rationale ("skill ships specs, not runtime libraries"). Defensible: shipping `drawDecisionTree()` would expand the skill's responsibility scope to library maintenance and force a Node runtime on every consumer. The 45-LOC SKILL.md snippet is the right altitude.
- Defect classes #2–#4 were honestly out-of-scope-flagged as "visual-review responsibility" because they require cross-shape topology analysis (point clustering / sibling proximity) the current flat-shape matcher cannot do. The SKILL.md prose makes the boundary explicit so consumers don't expect the linter to catch them.

**Snippet-geometry self-correction is a good signal.** The TASK-25 implementation notes record that the task-reviewer flagged a degenerate vline + an L-bend starting inside the root diamond, and the fix was committed before merge. The canonical 45-LOC snippet that ships to consumers is geometrically sound after that fix.

**Versioning trajectory remains SemVer-consistent.** Five minor bumps across five merged tasks (`0.1.1 → 0.6.0`). Each step justified per CLAUDE.md: broadened spec coverage (TASK-21), new skill content (TASK-22), Size Scale extension (TASK-23), new shipped script (TASK-24), new lint rule (TASK-25). No major bump needed — no renames or removals; the new `shape_type` matcher key is additive.

**Live verification (this review session):**

- `uv run pytest plugins/presentation/skills/pptx-arch-style/scripts/tests/` → 24 passed
- `uv run ruff check .` → All checks passed
- Linter on `violators/decision-tree-connector-orthogonal.pptx` → exit 2 with the warning reported on Slide 3
- Linter on `edge/decision-tree-orthogonal-clean.pptx` → exit 0
- Linter on `golden.pptx` → exit 0 (no regression from prior tasks)
- `plugin.json` version = `0.6.0` on disk

**Spec/rule consistency cross-check.** After TASK-25:
- `sizes_pt` in `rules.yaml` still matches SKILL.md Size Scale (no regression)
- Every rule in `rules.yaml` still has `spec_ref`; the new rule points at "SKILL.md → Diagram Conventions → Decision Tree Diagrams (orthogonal connectors only — no diagonals)" which resolves to the new Decision Tree section
- The 5-step Validation gate in SKILL.md continues to reference `postprocess-effectlst.py` by relative path
- Rule #11 in SKILL.md acknowledges the pptxgenjs gap and links forward to the Validation section

**Pass B saturation caveat closes out.** TASK-21 sampled 2 of 7 curated decks; the brainstorm's stop-on-saturation rule was relaxed to "sufficient for ask-user decisions." Two consecutive canary cycles (TASK-24 absorbing 3 findings, TASK-25 absorbing 1 component) have effectively functioned as the missing 5 decks — each cycle narrowed in scope, suggesting the audit's information yield really has saturated.

**Handoff hygiene observation.** TASK-25 (like TASK-24) is properly self-contained: Source line points at the upstream stacks repo + commit, the "Before starting" validation checklist is present, the four reference defect classes are enumerated inline with examples. The handoff acceptance pattern from CLAUDE.md is being applied consistently.

**Bottom line.** The feature is **Aligned**. Brainstorm intent is fully delivered (every BR-* row Delivered); both consumer canary cycles (TASK-24 + TASK-25) closed without scope creep or non-goal violations; the new decision-tree component is correctly positioned as a spec + mechanical lint rule + documented visual-review boundary, exactly matching the brainstorm philosophy that mechanical checks complement (not replace) the Anthropic visual-QA loop. No outstanding follow-ups are required from this review.
