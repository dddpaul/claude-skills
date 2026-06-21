# Feature Review: pptx-arch-style-validation (Seventh cumulative — after TASK-31)

**Verdict: Aligned**

**Passes run:** 3 (Brainstorm Scope Cuts), 5 (Out-of-Scope Creep)
**Passes skipped:** 1 (no PRD); 2 (no PRD non-goals; brainstorm Scope Cuts handled by Pass 3); 4 (no PRD success metrics — linter green/red remains the implicit binary metric, covered by per-task ACs)

## Carry-forward statement

Prior six reviews established the full **BR-1..BR-13 + CF-1..CF-11** matrix as Delivered. TASK-31 is an **architectural reversal**: it does not add new requirement coverage, it *rewinds* CF-1 (title-zone geometry) to the v0.2.0 design and tightens CF-3 (22pt migration note) into a hard rule. This review (a) verifies the seven TASK-31 incremental requirements (CF-12.1..7), (b) corrects two prior matrix rows (CF-1 and CF-3) that were wrong in direction, and (c) re-checks the existing 21 unchanged matrix rows for collateral damage. No drift detected.

## Intent → Implementation Matrix (TASK-31 incremental + matrix corrections)

| ID | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| CF-12.1 | Revert Content Slide Anatomy to v0.2.0 geometry (red line y=0.500, title h=0.626 valign='middle', subtitle y=0.550 h=0.220, content y=0.787) | Delivered | `SKILL.md:153-157` — all four numbers match; `references/rules.yaml:101` `red-accent-line-coords expect y: 0.500`; `rules.yaml:57-58,84-85` mandatory/forbid bands shifted to `y_min:0.45 / y_max:0.55`; commit `a08989a` |
| CF-12.2 | ASCII diagram on lines ~140-149 updated to match reverted numbers | Delivered | `SKILL.md:140-150` — annotations explicitly read `y=0, h=0.626, middle-aligned`, `red line at y=0.500 (brand-constant, under page badge)`, `subtitle (y=0.550, h=0.220)`, `from y≈0.787 to y≈5.10` |
| CF-12.3 | "No 2-line title wraps" promoted from soft advice to a hard MUST rule; title+subtitle split prescribed as the remedy | Delivered | `SKILL.md:155` — `**Hard rule — no 2-line title wraps.** A content slide title MUST fit on a single line at 24pt … the implementer MUST split it: short head as the title, remainder as the subtitle`; explicit char thresholds (~50 Cyrillic / ~60 Latin); cross-referenced from line 87 and Rule #3 (line 705) |
| CF-12.4 | ADR-style note explaining why v0.7.0's geometry move was an architectural error, to prevent recurrence | Delivered | `SKILL.md:160` — full ADR paragraph naming `v0.7.0`/`v0.9.0` versions, the "brand constant, not layout variable" framing, and the future-iteration guard: *"if a title does not fit, split it — do NOT move the red line"*; reinforced as historical breadcrumbs inside EMU table (`SKILL.md:694-696` mark 0.850/0.900/1.100 as "withdrawn — do not use") and Rules #3/#10 (`SKILL.md:705,712`) |
| CF-12.5 | SemVer 0.8.2 → 0.9.0 (minor; breaking for consumers on v0.7.x layout) | Delivered | `plugins/presentation/.claude-plugin/plugin.json:4` `"version": "0.9.0"`; minor bump correct — geometry constants visible to every consumer generator changed |
| CF-12.6 | Optional AC#4 (lint rule for title char-count or text-bottom-vs-red-line) — shipped OR skipped with rationale | Delivered (skipped with rationale) | Task notes record deliberate skip: "out of scope for the revert; existing `red-accent-line-coords` rule at y=0.500 ± 0.005 already catches the v0.7.0 line-position failure mode at error severity"; AC marked done per `Опц.` (optional) prefix |
| CF-12.7 | Tests + lint stay green | Delivered | Verified: `uv run pytest plugins/.../tests/` → 28 passed; `uv run ruff check .` → All checks passed |

## Matrix corrections (CF-1 and CF-3 from prior reviews)

Prior reviews (5th and earlier) listed CF-1 as "Delivered, then regressed, then re-delivered" — treating 2-line wrap support as a goal in itself. The user-feedback that drove TASK-31 reframes this: **2-line wrap support was never the right goal; CF-1's original direction was wrong**. The corrected reading:

