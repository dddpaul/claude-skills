# Feature Review: pptx-arch-style-validation

Generated 2026-06-20 by ralph-reviewer agent (fifth cumulative review, now covering TASK-21 + TASK-22 + TASK-23 + TASK-24 + TASK-25 + TASK-26).

In-scope tasks: TASK-21..26 (all Done).
Diff range: `a1c713e..HEAD` — diff bundle truncated at 100k chars (full ~272k).
Design documents: brainstorm only (no PRD).

Prior reviews:
- `design/pptx-arch-style-validation-review-2026-06-20.md` (TASK-21+22, flagged 3 drifts + 1 partial)
- `design/pptx-arch-style-validation-review-2026-06-20-01.md` (TASK-21+22+23, Aligned)
- `design/pptx-arch-style-validation-review-2026-06-20-02.md` (TASK-21+22+23+24, Aligned)
- `design/pptx-arch-style-validation-review-2026-06-20-03.md` (TASK-21+22+23+24+25, Aligned)

---

## Verdict: Aligned

**Passes run:** 1 (brainstorm-derived intent matrix), 3 (brainstorm scope cuts), 5 (out-of-scope creep)
**Passes skipped:** 2 (no PRD — no Non-Goals section), 4 (no PRD — no Success Metrics section)

TASK-26 was the third canary-driven handoff from `standard/stacks`. It shifted the canonical block+text snippet convention from overlay (`addShape`+`addText`) to combined form (`addText({shape, ...})`). TASK-26 is a refactor of existing spec content, not new component scope — evaluated as a CONVENTION extension rather than scope creep.

## Intent → Implementation Matrix

Requirement IDs: brainstorm locked decisions (`BR-*`), TASK-23 follow-ups (`FU-*`), TASK-24 canary findings (`CN-*`), TASK-25 decision-tree handoff (`DT-*`), TASK-26 shape+text convention (`ST-*`).

