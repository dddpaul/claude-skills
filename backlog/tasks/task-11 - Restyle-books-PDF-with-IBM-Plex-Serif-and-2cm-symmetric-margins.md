---
id: TASK-11
title: Restyle books PDF with IBM Plex Serif and 2cm symmetric margins
status: Done
assignee: []
created_date: '2026-06-15 05:19'
updated_date: '2026-06-15 06:12'
labels: []
dependencies: []
priority: medium
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

A user of the reading:books skill (v0.2.0) compared its Georgia-based weasyprint output against an older one-off PDF render of the same markdown done via pandoc+xelatex with PT Serif, and strongly preferred the older render. The two complaints about Georgia: (a) Georgia uses oldstyle figures by default, so digits visibly 'jump' against the baseline in technical text; (b) the user wanted a more sober/strict serif. After a side-by-side option review they picked IBM Plex Serif as the primary body font (lining figures, broad Cyrillic coverage, technical/documentation feel). For the ✅ emoji glyph that PT Serif and IBM Plex Serif both lack, the plan is a font-fallback to 'Apple Color Emoji' (built into macOS). Unicode arrows (→ U+2192, ↔ U+2194) are covered by IBM Plex Serif. The overall goal is to bring the books skill output close to that old pandoc+xelatex look without changing the rendering engine (stay on weasyprint).

## Scope

In scope:
- CSS-only changes in `references/styles.css`:
  - body font-family: `'IBM Plex Serif', 'PT Serif', 'Apple Color Emoji', 'Times New Roman', serif`
  - body: `font-variant-numeric: lining-nums` (explicit, defends against any future fallback to a font that defaults to oldstyle)
  - code/pre font-family: `'IBM Plex Mono', Menlo, Consolas, monospace`
  - @page margin: `20mm` symmetric (was `15mm 15mm 15mm 20mm` — i.e., asymmetric)
  - link color: blue hex (`#0050b3` or similar pleasant blue), currently black underlined
- `SKILL.md` text updates: PDF layout section + Dependencies section
- Bump plugin version 0.2.0 → 0.2.1 (patch — content tweak, no behavioral/API change)

Out of scope:
- Replacing the rendering engine (do NOT swap weasyprint for pandoc — this is a CSS port, not an engine swap)
- Any changes to `scripts/md-to-pdf.py` (the markdown→HTML pipeline is unchanged; only styles.css)
- Adding new SKILL.md features beyond the layout/deps doc update
- Touching styling for tables, TOC, page footer beyond the body font flowing through automatically
- Adding a config knob for the user to pick fonts (deferred — out of scope for this restyle)

## Files

- `plugins/reading/skills/books/references/styles.css` (exists) — bulk of the change: body/code font-family, font-variant-numeric, @page margin, a {color}
- `plugins/reading/skills/books/SKILL.md` (exists) — update 'PDF layout' section (font/margin/link values) and 'Dependencies' section (add `brew install --cask font-ibm-plex`)
- `plugins/reading/.claude-plugin/plugin.json` (exists) — bump `version` from `0.2.0` to `0.2.1`

## Source

Source: /Users/paul/Private/Alfa/Projects/standard/stacks@f05f0eb4c13c
Source design context (read-only, do NOT modify): the user's test corpus is the doc at `/Users/paul/Private/Alfa/Projects/standard/stacks/backlog/docs/doc-6 - Camunda-8-in-Russian-software-registry.md` — a Russian-language technical doc with Cyrillic + ✅ + → / ↔ + ASCII box-drawing chars. This is what they will use to eyeball-verify after the change lands.

## Before starting (destination Claude validation checklist)

Before running this task, verify:
1. All `(exists)` file paths in the Files section still exist in this repo.
2. Each AC is objectively pass/fail (a grep, test invocation, build command, or visible behavior — not 'works correctly').
3. All dependencies in the task's frontmatter are status=Done.
4. Out-of-scope items are not accidentally pulled in by ambiguous AC.

If anything is unclear or any check fails: STOP and ask the user. Do NOT start work blindly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 references/styles.css: body font-family stack begins with 'IBM Plex Serif' and includes 'Apple Color Emoji' as a fallback; code/pre font-family begins with 'IBM Plex Mono'
- [x] #2 references/styles.css: body declares font-variant-numeric: lining-nums
- [x] #3 references/styles.css: @page margin is 20mm symmetric (all four sides); 'a { color }' is a blue hex value (not black)
- [x] #4 SKILL.md 'PDF layout' section reflects new font / margin / link values; 'Dependencies' section documents 'brew install --cask font-ibm-plex' alongside the existing cairo/pango/gdk-pixbuf line
- [x] #5 .claude-plugin/plugin.json version bumped from 0.2.0 to 0.2.1
- [x] #6 uv run ruff check . passes from repo root (no new violations introduced)
- [x] #7 Manual verification recorded in task notes: rendered PDF (any test markdown) shows IBM Plex Serif body, lining digits (uniform baseline), valid emoji glyph (Apple Color Emoji color image), arrow glyphs render, 2cm symmetric margins, blue hyperlinks
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Manual verification render: /tmp/books-render-check-11.pdf

Embedded fonts (pdffonts): IBM-Plex-Serif (body), IBM-Plex-Serif-Bold (headings/bold), IBM-Plex-Mono (code), Apple-Color-Emoji (✅ ❌), Georgia (@bottom-center footer page number — preserved per scope rule 'do not change page footer styling beyond body-font automatic flow-through').

Visual checks:
- IBM Plex Serif body — yes (distinct from Georgia; rationalist letterforms)
- Lining digits — yes ('1234567890', '8.6.0', '128 544', '79.3' all on uniform baseline)
- Apple Color Emoji ✅ — yes (green check + red ❌ render as color glyphs)
- Unicode arrows → ↔ — yes (serif glyphs, no fallback square)
- Cyrillic — yes ('проектирование, реализация, тестирование' clean)
- 2cm symmetric margins — yes (visible even whitespace on all four sides)
- Blue hyperlinks — yes ('Claude Code' anchor is #0050b3 underlined)
- IBM Plex Mono code — yes ('monospace_token_42' + def block in mono)
- Tables / TOC / page footer unchanged (out of scope)

task-reviewer verdict: APPROVED. All 7 ACs satisfied, diff scoped to the three expected files, no out-of-scope drift, ruff passes. @bottom-center remains on Georgia per scope rule.

Commit: `15ef479` - task-11: restyle books PDF with IBM Plex Serif and 2cm symmetric margins
<!-- SECTION:NOTES:END -->
