# Feature Review: reading-books — 2026-06-14 (post-v0.1.1)

**Verdict: Aligned**

Second cumulative review, after TASK-9 closed two real-iPad rendering defects in v0.1.0 and bumped the plugin to v0.1.1. In-scope tasks: TASK-7, TASK-8, TASK-9.

## Drift List

No drift detected.

TASK-9's two changes are bug fixes against the v0.1.0 implementation, not scope expansion:

- The frontmatter strip closes a defect where `markdown.markdown()` leaks YAML keys into the rendered body — aligns with the brainstorm's "PDF is opaque" stance ("No frontmatter, no manifest, no metadata"). Uses stdlib `re` only; no new dependencies; no behavior change when no frontmatter is present.
- The table border CSS fills a styling gap for an HTML element type the existing converter already emits (the `tables` markdown extension was enabled in TASK-7). The brainstorm explicitly defined `references/styles.css` as the tweakable styling surface, and the new rules are consistent with the existing `code`-block grey-background treatment.

## Reviewer Notes (summary)

**Passes run:** 3 (Brainstorm Scope Cuts), 5 (Out-of-Scope Creep)
**Passes skipped:** 1, 2, 4 (no PRD)

All 9 brainstorm scope cuts remain honored end-to-end across v0.1.0 + v0.1.1: no read-back, no Books auto-import, no AirDrop/email fallback, no EPUB, no syntax highlighting, no offdesk sync, no Happy plugin code, no multi-file push, no auto-cleanup. Version bump 0.1.0 → 0.1.1 correctly follows the CLAUDE.md SemVer rule for content tweaks. The brainstorm's pin at 0.1.0 is a frozen Phase-3-end snapshot — not a contradiction of the v0.1.1 patch.

All 18 acceptance criteria across the three tasks are checked. All three carry task-reviewer APPROVED verdicts.

## Intent → Implementation Matrix (delta from prior review)

The v0.1.0 matrix (B-1 through B-19) remains Delivered. Two refinements landed in TASK-9:

| ID | Brainstorm Requirement | Status | Evidence |
|---|---|---|---|
| B-12 | A4 portrait, 35mm right gutter, 1.4 line-height | Delivered | `references/styles.css` lines 1-2 (unchanged from v0.1.0) |
| B-14 | Menlo monospace 10pt with light-grey background, no syntax highlighting | Delivered | `styles.css` line 6; markdown extensions limited to `fenced_code`, `tables` |
| **B-12a** | (NEW, gap-fill) Table styling within the existing CSS surface | Delivered | `styles.css` final three rules: `table { border-collapse: collapse; ... }`, `th, td { border: 1px solid #999; ... }`, `th { background: #f0f0f0; }` |
| **B-10a** | (NEW, gap-fill) YAML frontmatter stripped before `markdown.markdown()` | Delivered | `md-to-pdf.py` adds `import re` and `re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", raw, count=1, flags=re.DOTALL)` immediately before the markdown conversion call |

Both B-12a and B-10a close defects exposed by real-iPad use; neither expands design intent.

## Scope Cut Violations

| Cut | Honored? | Evidence |
|---|---|---|
| No read-back / annotation extraction | Yes | No pull triggers, no callout-parsing code |
| No Books library auto-import (URL scheme) | Yes | No URL-scheme code present |
| No AirDrop / email fallback | Yes | iCloud Drive is sole transport |
| No EPUB output | Yes | Script writes PDF only |
| No syntax highlighting in v0.1 | Yes | Markdown extensions still limited to `fenced_code`, `tables` |
| No bidirectional sync with offdesk | Yes | Separate plugin, separate skill |
| No Happy plugin code | Yes | No Happy-related files |
| No multi-file push in v0.1 | Yes | Script accepts a single source/target pair |
| No auto-cleanup of old PDFs | Yes | No cleanup logic |

None detected.
