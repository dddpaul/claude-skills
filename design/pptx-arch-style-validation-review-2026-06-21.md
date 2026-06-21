# Feature Review: pptx-arch-style-validation (5th cumulative review, TASK-21..29)

**Verdict: Aligned**

**Passes run:** 3 (Brainstorm Scope Cuts), 5 (Out-of-Scope Creep)
**Passes skipped:** 1 (no PRD), 2 (no PRD non-goals), 4 (no PRD success metrics) — only `design/pptx-arch-style-validation-brainstorm.md` exists for this feature; PRD was never written. As in prior four reviews, evaluation rests on brainstorm intent + per-task ACs.

## Intent → Implementation Matrix

The brainstorm framed two phases (Spec audit + Linter). Subsequent canary-driven follow-ups extended both phases. Mapping below uses the brainstorm-locked intents (BR-N) plus the canary follow-up intents (CF-N) surfaced after applied use.

| ID | Intent (from brainstorm or task body) | Status | Evidence |
|----|--------------------------------------|--------|----------|
| BR-1 | Phase 1 — close every "point of invention" in SKILL.md | Delivered | TASK-21 closed 42 audit findings; SKILL.md grew 465→530 lines; ranges/`~`/approx eliminated |
| BR-2 | Phase 2 — `.pptx`-level linter `uv run lint.py deck.pptx` | Delivered | `plugins/presentation/skills/pptx-arch-style/scripts/lint.py` exists; CLI works |
| BR-3 | YAML rules separate from code | Delivered | `references/rules.yaml` |
| BR-4 | 8 rule types with at least one rule each | Delivered | TASK-22 shipped 10 rules covering all 8 types |
| BR-5 | `spec_ref` field on every rule | Delivered | Confirmed by TASK-22 meta-tests |
| BR-6 | Explicit `<!--arch-style:content\|title\|section-->` slide tagging; heuristic classification rejected | Delivered | TASK-22 |
| BR-7 | Off-palette colors → warn + remap (ask-user batch decision) | Delivered | TASK-23 shipped `palette-fill-warning` (severity:warning, exit 2) |
| BR-8 | Validation gate in SKILL.md (4-step protocol) | Delivered | TASK-22 added final Validation section |
| BR-9 | Exit codes 0/1/2 + `--json` flag | Delivered | TASK-22 |
| BR-10 | Test fixtures regenerable from `gen_fixtures.js` (not opaque blobs) | Delivered | TASK-22, repaired to scoped path in TASK-23 |
| BR-11 | Tolerance defaults calibrated during fixture creation | Delivered | TASK-22 edge-tolerance fixtures (0.003in pass, 0.010in fail) |
| BR-12 | YAML in inches; EMU internal | Delivered | TASK-22 |
| BR-13 | SemVer bumps per CLAUDE.md convention | Delivered | 0.1.1→0.8.1 trajectory documented per task |
| CF-1 | Title-zone 2-line wrap support (TASK-24 finding #1) | Delivered, then **regressed**, then **re-delivered** | TASK-24 path (a) h=0.85/subtitle 0.78 introduced overlap → TASK-27 path (c) hybrid fix (red line moved to y=0.85, valign=top) |
| CF-2 | Canonical `<a:effectLst/>` post-processor (TASK-24 finding #2) | Delivered | `scripts/postprocess-effectlst.py` shipped + 4 pytest cases |
| CF-3 | 22pt migration note (TASK-24 finding #3) | Delivered | SKILL.md line 87: "MUST be 24pt, not the legacy 22pt"; long titles split via subtitle |
| CF-4 | Decision-tree component recipe (TASK-25) | Delivered | SKILL.md Decision Tree section + 45-LOC snippet |
| CF-5 | Decision-tree orthogonality lint rule (TASK-25 path c) | Delivered | `decision-tree-connector-orthogonal` (severity:warning) |
| CF-6 | Combined shape+text convention (TASK-26) | Delivered, then **broadened** in TASK-29 | TASK-26 narrow criterion → TASK-29 broadened to include mixed-format |
| CF-7 | Decision-tree connector direction semantics fix (TASK-28) | Delivered | SKILL.md (from,to) convention + canonical snippet rewritten |
| CF-8 | Decision-tree helper file `decision-tree.js` (TASK-28 locked YES) | Delivered | `scripts/decision-tree.js` exports `drawDecisionTree(slide, spec)` with explicit (from,to) + flip logic |
| CF-9 | Missing-arrowhead lint rule for decision-tree (TASK-28 locked YES) | Delivered | `decision-tree-connector-arrowhead-missing` (severity:warning) at y≥3.6 terminal band |
| CF-10 | Overlay broadening for mixed-format (TASK-29) | Delivered, spec-only | SKILL.md §Shape+Text Composition lines 197-226 added criterion (ii); lint rule deliberately **skipped** per lock |

## Scope Cut Violations (Pass 3)

Brainstorm explicitly cut six items. Checking each against the cumulative diff:

| Cut item | Still respected? | Evidence |
|---|---|---|
| No static code linter (pptxgenjs/python-pptx AST) | Respected | Only `.pptx` output-level checks shipped |
| No semantic checks ("is this text about the right topic?") | Respected | No content-meaning rules added |
| No aesthetic checks (overlap/balance/density) | Respected | Topology-related rules added in TASK-25/28 are orthogonality + arrowhead presence — these are spec-conformance rules, not aesthetic judgments. Borderline but defensible: orthogonal-vs-diagonal is a binary spec rule, not "is this layout pretty" |
| No content QA (typos, missing sections) | Respected | None added |
| No auto-fix mode in v1 | Respected | All 14 rules are report-only |
| No `pptx-core-style` coverage in this iteration | Respected | Only `pptx-arch-style` touched |

**Scope Cut Violations: None detected.**

## Drift List (Pass 5)

Scanning the cumulative diff for hunks unrelated to any backlog AC or brainstorm intent:

| Hunk | Verdict |
|---|---|
| `.gitignore` adds `plugins/.../scripts/tests/node_modules/` | In scope — TASK-23 AC #4 explicitly mandates the scoped path |
| `pyproject.toml` adds `python-pptx>=1.0.2`, `pyyaml>=6.0.3` to dev deps; `uv.lock` regenerated | In scope — direct deps of `lint.py`, surfaced via TASK-22 review |
| All SKILL.md / rules.yaml / lint.py / fixtures / tests changes | In scope — traceable to TASK-21 through TASK-29 ACs |

**No drift detected.**

## Special Attention Checks

**(1) TASK-27 path (c) locked geometry vs. shipped**
- Locked: title h=0.85 valign=top, red line y=0.85, subtitle y=0.87, content y=1.10..5.10
- Shipped: title h=0.85 valign=top (✓), red line y=0.85 (✓), subtitle **y=0.90** h=0.18 (deviation), content y=1.10..5.10 (✓)
- The subtitle moved from locked 0.87 to shipped 0.90. Justification visible in SKILL.md line 155: "Sits immediately below the red line (which ends at y=0.892); ends at y=1.08 leaving a 0.02in gap above content." Subtitle at y=0.87 would have overlapped the red line band [0.85, 0.892]. The implementer caught the arithmetic flaw in the lock and corrected it. This is a defensible mid-flight correction, not drift — the *intent* (subtitle below red line, above content area) is preserved. Should be noted, not flagged as a violation.

**(2) TASK-28 helper + lint rule both shipped**
- `plugins/presentation/skills/pptx-arch-style/scripts/decision-tree.js`: confirmed present, exports `drawDecisionTree(slide, spec)` with explicit `(from, to)` semantics and `flipH/flipV` direction handling.
- `decision-tree-connector-arrowhead-missing` rule: confirmed in `rules.yaml` lines 245+, severity:warning, scoped to vertical gray LINEs at y≥3.6 (terminal band) to avoid bus-segment false positives.
- Both delivered per lock. ✓

**(3) TASK-29 spec-only (no lint rule shipped)**
- Confirmed: no overlay/mixed-format rule in `rules.yaml`. AC#4/#5 of TASK-29 (lint rule + fixtures) marked skipped in task notes with rationale (heuristic too fuzzy, severity:info non-blocking). ✓

**(4) SemVer trajectory 0.6.1 → 0.7.0 → 0.8.0 → 0.8.1**
- 0.6.1 → 0.7.0 (TASK-27): justified — title-zone shift is a breaking change for consumer generators already on y=0.78 subtitle (per TASK-58 in stacks). Minor bump correct.
- 0.7.0 → 0.8.0 (TASK-28): justified — new public surface (`decision-tree.js` helper) + new lint rule. Minor bump correct.
- 0.8.0 → 0.8.1 (TASK-29): justified — pure spec clarification, no new public surface, no new rule. Patch bump correct.
- Full trajectory 0.1.1 → 0.8.1 (8 bumps across 9 tasks; TASK-29 is the only patch) is internally consistent with CLAUDE.md SemVer convention.

**(5) Cross-task drift from brainstorm intent**
The brainstorm originally envisioned **two tasks** (TASK-A + TASK-B). What shipped is 9 tasks: 2 brainstorm tasks (TASK-21/22), 1 immediate review follow-up (TASK-23), 2 canary follow-ups (TASK-24/25/26 — three sibling spec-clarifications surfaced by stacks TASK-57), and 3 second-canary follow-ups (TASK-27/28/29 — bugs surfaced by stacks TASK-58 applying v0.6.1). This is **iteration through canary feedback**, not scope creep — each follow-up traces to an applied-canary defect with reference source in `stacks/presentations/registry/`. The brainstorm's "Open questions" section explicitly anticipated this ("Calibrate during fixture creation"; "which actual `.pptx` files to treat as authoritative") and the validation-gate scope was always meant to be exercised by real consumers. Iteration depth reflects feature health (canary exposes drift, drift is closed), not scope drift.

One genuine *internal* drift worth recording: TASK-24 path (a) (h=0.85, subtitle y=0.78) shipped an internally inconsistent SKILL.md (subtitle range [0.78, 1.00] overlapped content area [0.787, 5.10]). TASK-27 path (c) repaired this. The TASK-24 → TASK-27 round-trip is **not** drift from the brainstorm — it's the canary loop working as designed — but it is a flag that path-choice ACs ("implementer chooses") need arithmetic-consistency review even after task-reviewer approval. TASK-27's locked plan suffered the same flaw (subtitle y=0.87 inside red-line band [0.85, 0.892]) and was again caught by the implementer mid-flight. Two consecutive title-zone fixes had latent arithmetic errors in the locked plan; both were caught downstream. Suggest a **future improvement** for title-zone-like geometry changes: require an arithmetic-consistency table (zones must not overlap) in the locked plan before Ralph fires.

## Reviewer Notes

- **Feature is shippable and being shipped.** Plugin version 0.8.1, all 28 tests pass, ruff clean, all 9 tasks Done with task-reviewer APPROVED. The cumulative state is internally consistent.
- **Canary loop is functioning as intended.** TASK-23/24/25/26 came from stacks TASK-57's canary; TASK-27/28/29 came from stacks TASK-58's second canary. Each surfaced concrete defects (title-zone overlap, decision-tree topology, connector direction, mixed-format collapse) that the linter alone could not catch (acknowledged by brainstorm: "complements not replaces visual-QA"). The handoff machinery is doing its job.
- **Spec maturity is now high.** TASK-29's deliberate decision to ship spec-only (no fuzzy lint rule) is the correct call — over-restrictive lint rules erode trust. The pattern of "ship recipe → consumer applies → defect surfaces → broaden criterion" is healthy as long as broadenings continue to come from real canary data.
- **One latent risk worth noting** (carry-forward from prior reviews): the `decision-tree-connector-arrowhead-missing` rule is scoped narrowly (`y_min=3.6`, vertical only, gray-only) to avoid false positives on bus segments. This is documented as a known limitation in TASK-28 notes. If decision-trees ever appear with terminals outside that y-band, the rule silently misses. Acceptable for now (matches the one canonical layout), but worth a follow-up if a second decision-tree shape ever ships.
- **Subtitle y deviation in TASK-27** (locked 0.87, shipped 0.90) should be noted in the task summary for the next review pass — not a violation, but the kind of mid-flight correction that's worth being explicit about so future review passes don't re-flag it as drift.
- **No PRD remains a methodological gap.** This is the fifth review without a PRD; the brainstorm has been adequate so far because the feature is bounded (one skill, one linter, fixed rule taxonomy). If a sixth iteration emerges, consider whether a retrospective PRD would help, especially for the canary-driven follow-up tasks (TASK-24..29) that have outgrown the original two-phase scope.

Relevant absolute paths reviewed:
- `/Users/paul/Private/Projects/ai/claude-skills/plugins/presentation/skills/pptx-arch-style/SKILL.md`
- `/Users/paul/Private/Projects/ai/claude-skills/plugins/presentation/skills/pptx-arch-style/scripts/decision-tree.js`
- `/Users/paul/Private/Projects/ai/claude-skills/plugins/presentation/skills/pptx-arch-style/scripts/lint.py`
- `/Users/paul/Private/Projects/ai/claude-skills/plugins/presentation/skills/pptx-arch-style/scripts/postprocess-effectlst.py`
- `/Users/paul/Private/Projects/ai/claude-skills/plugins/presentation/skills/pptx-arch-style/references/rules.yaml`
- `/Users/paul/Private/Projects/ai/claude-skills/plugins/presentation/.claude-plugin/plugin.json`
- `/Users/paul/Private/Projects/ai/claude-skills/design/pptx-arch-style-validation-brainstorm.md`
