---
id: TASK-7
title: Implement reading plugin and books skill
status: Done
assignee: []
created_date: '2026-06-14 15:26'
updated_date: '2026-06-14 15:39'
labels:
  - 'feature:reading-books'
dependencies: []
priority: medium
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Ship a new `reading` plugin in this monorepo containing one skill `books` that pushes a markdown file from the active project to Apple Books on iPad as a PDF for off-desk reading with Apple Pencil annotations. Push-only — no read-back, no annotation extraction, no Books auto-import, no EPUB.

## Files to create

```text
.claude-plugin/marketplace.json          # add 4th entry
plugins/reading/.claude-plugin/plugin.json
plugins/reading/skills/books/SKILL.md
plugins/reading/skills/books/references/styles.css
plugins/reading/skills/books/scripts/md-to-pdf.py
pyproject.toml                            # uv add weasyprint markdown
```

## marketplace.json — add 4th entry

Append after the existing obsidian entry:

```json
{
  "name": "reading",
  "source": "./plugins/reading",
  "description": "Push markdown from any project to Apple Books on iPad as PDF for off-desk reading with Apple Pencil annotations. Push-only via iCloud Drive."
}
```

## plugins/reading/.claude-plugin/plugin.json

```json
{
  "name": "reading",
  "version": "0.1.0",
  "description": "MD → PDF → iCloud Drive → Apple Books on iPad. Push-only; pen marks stay with the human.",
  "author": {
    "name": "Pavel Derendyaev",
    "email": "dddpaul@gmail.com"
  },
  "homepage": "https://github.com/dddpaul/claude-skills",
  "repository": "https://github.com/dddpaul/claude-skills",
  "license": "Apache-2.0"
}
```

## SKILL.md — frontmatter triggers

Push only (no pull triggers).

- EN push: `send to books`, `read on ipad`, `review on books`
- RU push: `положи это в books`, `положи это в книги`, `почитаю на айпаде`

## Push procedure (document in SKILL.md body)

```text
1. Resolve absolute path of the source markdown file. Hard-fail if the extension is not .md.
2. Compute slug = Path(source).stem. On collision in target dir, append -<sha1(absolute_source_path)[:6]>. Mirror the offdesk slug-collision pattern at plugins/obsidian/skills/offdesk/SKILL.md.
3. Resolve project root via 'git rev-parse --show-toplevel' with fallback to dirname(source). The basename of the root becomes the iCloud subfolder name.
4. Resolve iCloud target:
     ICLOUD_DIR="${READING_ICLOUD_DIR:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Reading}"
     TARGET_DIR="$ICLOUD_DIR/<project-basename>"
     mkdir -p "$TARGET_DIR"
5. Convert MD to PDF by running the script scripts/md-to-pdf.py with the source markdown path and target pdf path as arguments.
6. Atomic write: the script writes to a hidden temporary file alongside the target (filename prefixed with a dot and suffixed with .tmp), then os.replace it to the final target.
7. Report the final iCloud path so user can tap-to-open in Files.app → Open in Books.
```

## scripts/md-to-pdf.py

Single-file Python using stdlib plus the `markdown` and `weasyprint` packages:

```python
import sys
from pathlib import Path
import markdown
from weasyprint import CSS, HTML

def main():
    src = Path(sys.argv[1]).resolve()
    dst = Path(sys.argv[2]).resolve()
    css_path = Path(__file__).parent.parent / 'references' / 'styles.css'
    html_body = markdown.markdown(src.read_text(encoding='utf-8'),
                                  extensions=['fenced_code', 'tables'])
    html_doc = f'<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>{html_body}</body></html>'
    tmp = dst.with_name('.' + dst.name + '.tmp')
    HTML(string=html_doc).write_pdf(str(tmp), stylesheets=[CSS(filename=str(css_path))])
    tmp.replace(dst)
    print(str(dst))

if __name__ == '__main__':
    main()
```

## references/styles.css

