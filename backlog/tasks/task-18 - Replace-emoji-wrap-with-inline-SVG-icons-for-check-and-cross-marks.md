---
id: TASK-18
title: Replace emoji wrap with inline SVG icons for check and cross marks
status: Done
assignee: []
created_date: '2026-06-15 11:44'
updated_date: '2026-06-15 11:49'
labels: []
dependencies: []
priority: medium
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

The Apple-Color-Emoji approach (TASK-12 `.emoji { font-size, vertical-align }`) cannot be fully fixed by CSS tuning:

- SBIX bitmap font metrics don't compose cleanly with serif text-flow metrics; baseline never lands exactly on the text baseline across all contexts (body 11pt, table 9pt, headings 18/15/13pt).
- Em-based `font-size: 0.8em` cascades multiplicatively, producing a microscopic 7.2pt glyph inside a 9pt table cell.
- Negative `vertical-align` expands the line box, growing leading per CSS spec.
- Even where IBM Plex Serif has the codepoint (e.g. U+274C ❌), Unicode's `Emoji_Presentation=Yes` rule causes weasyprint's font cascade to prefer Apple Color Emoji anyway.

**Visually ideal fix:** replace each recognized emoji codepoint with a hand-coded inline SVG. SVG is a "replaced element" — weasyprint uses geometric bounds for sizing and vertical alignment, completely bypassing font-metric guesswork. Same icon renders identically in body, table cell, heading, TOC entry.

## Scope

In scope:
- `plugins/reading/skills/books/scripts/md-to-pdf.py`:
  - Remove the `EMOJI_RE` and `EMOJI_SUB` constants.
  - Add a new `EMOJI_SVG_MAP` dict keyed by emoji codepoint, value = full inline SVG markup string. Initial mapping covers ✅ (U+2705) → green-circle-with-white-check, and ❌ (U+274C) → red-X-strokes.
  - Add a compiled regex `EMOJI_SVG_RE` matching any codepoint in `EMOJI_SVG_MAP.keys()` and a helper that substitutes via the map.
  - In `main()`: replace the existing `EMOJI_RE.sub(EMOJI_SUB, html_body)` call with the new SVG transform on `html_body`.
  - In the toc-flatten rows comprehension: replace the existing `EMOJI_RE.sub(EMOJI_SUB, name)` call with the new SVG transform on `name`.
- `plugins/reading/skills/books/references/styles.css`:
  - Remove the `.emoji { font-size: 0.8em; vertical-align: -0.75em; }` rule.
  - Add `.icon { height: 0.9em; width: 0.9em; vertical-align: -0.12em; }`.
- `plugins/reading/.claude-plugin/plugin.json` — patch bump 0.2.7 → 0.2.8.