| ID | Requirement (corrected) | Status | Evidence |
|----|-------------------------|--------|----------|
| CF-1 | ~~Title-zone 2-line wrap support~~ → **rescinded: 2-line wraps are explicitly forbidden; long titles MUST be split into title+subtitle (the subtitle exists for exactly this)** | Rescinded and **inverted** in v0.9.0 (TASK-31). The TASK-24 → TASK-27 round-trip is now correctly classified as a Class-B spec error (chasing the wrong variable), repaired by TASK-31 | `SKILL.md:155` hard rule; ADR at `SKILL.md:160` |
| CF-3 | 22pt migration note (TASK-24 finding #3) — now **promoted to cross-reference the hard rule**, not just legacy advice | Delivered, **strengthened** | `SKILL.md:87` now explicitly states *"Title length is the load-bearing variable: a 24pt title MUST fit on a single line … (no 2-line wraps — see Content Slide Anatomy for the hard rule)"*; cross-link present |

All other CF-N and BR-N rows (BR-1..13, CF-2, CF-4..11) remain Delivered and untouched. TASK-31's surgery is confined to title-zone geometry and Y0; decision-tree (CF-4/5/7/8/9), overlay form (CF-6/10), postprocess-effectlst (CF-2), and the v0.8.2 contradiction sweep (CF-11) are all intact (verified by inspection — `decision-tree.js` exports unchanged, Shape+Text Composition section at `SKILL.md:183-226` unchanged, Connectors at `SKILL.md:451-595` unchanged, Rule #4 still names only "section" slides per CF-11.1).

## Scope Cut Violations

None detected. Brainstorm cuts (no static linter, no semantic checks, no aesthetic checks, no content QA, no auto-fix v1, no pptx-core-style coverage) are all still respected. TASK-31 adds zero rules and zero new public surface — it is a pure geometry reversion + spec-text tightening.

## Drift List

No drift detected. The `git show a08989a --stat` change list is fully traceable:
- `SKILL.md` (42 lines changed) — Anatomy section, ADR, Y0 constant, EMU reference rows, Rules #3/#10 — all in scope per AC#1/#2/#3/#5
- `rules.yaml` (12 lines changed) — red-accent-line-coords expected y and the two ±0.05 bands — required to keep the linter consistent with the reverted spec
- `gen_fixtures.js` + `test_lint.py` + 19 binary fixtures — fixture regeneration mandated by the change in `addRedLine` / `addContentTitle` defaults; renamed pytest from `_v070_geometry` to `_v090_anatomy`; expected per a coordinate revert
- `plugin.json` — version bump per AC#6
- `d323fc6` follow-up — 1-line fix to a stale `Y0=1.10` reference in Category Cards (`SKILL.md:317`), flagged by task-reviewer; no drift

The fixture binaries each shifted by 1 byte (`Bin NNNN -> NNNN+1`) which is consistent with a deterministic regeneration through the same toolchain after a tiny defaults change — not unrelated edits.

## New internal contradictions check (TASK-31 incremental)

Cross-checked every TASK-31 number against every other place it could conflict — none found:

| New text | Cross-reference | Verdict |
|---|---|---|
| ASCII line 142 "red line at y=0.500" | Rule #3 (line 705), EMU table line 686, rules.yaml:101 | Consistent |
| Anatomy line 154 "title h=0.626 valign:'middle'" | EMU table line 690, ADR line 160 | Consistent |
| Anatomy line 156 "subtitle y=0.550 h=0.220 … ends at y=0.770" | 0.550+0.220=0.770 ✓; content top y=0.787 leaves 0.017in gap (claimed ~0.02) ✓ | Arithmetically correct |
| Anatomy line 157 "content area … y=0.787, ends at y≈5.10 (4.31in usable)" | 5.10-0.787=4.313 ≈ 4.31 ✓; Y0=0.787 in Category Cards (line 317) after d323fc6 fix; Rule #10 line 712; formulas Y0=0.787 line 607 | Consistent |
| Hard rule "~50 Cyrillic / ~60 Latin chars at 24pt in 9.234in" | No prior conflicting number in spec | New, non-contradictory |
| Rule #4 still names only "section" slides (TASK-30 CF-11.1) | SKILL.md:706 unchanged | TASK-30 fix preserved |
| EMU 0.500"=457200 EMU | 0.500×914400=457200 ✓ | Arithmetically correct |
| EMU 0.626"≈572414 EMU | 0.626×914400=572414.4 ✓ | Arithmetically correct |
| EMU 0.787"≈719633 EMU | 0.787×914400=719632.8 ✓ | Arithmetically correct |
| EMU 0.850/0.900/1.100" rows kept and labelled "withdrawn — do not use" | Historical breadcrumb, no live spec uses them | Consistent (informational only) |
| TASK-28 connector section + TASK-29 overlay section + TASK-30 Rule #4/Rule #12 | grep confirms unchanged | Out-of-scope preserved per task spec |

One minor observational note (not a contradiction, not a blocker): the ADR at `SKILL.md:160` says title h was widened "between v0.4.x and v0.7.0" — strictly it widened to 0.85 in TASK-24 (v0.4.1→v0.5.0) and the red line was moved in TASK-27 (v0.6.1→v0.7.0). The summary phrasing collapses two steps into one but is directionally correct and serves the ADR's purpose.

## SemVer trajectory check

`0.1.1 → 0.2.0 → 0.3.0 → 0.4.0 → 0.5.0 → 0.6.0 → 0.6.1 → 0.7.0 → 0.8.0 → 0.8.1 → 0.8.2 → 0.9.0` (12 bumps across 11 tasks). 0.9.0 is correctly minor: every consumer generator on v0.7.x that adopted `addRedLine(y=0.85)` and `Y0=1.10` MUST update to v0.2.0 geometry.

## Reviewer Notes

- **The right kind of correction.** TASK-31 is the canary loop doing what it was designed to do: a third applied canary (stacks TASK-59) under v0.8.1 surfaced that v0.7.0's "fix" had moved the wrong variable. The user feedback ("Это очень простой вопрос, но ты 3-й раз не можешь сделать нормально") is harsh but accurate — three rounds chasing the wrong invariant is a meta-failure that an ADR is the right antidote to. The ADR at `SKILL.md:160` reads like a postmortem and is exactly the kind of guardrail that prevents the same mistake from re-occurring in iteration 4.
- **Matrix correction is the real news.** Prior reviews (CF-1 row in the 5th cumulative) accepted the framing that 2-line wrap support was a goal. That framing was wrong from the start — it inherited the wrong direction from TASK-24's finding #1 wording ("Title-zone height не вмещает 2-line wraps"). The corrected matrix entry should now read **"long titles MUST be split"** as a positive intent, not "wrap support" as a feature. This is worth flagging to the user so future review templates don't reintroduce the inverted framing.
- **CF-3 was already half-right; v0.9.0 makes it fully right.** Line 87 in SKILL.md already said "long titles must be split title+subtitle" but only as advice inside the legacy-22pt note. TASK-31 promoted the rule to the Content Slide Anatomy section as a MUST, and inserted a cross-reference from line 87 back to it. The two locations now agree: legacy-22pt advice points at the hard rule, hard rule defines the contract.
- **AC#4 skip is correctly justified.** The existing `red-accent-line-coords` rule at `expect y: 0.500` with tolerance `coord: 0.005` already catches the v0.7.0 failure mode (a generator emitting the line at y=0.85 trips the rule at error severity, exit code 1, blocks publishing). A character-count heuristic for titles would have been valuable as a *prevention* rule (catch the long title before render), but it is genuinely separable and can ship as a follow-up if a fourth canary proves it needed.
- **TASK-28/29 untouched, as required.** Connectors / Decision Tree section (line 451+), Shape+Text Composition section (line 183+), `decision-tree.js`, and the `decision-tree-connector-arrowhead-missing` rule are all unchanged. Out-of-scope discipline held.
- **Tests + lint green confirmed.** Pytest 28 passed; ruff clean.
- **Feature health.** Plugin version 0.9.0, all 11 tasks Done, task-reviewer APPROVED on each, cumulative state internally consistent. The skill is now back to its v0.2.0 visual signature with the wrap-handling lesson preserved as an ADR. Recommend not opening TASK-32 unless a fourth canary surfaces a new defect — the spec is mature.

Commits verified: `a08989a` (TASK-31 main), `d323fc6` (TASK-31 reviewer-nit fix), `481d75c` (mark Done)
Bundle path consulted: `/tmp/ralph-review-bundle.md` (cumulative diff truncated at 100k chars; reviewer verified directly from working tree and `git show a08989a d323fc6 --stat`)
Prior reviews carry-forward base: `design/pptx-arch-style-validation-review-2026-06-21-01.md`
