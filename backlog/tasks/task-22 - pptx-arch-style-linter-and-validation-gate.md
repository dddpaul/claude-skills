---
id: TASK-22
title: 'pptx-arch-style: linter and validation gate'
status: To Do
assignee: []
created_date: '2026-06-20 10:06'
labels:
  - 'feature:pptx-arch-style-validation'
dependencies:
  - TASK-21
priority: high
ordinal: 22000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**Depends on:** TASK-21 (must be Done).

**Goal:** ship a `.pptx`-level validator that compares produced artifacts against the (now-complete after TASK-21) spec, plus a hard gate in SKILL.md that prevents shipping un-validated decks.

**Why output-level (not source-level).** Universal across pptxgenjs and python-pptx; no dual AST parsers to maintain; produced XML is canonical regardless of generator; plugs into Anthropic's existing visual-QA pipeline as the *first* (programmatic) step before subagent visual inspection.

**Stack:** Python 3 + `python-pptx` for reading; rules in YAML (hand-editable, separate from code); CLI `uv run scripts/lint.py deck.pptx` with exit codes 0/1/2 (green/error/warning); `--json` flag for machine output.

**Layout:**
```
plugins/presentation/skills/pptx-arch-style/
├── SKILL.md                        (+ new "Validation" gate section, last in file)
├── scripts/
│   ├── lint.py                     (entrypoint)
│   └── tests/
│       ├── fixtures/
│       │   ├── golden.pptx         (3 slides: title+section+content, 100% conformant)
│       │   ├── violators/          (one .pptx per violation type)
│       │   └── edge/               (tolerance boundaries, ambiguous matches)
│       ├── gen_fixtures.js         (pptxgenjs script that regenerates fixtures — committed; fixtures regenerable, not opaque blobs)
│       └── test_lint.py            (pytest)
└── references/
    └── rules.yaml                  (rule definitions)
```

**Rule taxonomy — 8 types** mapped directly to the empirical error categories:

| Type | Catches |
|---|---|
| `mandatory_element` | Content slide → page badge + red line present |
| `forbidden_element` | Title/section slide → no page badge, no red line |
| `shape_coordinates` | Red line at x=0, y=0.500, w=10.000, h=0.042 |
| `fill_color` | Brand red F12D16 (not FF0000); only colors from palette |
| `border_spec` | Color + width + dashType per shape type |
| `font_spec` | Face + size + weight (Arial / Roboto Condensed only; sizes from approved scale) |
| `text_alignment` | Body left; titles per slide kind (title=left, section=center, content=left) |
| `effect_override` | Every shape has `<a:effectLst/>` (Rule #11) |

**YAML rule format example** (every rule has `spec_ref` so failed checks point at exact SKILL.md line):

```yaml
- id: red-accent-line-coords
  type: shape_coordinates
  applies_to: { slide_kind: content, shape_match: { fill: F12D16, h_lt: 0.1 } }
  expect: { x: 0.000, y: 0.500, w: 10.000, h: 0.042 }
  tolerance: { coord: 0.005 }
  severity: error
  spec_ref: "Rule #3 in SKILL.md"
```

**Slide classification: explicit tag.** Generator must put `<!--arch-style:content-->` / `:title` / `:section` in speaker notes of every slide. Heuristic classification was considered and rejected as fragile. Linter emits hard error per untagged slide.

**Report format (text, grouped by slide):**

```
deck.pptx · 24 slides

[Slide 2 · CONTENT]
  ✗ red-accent-line-coords (error)
      expected: x=0.000, y=0.500, w=10.000, h=0.042
      actual:   x=0.100, y=0.500, w=9.800, h=0.042
      spec:     SKILL.md → Rule #3

Summary: 22 passed · 2 failed · 0 warnings
Exit code: 1
```

**Validation gate** added to SKILL.md as new final section:
> After every generation/edit of an arch-style `.pptx`:
> 1. Run `uv run plugins/presentation/skills/pptx-arch-style/scripts/lint.py deck.pptx`
> 2. Exit ≠ 0 → fix violations, regenerate, repeat
> 3. Only after green linter → proceed to Anthropic visual-QA loop (render → PDF → JPEG → subagent inspection)
> 4. Every slide must carry `<!--arch-style:content|title|section-->` in speaker notes

**Scope cuts:**
- No static code linter (neither pptxgenjs nor python-pptx) — output check covers both runtimes by construction.
- No semantic / aesthetic / content checks — those live in the Anthropic visual-QA subagent loop or markitdown upstream.
- No auto-fix mode in v1 — report only.
- No `pptx-core-style` coverage — separate iteration.

**Open questions for the implementer (resolve during work):**
- Tolerance defaults per rule: start at 0.005in, may need per-rule overrides (e.g. red-line width h=0.042 may render as 0.0419 after round-trip). Calibrate during golden fixture creation.
- Inches vs EMU in YAML: keep YAML in inches (readable); linter converts internally.
- Which real deck was canonical in TASK-21 determines what to additionally cross-test against here.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 scripts/lint.py exists and runs as uv run plugins/presentation/skills/pptx-arch-style/scripts/lint.py <deck.pptx>
- [ ] #2 references/rules.yaml covers all 8 rule types with at least one instance each; every rule has spec_ref field
- [ ] #3 Linter exits 0 on fixtures/golden.pptx; exits 1 on each fixtures/violators/*.pptx with the expected rule id reported as failed
- [ ] #4 scripts/tests/gen_fixtures.js regenerates all fixtures deterministically from source (committed; node + pptxgenjs)
- [ ] #5 scripts/tests/test_lint.py passes under uv run pytest covering golden, violators, and edge tolerance cases
- [ ] #6 SKILL.md has a new final 'Validation' section with the 4-step gate protocol and speaker-notes tagging requirement
- [ ] #7 plugins/presentation/plugin.json version bumped (minor)
- [ ] #8 uv run ruff check . and uv run pytest both pass; task-reviewer agent returns APPROVED before merging
<!-- AC:END -->