Out of scope:
- High-plane pictograph emoji (U+1F300-U+1FAFF) — those drop back to font-cascade rendering (Apple Color Emoji). Most technical docs in this skill's use case won't contain them; ✨ (U+2728) handling from TASK-12 is intentionally retired here. If needed later, add more entries to `EMOJI_SVG_MAP`.
- Any other CSS rule beyond the two changes above.
- Any other md-to-pdf.py change beyond the EMOJI_RE/EMOJI_SUB removal, the new map + regex + transform, and the two .sub() call swaps.
- Heading sizes, body font, TOC styling, page margins, table styling, link color, font stack, lining-nums declaration.
- SKILL.md — no changes (the documented values don't change).

## Files

- `plugins/reading/skills/books/scripts/md-to-pdf.py` (exists)
- `plugins/reading/skills/books/references/styles.css` (exists)
- `plugins/reading/.claude-plugin/plugin.json` (exists)

## Change 1 — md-to-pdf.py SVG transform

Replace the module-level `EMOJI_RE` and `EMOJI_SUB` constants with:

    EMOJI_SVG_MAP = {
        "✅": (
            '<svg class="icon" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">'
            '<circle cx="8" cy="8" r="7" fill="#2e8b57"/>'
            '<path d="M4.5 8l2.5 2.5 4.5-5" stroke="white" stroke-width="1.8" '
            'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            "</svg>"
        ),
        "❌": (
            '<svg class="icon" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M3.5 3.5 L12.5 12.5 M12.5 3.5 L3.5 12.5" '
            'stroke="#c41e3a" stroke-width="2.5" stroke-linecap="round"/>'
            "</svg>"
        ),
    }
    EMOJI_SVG_RE = re.compile("|".join(re.escape(k) for k in EMOJI_SVG_MAP))

    def _svg_emoji(html: str) -> str:
        return EMOJI_SVG_RE.sub(lambda m: EMOJI_SVG_MAP[m.group(0)], html)

In `main()`, change the body emoji pass from `html_body = EMOJI_RE.sub(EMOJI_SUB, html_body)` to `html_body = _svg_emoji(html_body)`.

In the toc-flatten rows comprehension, change `{EMOJI_RE.sub(EMOJI_SUB, name)}` to `{_svg_emoji(name)}`.

## Change 2 — styles.css icon rule

Remove the line:

    .emoji { font-size: 0.8em; vertical-align: -0.75em; }

Add immediately after the .toc-h3 rule:

    .icon { height: 0.9em; width: 0.9em; vertical-align: -0.12em; }

## Change 3 — plugin.json version

Bump `version` from `0.2.7` to `0.2.8` (patch — visual fix, swap emoji rendering strategy).

## Verification

Render a sample markdown that exercises ✅ and ❌ in body, list, table, heading:

    /tmp/books-emoji-svg-check.md should contain at least:
      # ✅ Status ✅
      Inline body: build ✅, tests ✅, deploy ❌.
      - ✅ item one
      - ❌ item two
      A table with status cells (one column with ✅, another with ❌).

Render with the script. Open the PDF and confirm:
- ✅ and ❌ glyphs sit ON the text baseline (no top-drift) in EVERY context (body paragraph, list, table cell, heading).
- Glyph size scales naturally with surrounding text (smaller in table, larger in heading) without any context-specific tuning.
- No line-box expansion (paragraph leading visibly equal across lines that do and don't contain emoji).
- Visual: ✅ is a small green circle with a white check; ❌ is two crossed red strokes.

Also re-render the Camunda doc as a regression check:

    uv run plugins/reading/skills/books/scripts/md-to-pdf.py "/Users/paul/Private/Alfa/Projects/standard/stacks/backlog/docs/doc-6 - Camunda-8-in-Russian-software-registry.md" /tmp/task-18-camunda.pdf

Confirm c8-saas image still renders, TOC alignment still pixel-perfect, table styling unchanged from TASK-17.

Save both artifacts to `~/Downloads/task-18-emoji-svg.pdf` and `~/Downloads/task-18-camunda.pdf`.

## Quality gates

- `uv run ruff check .` passes from repo root.
- task-reviewer agent verdict on git diff master..HEAD is APPROVED.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 md-to-pdf.py no longer contains EMOJI_RE or EMOJI_SUB module-level constants
- [x] #2 md-to-pdf.py contains EMOJI_SVG_MAP dict mapping the U+2705 codepoint to a green-circle-with-white-check SVG and the U+274C codepoint to a red-X SVG
- [x] #3 md-to-pdf.py contains EMOJI_SVG_RE compiled from EMOJI_SVG_MAP keys and a _svg_emoji helper that substitutes via the map
- [x] #4 Body and TOC entry names are run through _svg_emoji (the prior EMOJI_RE.sub calls in those two spots are gone)
- [x] #5 styles.css no longer contains the .emoji rule
- [x] #6 styles.css contains .icon rule with height 0.9em, width 0.9em, vertical-align -0.12em
- [x] #7 Verification render shows check and cross glyphs on text baseline across body, list, table, and heading contexts; no line-box expansion
- [x] #8 Regression render of the Camunda doc shows no changes to image rendering, TOC alignment, or table styling
- [x] #9 plugins/reading/.claude-plugin/plugin.json version bumped from 0.2.7 to 0.2.8
- [x] #10 uv run ruff check . passes from repo root
- [x] #11 task-reviewer agent verdict on git diff master..HEAD is APPROVED
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Commit: `708179d` - task-18: replace emoji wrap with inline SVG icons for U+2705 and U+274C. md-to-pdf.py EMOJI_RE/EMOJI_SUB -> EMOJI_SVG_MAP + _svg_emoji helper. styles.css .emoji rule -> .icon rule using geometric height/vertical-align (replaced element metrics bypass font-cascade). plugin 0.2.7->0.2.8.

Implementation:
- md-to-pdf.py: removed EMOJI_RE + EMOJI_SUB; added EMOJI_SVG_MAP (✅ -> green-circle-white-check SVG, ❌ -> red-X SVG), EMOJI_SVG_RE, _svg_emoji helper. Body and toc-flatten now call _svg_emoji().
- styles.css: removed .emoji rule; added .icon { height: 0.9em; width: 0.9em; vertical-align: -0.12em } (geometric metrics on replaced element).
- plugin.json: 0.2.7 -> 0.2.8.

Verification artifacts:
- /Users/paul/Downloads/task-18-emoji-svg.pdf: icons sit on baseline across body / list / table / H1 / H2 / H3 / TOC; sizing scales naturally with surrounding font-size (no per-context tuning); no line-box expansion (verified by three consecutive paragraph lines with/without icons having identical leading).
- /Users/paul/Downloads/task-18-camunda.pdf: regression check — c8-saas image still renders, TOC alignment still pixel-perfect, table styling unchanged from TASK-17.

Note: ✨ (U+2728) handling from TASK-12 intentionally retired; can be added back to EMOJI_SVG_MAP if needed. High-plane pictograph emoji (U+1F300-U+1FAFF) fall back to font-cascade (Apple Color Emoji); add to map on demand.

Lint: uv run ruff check . -> All checks passed.
task-reviewer verdict: APPROVED.
<!-- SECTION:NOTES:END -->
