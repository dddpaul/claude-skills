---
id: TASK-12
title: Normalize emoji baseline in books PDF (wrap + scale)
status: Done
assignee: []
created_date: '2026-06-15 07:00'
updated_date: '2026-06-15 07:06'
labels: []
dependencies: []
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
In the books skill PDF output, color emoji (e.g., ✅ U+2705, ❌ U+274C, and any character in the high-plane pictograph block U+1F300–U+1FAFF) fall back to Apple Color Emoji. That font has a taller em-box and a different baseline than IBM Plex Serif, so the emoji glyphs visibly float above the surrounding text line and look oversized. Fix: post-process the converted HTML to wrap each color-emoji code point in `<span class="emoji">`, and add a small CSS rule that down-scales and lowers them onto the text baseline. Native serif glyphs in IBM Plex Serif (arrows → ↔, dingbats ✓ ✗ when typed explicitly) must NOT be wrapped — they already align correctly.

## Files to change

- `plugins/reading/skills/books/scripts/md-to-pdf.py`
- `plugins/reading/skills/books/references/styles.css`
- `plugins/reading/.claude-plugin/plugin.json`

## Change 1 — md-to-pdf.py emoji wrapping

Add a module-level compiled regex covering the high-plane pictograph blocks plus a few BMP code points that have emoji-presentation by default (so they fall back to Apple Color Emoji in the current font stack):

    EMOJI_RE = re.compile(r"([\U0001F300-\U0001FAFF\u2705\u274C\u2728])")

After `html_body = md.convert(raw)` and `toc_html = md.toc or ""`, but before the toc rewriting and `toc_section` assembly, apply the wrap to BOTH strings:

    html_body = EMOJI_RE.sub(r'<span class="emoji">\1</span>', html_body)
    toc_html = EMOJI_RE.sub(r'<span class="emoji">\1</span>', toc_html)

Do NOT wrap arrows (U+2190–U+21FF range), dingbat check/cross U+2713/U+2717, or anything else outside the listed code points — IBM Plex Serif renders those natively at the correct baseline.

## Change 2 — styles.css emoji rule

Append a single rule at the end of `styles.css`:

    .emoji { font-size: 0.85em; vertical-align: -0.1em; }

This shrinks the emoji em-box and nudges the glyph down so it sits on (or just above) the text baseline of the surrounding IBM Plex Serif text.

## Change 3 — plugin.json version

Bump `plugins/reading/.claude-plugin/plugin.json` `version` from `0.2.1` to `0.2.2` (patch — visual fix, no API or behavior change beyond the rendered PDF).

## Verification

Render the existing TASK-11 sanity sample (or a fresh equivalent) at the path shown below, containing both ✅ and ❌ inline in a paragraph plus an arrow → for control:

    /tmp/books-render-check-12.md

Render with:

    uv run plugins/reading/skills/books/scripts/md-to-pdf.py /tmp/books-render-check-12.md /tmp/books-render-check-12.pdf

Open the PDF and confirm:

- ✅ and ❌ glyphs sit on the same visual baseline as the surrounding text — they should no longer float above the cap-height line.
- ✅ and ❌ are visibly smaller than they were in the pre-fix render (closer to text x-height).
- Arrow → still renders as a serif IBM Plex Serif glyph at full body size (NOT wrapped, NOT shrunk).
- Cyrillic, lining digits, blue links, table styling all unchanged.
- TOC entries that happen to contain ✅/❌ also show the down-scaled glyph (verify the wrap applied to toc_html too).

## Quality gates

- `uv run ruff check .` passes.
- `uv run pytest` passes (no tests exist for this skill, so a clean pass is the expected outcome).
- task-reviewer agent verdict is APPROVED before marking Done and merging.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 md-to-pdf.py defines EMOJI_RE compiled regex matching the character class [\U0001F300-\U0001FAFF\u2705\u274C\u2728]
- [x] #2 md-to-pdf.py applies EMOJI_RE.sub wrapping with '<span class="emoji">\1</span>' to BOTH html_body and toc_html before injection
- [x] #3 md-to-pdf.py does NOT wrap arrows U+2190-U+21FF, dingbat check U+2713, or dingbat cross U+2717 (verify by absence of those code points from the regex character class)
- [x] #4 styles.css ends with a rule '.emoji { font-size: 0.85em; vertical-align: -0.1em; }'
- [x] #5 plugins/reading/.claude-plugin/plugin.json version is 0.2.2
- [x] #6 Rendering a sample md containing inline '✅' and '❌' and '→' produces a PDF where ✅ and ❌ are wrapped in <span class="emoji"> in the HTML pipeline and visibly sit on the surrounding text baseline rather than floating above the cap-height line; arrow → renders at full body size unchanged
- [x] #7 uv run ruff check . passes from repo root
- [x] #8 uv run pytest passes from repo root
- [x] #9 task-reviewer agent verdict on git diff master..HEAD is APPROVED
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Manual verification: /tmp/books-render-check-12.pdf

- ✅ ❌ ✨ 🎯 wrapped + scaled (0.85em) + vertical-align -0.1em — sit on/near text baseline, no longer float above cap-height
- → ✓ ✗ unchanged — full body size, native IBM Plex Serif serif glyphs (control passed)
- Mixed line side-by-side comparison: ✅ small/lowered, ✓ full-size body glyph — wrap targeting is correct
- ruff passes
- pytest: 'collected 0 items' (no tests in repo — project has no test suite)

task-reviewer verdict: APPROVED. All 8 testable ACs satisfied, regex class verified to exclude arrows U+2190-U+21FF, U+2713, U+2717.

Commit: `32d40e6` - task-12: normalize emoji baseline in books PDF (wrap + scale)
<!-- SECTION:NOTES:END -->
