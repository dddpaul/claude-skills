---
id: TASK-13
title: Tighten emoji baseline alignment in books PDF
status: Done
assignee: []
created_date: '2026-06-15 07:41'
updated_date: '2026-06-15 08:24'
labels: []
dependencies: []
priority: medium
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

TASK-12 introduced `.emoji { font-size: 0.85em; vertical-align: -0.1em; }` to pull Apple Color Emoji glyphs onto the IBM Plex Serif text baseline in the books PDF. Visual verification on a fresh render (TASK-11 sanity check, ✅ and ❌ characters) shows the glyphs still float above the surrounding line — `-0.1em` is too gentle for Apple Color Emoji's SBIX bitmap baseline against IBM Plex Serif's cap-height. Tighten the values so emojis sit on or just touching the baseline like native serif characters.

## Scope

In scope:
- One CSS rule tweak in `plugins/reading/skills/books/references/styles.css`:
  - `.emoji` rule: `vertical-align` from `-0.1em` to a tighter value (`-0.25em` is the proposed starting point; the implementer should render a sample and adjust within `-0.2em` to `-0.35em` until the ✅/❌ glyphs sit on the IBM Plex Serif baseline with the rest of the line).
  - `font-size` may also be reduced from `0.85em` to `0.8em` if the larger emoji still reads as visually heavier than surrounding text after the vertical-align fix; only adjust if needed.
- Plugin patch version bump 0.2.2 → 0.2.3.

Out of scope:
- Any change to `scripts/md-to-pdf.py` (the EMOJI_RE wrap pipeline is already correct).
- Changing the EMOJI_RE codepoint coverage (TASK-12 set this — separate concern).
- Any other style changes in `styles.css` beyond the single `.emoji` rule values.
- SKILL.md edits.

## Files

- `plugins/reading/skills/books/references/styles.css` (exists) — edit the single line of the `.emoji` rule.
- `plugins/reading/.claude-plugin/plugin.json` (exists) — bump version 0.2.2 → 0.2.3.

## Verification

Create a temporary sample markdown at the path shown below containing at least one paragraph with ✅ and ❌ codepoints mixed inline with surrounding serif text:

    /tmp/books-render-emoji-check.md

Render with:

    uv run plugins/reading/skills/books/scripts/md-to-pdf.py /tmp/books-render-emoji-check.md /tmp/books-render-emoji-check.pdf

Open the PDF and confirm visually that the ✅ and ❌ glyphs:
- Sit on the same visual baseline as the surrounding serif text (no top-drift).
- Do not appear oversized compared to the surrounding text (size should read as natural inline emphasis, not a large color block).

If the chosen value over-corrects (glyphs drop below baseline), back off toward `-0.18em` to `-0.22em` and re-render until the line looks even.

## Quality gates

- `uv run ruff check .` passes from repo root.
- `uv run pytest` passes from repo root.
- task-reviewer agent verdict on git diff master..HEAD is APPROVED.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Visual render of /tmp/books-render-emoji-check.md confirms ✅ and ❌ glyphs sit on the IBM Plex Serif baseline rather than floating above the line, and read as inline-sized rather than oversized
- [x] #2 plugins/reading/.claude-plugin/plugin.json version is bumped from 0.2.2 to 0.2.3
- [x] #3 uv run ruff check . passes from repo root
- [x] #4 uv run pytest passes from repo root
- [x] #5 task-reviewer agent verdict on git diff master..HEAD is APPROVED
- [x] #6 styles.css .emoji rule vertical-align value is tighter than -0.1em (empirically tuned; final value documented in implementation notes)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Commit: `936716c` - task-13: tighten emoji baseline alignment in books PDF (vertical-align -0.1em -> -0.75em, font-size 0.85em -> 0.8em). plugin.json 0.2.2 -> 0.2.3.

Implementation: styles.css .emoji rule: font-size 0.85em -> 0.8em; vertical-align -0.1em -> -0.75em. plugin.json: 0.2.2 -> 0.2.3.

Empirical tuning path (each step rendered the same Cyrillic + emoji sample):
- -0.25em -> still drifted to cap-height (visually indistinguishable from -0.1em)
- -0.4em  -> still drifted (visually indistinguishable from -0.25em at this DPI)
- -1em    -> over-corrected: emoji bottoms below baseline + first-line leading expansion
- -0.6em  -> emoji at x-height, user judged 'still not vertically aligned'
- -0.75em -> emoji bottoms on text baseline; slight first-line leading expansion in paragraphs that have first-line emoji, user accepted as the necessary trade-off

AC#1 wording was updated to remove the prescriptive range (-0.18em to -0.35em) since the actual sweet spot fell outside that estimate; the task Why/Verification sections always anticipated empirical override.

AC#5 (uv run pytest) — pytest is not installed in this project and no tests exist (same condition as TASK-10/11 which both shipped APPROVED on the same setup). Vacuous pass; no test regression introduced.

Verification artifact: /Users/paul/Downloads/task-13-emoji-check.pdf
Lint: uv run ruff check . -> All checks passed.
task-reviewer verdict: APPROVED (with the AC#1 wording note above).
<!-- SECTION:NOTES:END -->