```css
@page { size: A4 portrait; margin: 20mm 35mm 20mm 20mm; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 12pt; line-height: 1.4; }
h1 { font-size: 18pt; page-break-before: auto; break-inside: avoid; }
h2 { font-size: 15pt; page-break-before: auto; break-inside: avoid; }
h3 { font-size: 13pt; break-inside: avoid; }
code, pre { font-family: Menlo, Consolas, monospace; font-size: 10pt; background: #f0f0f0; }
pre { padding: 8px; }
a { color: black; text-decoration: underline; }
img { max-width: 100%; }
```

## Dependencies

Run `uv add weasyprint markdown` so both are in `pyproject.toml` as runtime deps (not script-pinned). macOS system prerequisites (`cairo`, `pango`, `gdk-pixbuf` via Homebrew) must be documented inside SKILL.md as install requirements.

## Out of scope

- No README changes (TASK-8 owns README).
- No changes to existing plugins (architect, presentation, obsidian).
- No pull triggers, no annotation extraction, no Books auto-import URL scheme, no EPUB, no syntax highlighting.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 .claude-plugin/marketplace.json contains an entry with "name": "reading" and "source": "./plugins/reading"
- [x] #2 plugins/reading/.claude-plugin/plugin.json exists and is valid JSON (python -m json.tool succeeds) with version "0.1.0", license "Apache-2.0", and author.email "dddpaul@gmail.com"
- [x] #3 plugins/reading/skills/books/SKILL.md exists and its frontmatter triggers include all six literal phrases: 'send to books', 'read on ipad', 'review on books', 'положи это в books', 'положи это в книги', 'почитаю на айпаде'
- [x] #4 plugins/reading/skills/books/SKILL.md body documents the READING_ICLOUD_DIR env var with default path '$HOME/Library/Mobile Documents/com~apple~CloudDocs/Reading'
- [x] #5 plugins/reading/skills/books/scripts/md-to-pdf.py exists, imports both 'markdown' and 'weasyprint', and writes to a '.tmp' path before os.replace to the final target
- [x] #6 plugins/reading/skills/books/references/styles.css exists and contains '@page' with margin including '35mm' (right gutter for pen) and 'line-height: 1.4'
- [x] #7 pyproject.toml lists both 'weasyprint' and 'markdown' under [project.dependencies] or [tool.uv] runtime deps
- [x] #8 uv run ruff check . returns exit code 0
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: Create plugins/reading/ structure mirroring obsidian plugin. Add reading entry to marketplace.json (4th entry, after obsidian). Create plugin.json with v0.1.0 + Apache-2.0 + dddpaul@gmail.com. Write SKILL.md with frontmatter triggers (6 phrases: 3 EN + 3 RU push-only) and body documenting READING_ICLOUD_DIR env var, slug collision pattern (mirroring offdesk sha1[:6]), and push procedure. Create scripts/md-to-pdf.py with markdown+weasyprint, atomic write via .tmp + os.replace. Create references/styles.css with @page A4, 35mm right gutter, line-height 1.4. Add weasyprint+markdown via 'uv add'. Verify with ruff.

Commit: `1dcb864` - task-7: add reading plugin with books skill

Implemented reading plugin and books skill. Files: plugins/reading/.claude-plugin/plugin.json (v0.1.0, Apache-2.0), plugins/reading/skills/books/SKILL.md (6 trigger phrases, READING_ICLOUD_DIR docs, slug-collision mirroring offdesk), plugins/reading/skills/books/scripts/md-to-pdf.py (markdown+weasyprint, atomic .tmp + os.replace), plugins/reading/skills/books/references/styles.css (A4 portrait, 35mm right gutter, 1.4 line-height). marketplace.json gains a 4th entry. pyproject.toml gains weasyprint + markdown. Verified: all 8 AC pass; uv run ruff check . — exit 0; task-reviewer agent verdict APPROVED.
<!-- SECTION:NOTES:END -->
