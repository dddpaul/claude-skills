# Feature Review: reading-books — 2026-06-14

**Verdict: Aligned**

## Drift List

No drift detected.

## Reviewer Notes (summary)

All nine brainstorm scope cuts are honored. All architectural decisions (push-only, iCloud-only transport, A4 portrait with 35mm right gutter, 1.4 line-height, Georgia serif, no syntax highlighting, single-file push, no Happy plugin code) are reflected verbatim in the diff. All six trigger phrases (3 EN + 3 RU) are present in SKILL.md frontmatter and the README example block carries the required subset. Atomic write via `.<slug>.pdf.tmp` + `os.replace` is implemented in `plugins/reading/skills/books/scripts/md-to-pdf.py`. `READING_ICLOUD_DIR` env var with the spec'd default path is documented. Marketplace gains the 4th entry; plugin.json carries `version 0.1.0`, `license Apache-2.0`, `author.email dddpaul@gmail.com`. README structural changes follow the established pattern. One sensible elaboration: SKILL.md invokes the script via `uv run …` rather than a bare interpreter call — consistent with project-level `CLAUDE.md` uv conventions, not drift.

Both tasks (TASK-7, TASK-8) carry task-reviewer APPROVED verdicts in their notes, and all 13 acceptance criteria across the two tasks are checked.

## Intent → Implementation Matrix

Passes run: 3 (Brainstorm Scope Cuts), 5 (Out-of-Scope Creep)
Passes skipped: 1 (no PRD), 2 (no PRD), 4 (no PRD)

| ID | Brainstorm Requirement | Status | Evidence |
|---|---|---|---|
| B-1 | New `reading` plugin in `plugins/reading/` | Delivered | `plugins/reading/.claude-plugin/plugin.json` |
| B-2 | Single `books` skill under plugin | Delivered | `plugins/reading/skills/books/SKILL.md` |
| B-3 | marketplace.json 4th entry with exact name/source/description | Delivered | diff lines 10-13 of `.claude-plugin/marketplace.json` |
| B-4 | plugin.json with v0.1.0, Apache-2.0, dddpaul@gmail.com | Delivered | `plugins/reading/.claude-plugin/plugin.json` lines 1-12 |
| B-5 | 6 trigger phrases (3 EN push + 3 RU push, no pull) | Delivered | SKILL.md frontmatter description |
| B-6 | Hard-fail if extension not `.md` | Delivered | SKILL.md Push step 1 |
| B-7 | Slug = basename without ext; sha1[:6] suffix on collision | Delivered | SKILL.md Push step 2 + "Slug collision" section |
| B-8 | Project root via `git rev-parse`, fallback to `dirname(source)` | Delivered | SKILL.md Push step 3 |
| B-9 | `READING_ICLOUD_DIR` env var with spec default | Delivered | SKILL.md "iCloud target path" + step 4 |
| B-10 | MD→PDF via `scripts/md-to-pdf.py` using markdown + weasyprint | Delivered | `scripts/md-to-pdf.py` imports both packages |
| B-11 | Atomic write via `.<name>.tmp` + `os.replace` | Delivered | `md-to-pdf.py` lines 26-30 |
| B-12 | A4 portrait, 35mm right gutter, 1.4 line-height | Delivered | `references/styles.css` lines 1-2 |
| B-13 | Georgia serif body 12pt; H1/H2/H3 at 18/15/13pt | Delivered | `styles.css` lines 2-5 |
| B-14 | Menlo monospace 10pt with light-grey background, no syntax highlighting | Delivered | `styles.css` line 6; no `codehilite` extension in `md-to-pdf.py` |
| B-15 | Black underlined links, max-width images | Delivered | `styles.css` lines 8-9 |
| B-16 | Page-break rules to prevent orphan headings | Delivered | `styles.css` lines 3-5 |
| B-17 | `uv add weasyprint markdown` as runtime deps | Delivered | `pyproject.toml` dependencies array |
| B-18 | Brew prerequisites documented (cairo, pango, gdk-pixbuf) | Delivered | SKILL.md "Dependencies" section |
| B-19 | README surfaces books skill + tree + install line | Delivered | `README.md` Skills, Project Structure, Installation sections |

## Scope Cut Violations

| Cut | Honored? | Evidence |
|---|---|---|
| No read-back / annotation extraction | Yes | No pull triggers, no callout-parsing code |
| No Books library auto-import (URL scheme) | Yes | No URL-scheme code present |
| No AirDrop / email fallback | Yes | iCloud Drive is sole transport |
| No EPUB output | Yes | Script writes PDF only |
| No syntax highlighting in v0.1 | Yes | Markdown extensions limited to `fenced_code`, `tables` |
| No bidirectional sync with offdesk | Yes | Separate plugin, separate skill |
| No Happy plugin code | Yes | No Happy-related files |
| No multi-file push in v0.1 | Yes | Script accepts a single source/target pair |
| No auto-cleanup of old PDFs | Yes | No cleanup logic |

None detected.