| ID | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| BR-1 | Two-phase sequencing: spec audit before linter | Delivered | TASK-21 merged before TASK-22 began; dependency declared on TASK-22 |
| BR-2 | Phase 1 produces `design/pptx-arch-style-audit.md` with three-bucket routing | Delivered | 42 findings (35 auto-fill / 3 from-deck / 4 ask-user) |
| BR-3 | Pass A: structural read-through, all `~`/"approximately"/numeric ranges flagged | Delivered | SKILL.md has no remaining tildes/ranges in visual attributes |
| BR-4 | Pass B: cross-reference real Alfa decks newest-first, stop on saturation | Delivered (caveat) | 2 of 7 decks sampled; "saturation NOT reached" — AC#5 required ≥1. Retroactively validated by 3 canary cycles (TASK-24/25/26) surfacing only narrow gaps |
| BR-5 | ask-user batch in single message, decisions verbatim | Delivered | "Ask-user batch — RESOLVED" section in audit doc |
| BR-6 | Ask-user #1: Rule #11 weakened to bgPr-only | Delivered | SKILL.md Rule #11 rewritten; rules.yaml `background-effectLst-override` checks `<p:bgPr>` only |
| BR-7 | Ask-user #2: off-palette colors WARN + remap | Delivered (closed by TASK-23) | `palette-fill-warning` rule + fixture; remap table in SKILL.md |
| BR-8 | Ask-user #3: extend Size Scale 13/16/20/36; 5pt forbidden | Delivered | rules.yaml `sizes_pt` and SKILL.md Size Scale agree on `{7,8,9,10,10.5,11,12,13,14,15,16,20,24,28,32,36,40.5,52}` |
| BR-9 | Ask-user #4: tree connectors 1.0pt parity with flow | Delivered | SKILL.md Decision Tree section |
| BR-10 | Slide classification via explicit speaker-notes tag | Delivered | `KIND_RE` in lint.py; untagged → hard error |
| BR-11 | Linter is output-level (.pptx), pptxgenjs+python-pptx | Delivered | lint.py uses python-pptx only; no AST inspection |
| BR-12 | 8 rule types represented with spec_ref | Delivered | 12 rules in rules.yaml; meta-tests enforce coverage + spec_ref |
| BR-13 | YAML rules separate from code, inches not EMU | Delivered | `references/rules.yaml`; lint converts via `EMU_PER_INCH` |
| BR-14 | CLI `uv run scripts/lint.py deck.pptx`, exit 0/1/2, `--json` | Delivered | Live verified |
| BR-15 | Text report grouped by slide | Delivered | `format_text()` matches brainstorm format |
| BR-16 | Validation gate as final SKILL.md section, 4-step protocol | Delivered (extended to 5 steps by TASK-24) |
| BR-17 | Fixtures regenerable from committed gen script | Delivered | `gen_fixtures.js` updated by TASK-23/25 |
| BR-18 | Golden + violators + edge fixtures | Delivered | 1 golden + 12 violators + 3 edge (16 total) |
| BR-19 | `plugin.json` minor bump per task | Delivered with one nuance | `0.1.1 → 0.2.0 → 0.3.0 → 0.4.0 → 0.5.0 → 0.6.0 → 0.6.1`; TASK-26 used patch (see Reviewer Notes) |
| BR-20 | ruff + pytest green; task-reviewer APPROVED | Delivered | Live: 24/24 pytest pass, ruff clean |
| FU-1..3 (TASK-23) | Off-palette warn, sizes_pt reconcile, Node placement | Delivered | See prior reviews |
| CN-1..4 (TASK-24) | Title-zone, postprocess-effectlst.py, 22pt note, version bump | Delivered | See prior reviews |
| DT-1..6 (TASK-25) | Decision-tree recipe + orthogonal lint rule | Delivered with path (b) skipped per task spec |
| ST-1 (TASK-26) | SKILL.md canonical convention: combined form `addText({shape, ...})` default for single-text blocks | Delivered | New "Shape+Text Composition" section at SKILL.md L180-211 establishes combined form as default; overlay form documented as exception requiring ≥2 labels + justifying code comment |
| ST-2 (TASK-26) | All block+text snippets rewritten to combined form; overlay only with comment | Delivered | Decision-tree canonical snippet's `diamond()` and `terminal()` helpers use combined form (L478, L484); other component recipes describe shapes in style-guide notation rather than executable overlays, so are governed by the new convention block |
| ST-3 (TASK-26, optional) | Lint rule (severity: info) detecting block-shape + addText overlay | Skipped with rationale | Task notes: requires new evaluator type in lint.py (none of 8 existing types matches coincident shape+text pairs); severity:info is non-blocking; deferred to separable follow-up. AC#3 explicitly permits skip-with-rationale |
| ST-4 (TASK-26, optional) | Overlay/combined fixture pair if ST-3 shipped | Skipped (conditional on ST-3) | Correctly skipped because ST-3 was skipped |
| ST-5 (TASK-26) | plugin.json version bump per SemVer | Delivered (patch — see Reviewer Notes for SemVer commentary) | `0.6.0 → 0.6.1`; AC#5 specified patch when only SKILL.md convention rewrite shipped |

## Non-Goal Violations

Pass 2 skipped — no PRD with explicit Non-Goals section.

## Scope Cut Violations (Pass 3)

Brainstorm's six explicit scope cuts re-verified against the cumulative diff after TASK-26:

1. **No static code linter** — respected. lint.py reads .pptx only; postprocess-effectlst.py reads/writes the .pptx package only; the new combined-form convention is enforced via SKILL.md guidance, NOT via any new code-AST inspection.
2. **No semantic checks** — respected.
3. **No aesthetic checks** — respected. The skipped TASK-26 optional lint rule (overlay-detection) would have been mechanical, not aesthetic; its skip avoids feature scope expansion regardless.
4. **No content QA** — respected.
5. **No auto-fix mode in v1** — respected. `postprocess-effectlst.py` was already noted in `-02.md` as a generator-gap shim, not a linter mode. TASK-26 added nothing to this surface.
6. **No `pptx-core-style` coverage** — respected. No edits under `plugins/presentation/skills/pptx-core-style/`.

**None detected.**

### Scope Cut Violations (TASK-26 specific)

TASK-26's own out-of-scope items re-verified:

- No component-visual changes (colors/fonts/sizes/layout) — respected; convention is purely about HOW shape+text is generated.
- No refactoring of stacks-side generators — respected; only this repo's SKILL.md was touched.
- No touching of TASK-25's Decision tree section beyond the snippet rewrite — respected; the L478/L484 edits are the only Decision-tree changes, and they convert the `diamond()`/`terminal()` helpers from overlay to combined form, fully within the announced scope.
- No auto-fix for the optional lint rule — respected (rule was skipped entirely).

**None detected.**

