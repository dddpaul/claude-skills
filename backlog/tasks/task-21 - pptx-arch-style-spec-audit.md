---
id: TASK-21
title: 'pptx-arch-style: spec audit'
status: To Do
assignee: []
created_date: '2026-06-20 10:05'
updated_date: '2026-06-20 10:57'
labels:
  - 'feature:pptx-arch-style-validation'
dependencies: []
priority: high
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**Goal:** close every "point of invention" in `plugins/presentation/skills/pptx-arch-style/SKILL.md` so the spec becomes a complete source of truth (~120 precise values across coordinates, colors, fonts, borders, paddings).

**Background.** The empirical error catalog (extracted from commit 038308b "Improve pptx-arch-style" — every diff line in that commit was a real lesson) split historical mistakes into two classes. Class A = wrong value against a known rule (linter territory, separate TASK-B). Class B = spec was incomplete, the implementer invented (spec-audit territory, **this task**). Phase 1 must precede Phase 2; otherwise a linter would scream at spec gaps, not violations.

**Method.**
- **(A) Structural read-through** of `SKILL.md` section by section. Checklist per object type: shapes need x/y/w/h, fill, border, shadow, corner radius; text needs face, size, weight, color, alignment, line spacing. Flag every `~`, `approximately`, `9-10pt`, `0.65–0.70`, missing attribute.
- **(B) Cross-reference real decks.** Process the curated set below from newest to oldest (start with #1 — the most recent and arch-suffixed). Unpack XML, enumerate unique `(shape_type, fill, border, font, size)` combinations across the set. Any combination not derivable from the spec = either spec gap or deck violation — log both separately. Stop early if signal saturates (no new combinations in 2 consecutive decks).

  Canonical deck set (7 files across 4 projects, all generated arch-style output, user-curated):

  **channels**:
  1. `/Users/paul/Private/Alfa/Projects/channels/presentations/doc-2/output/channels-definition-arch.pptx` ⭐ — most recent, arch-suffix, start here
  2. `/Users/paul/Private/Alfa/Projects/channels/presentations/doc-3/output/patterns-overview.pptx`

  **equation/core**:
  3. `/Users/paul/Private/Alfa/Projects/equation/core/presentations/doc-3/output/doc-3-presentation.pptx`
  4. `/Users/paul/Private/Alfa/Projects/equation/core/presentations/doc-4-v2/output/doc-4-v2-presentation.pptx`

  **standard/stacks**:
  5. `/Users/paul/Private/Alfa/Projects/standard/stacks/presentations/workflows/output/workflow-engines.pptx`
  6. `/Users/paul/Private/Alfa/Projects/standard/stacks/presentations/workflows/output/workflow-service-vision.pptx`

  **datapower-v2**:
  7. `/Users/paul/Private/Alfa/Projects/datapower/datapower-v2/presentations/integration-architecture-ak-v6.2.pptx` ⭐ — last revision of the ak series (Архитектурный комитет target audience)

```bash
# Unpack a .pptx for XML inspection:
unzip -q deck.pptx -d /tmp/unpacked && ls /tmp/unpacked/ppt/slides/
# Cleanup:
rm -rf /tmp/unpacked
```

**Decision routing for each gap (three buckets, marked in audit doc `decision` column):**
- **auto-fill** — natural default exists from spec patterns (unspecified font → Arial; unspecified padding → 0.100in; unspecified border → 1pt; missing effect → `<a:effectLst/>` per Rule #11). Apply without asking.
- **from-deck** — value not in spec but stable across real decks → adopt as de-facto standard.
- **ask-user** — affects visual identity, no donor pattern (new color outside palette, new size outside the 8/9/10/10.5/11/12/14/15/24/40.5/52pt scale, new distance not derivable from formulas). Present as **single batch message** to the user; do NOT interrupt mid-audit.

**Artifacts produced:**
- `design/pptx-arch-style-audit.md` — table with columns: `[SKILL.md section] | [ambiguous formulation] | [proposed concrete value] | [reasoning/source] | [decision]`. Kept after merge as design artifact.
- Updated `plugins/presentation/skills/pptx-arch-style/SKILL.md` — single commit merging all bucket-decided values (after user resolves the ask-user batch).
- `plugins/presentation/plugin.json` — minor bump per CLAUDE.md SemVer (broadened spec coverage).

**Out of scope (will be a separate TASK):** linter implementation, validation gate, speaker-notes tagging, YAML rules, test fixtures. Out of scope: pptx-core-style coverage.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 design/pptx-arch-style-audit.md exists with every spec gap classified into one of three buckets (auto-fill / from-deck / ask-user)
- [ ] #2 plugins/presentation/skills/pptx-arch-style/SKILL.md no longer contains '~', 'approximately', 'depending on', or numeric ranges (e.g. '0.65-0.70') for visual attributes
- [ ] #3 Every shape/text spec in SKILL.md has explicit values for: coords, fill, border, font face, font size, weight, color, alignment, effect override
- [ ] #4 ask-user batch was presented to user once via AskUserQuestion; decisions captured verbatim in audit doc
- [ ] #5 Cross-reference check (B) completed against at least 1 real Alfa deck; per-deck findings documented in audit doc
- [ ] #6 plugins/presentation/plugin.json version bumped (minor) per CLAUDE.md SemVer rules
- [ ] #7 uv run ruff check . and uv run pytest both pass
- [ ] #8 task-reviewer agent returns APPROVED before merging
<!-- AC:END -->