## Success Metric Assessment

Pass 4 skipped — no PRD with Success Metrics section.

## Drift List (Pass 5)

The TASK-26 diff was scanned for hunks not traceable to ST-1..ST-5:

- SKILL.md L180-211 ("Shape+Text Composition" section) — traces to ST-1, in-scope
- SKILL.md L468 (canonical snippet header comment referencing `[[#Shape+Text Composition]]`) — traces to ST-1/ST-2, in-scope
- SKILL.md L478, L484 (`diamond()`/`terminal()` helpers using combined form) — traces to ST-2, in-scope
- `plugin.json` 0.6.0 → 0.6.1 — traces to ST-5
- task-26 backlog file — task tracking, expected

**No drift detected.** The TASK-26 diff is narrow and entirely traceable to its 4 (mandatory + version) AC. The optional AC #3/#4 were correctly recorded as skipped with rationale in task notes rather than partial-implemented.

## Reviewer Notes

**TASK-26 lands cleanly as a CONVENTION shift, not a new feature.** The "Shape+Text Composition" section is positioned correctly in SKILL.md — before "Component Styles" — so it governs every downstream component recipe authoritatively. The overlay-as-exception rule is precise (2+ labels per block, justifying comment required), which prevents the canonical-vs-exception distinction from drifting again. The decision-tree snippet rewrite at L478/L484 is internally consistent: each `addText({shape, ...})` call carries the full geometry inline, matching the new convention.

**SemVer choice for TASK-26 (patch, not minor) is defensible but discussable.** AC#5 explicitly maps "only SKILL.md convention rewrite" → patch (0.6.0 → 0.6.1) and the task followed that. However, this is genuinely a *broadened spec coverage* event — a new canonical convention governing every block+text snippet downstream — which CLAUDE.md's SemVer note describes as "minor for broadened triggers" / "minor for new content." The task's AC pinned `patch`, and the implementer obeyed; this is acceptable, but worth flagging that the version trajectory now contains its first patch bump where prior tasks (TASK-21 through TASK-25) all bumped minor for analogous spec broadenings. Not a blocker — just a noted inconsistency in versioning judgment between TASK-25 (decision-tree recipe = minor) and TASK-26 (shape+text convention = patch) when both broadened the canonical recipe surface.

**The optional lint rule skip (ST-3) is well-reasoned.** Detecting coincident shape+text pairs requires a new evaluator type that walks pairs of sibling shapes by coordinate proximity — fundamentally different from the per-shape matchers the current 8 rule types use. Filing it as a separable follow-up is correct architectural hygiene rather than artificial deferral. The skip explicitly notes severity:info is non-blocking, so consumer migration is not gated on it.

**Pass B saturation caveat (BR-4) remains unchanged.** TASK-21 sampled 2 of 7 curated decks. The brainstorm's preferred stop condition was "no new combinations in 2 consecutive decks"; actual stop was "sufficient for ask-user decisions." Three subsequent canary cycles (TASK-24 title-zone/postprocess/22pt; TASK-25 decision-tree topology; TASK-26 shape+text convention) surfaced narrow, specific gaps — exactly the validation signal an exhaustive Pass B would have wanted, just amortized across multiple tasks. The caveat is acceptable in steady state but worth retiring formally if a future task does the remaining 5 decks (and the convention-coverage gap that TASK-26 closed is itself evidence that a fresh deck-sweep might surface more such items).

**Brainstorm intent + 3 canary extensions, all fully realized.** The two-phase architecture (audit → linter + gate) is intact; the off-palette warn/remap is enforced; the title-zone/postprocess/migration trio is shipped; the decision-tree component recipe + orthogonal-connector rule is shipped; the shape+text convention shift is shipped. Every `spec_ref` in `rules.yaml` resolves to a real SKILL.md section. Live verification: `uv run pytest plugins/presentation/skills/pptx-arch-style/scripts/tests/` = 24/24 pass, `uv run ruff check .` = clean, `plugin.json` version = `0.6.1`.

**Bottom line.** The feature is **Aligned**. The TASK-26 convention shift was the right altitude (spec rewrite + new section + targeted snippet refactor; optional lint rule correctly deferred). No outstanding follow-ups required from this review — the only flaggable item is the minor-vs-patch SemVer choice for TASK-26, which is a defensible reading of AC#5 but creates a small precedent gap with TASK-25's analogous bump-to-minor.
