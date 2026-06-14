---
id: TASK-9
title: 'Fix books PDF rendering: strip frontmatter and add table borders'
status: Done
assignee: []
created_date: '2026-06-14 16:30'
updated_date: '2026-06-14 16:33'
labels:
  - 'feature:reading-books'
dependencies: []
priority: medium
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
After v0.1.0 shipped, real-iPad testing revealed two rendering defects in the books skill:

1. **YAML frontmatter collapses to a single line.** When the source markdown begins with a YAML frontmatter block (`---\nkey: value\n...\n---`), the `markdown` Python package does not strip it. The two `---` lines render as horizontal rules and the intervening `key: value` lines collapse into one paragraph (no blank lines separate them, so they flow together).

2. **Tables render without borders.** The `tables` markdown extension emits plain `<table>` / `<th>` / `<td>` HTML, but `references/styles.css` has no rules for those elements, so weasyprint renders them with no visible structure.

Both are content tweaks → bump the reading plugin version per CLAUDE.md SemVer rule.

## Fix 1 — strip leading YAML frontmatter

Edit `plugins/reading/skills/books/scripts/md-to-pdf.py` so that, immediately before the `markdown.markdown(...)` call, it checks whether the source content begins with a YAML frontmatter block and strips it. Use stdlib only:

```python
import re

raw = src.read_text(encoding='utf-8')
# Strip leading YAML frontmatter if present.
raw = re.sub(r'\A---\r?\n.*?\r?\n---\r?\n', '', raw, count=1, flags=re.DOTALL)
html_body = markdown.markdown(raw, extensions=['fenced_code', 'tables'])
```

The regex matches only an opening `---` at the very start of the file (`\A`), then any content (DOTALL), then a closing `---\n` — and consumes the trailing newline so the resulting body has no leading blank. If no frontmatter is present, the substitution is a no-op.

## Fix 2 — add table border CSS

Append to `plugins/reading/skills/books/references/styles.css`:

```css
table { border-collapse: collapse; width: 100%; margin: 8px 0; }
th, td { border: 1px solid #999; padding: 4px 8px; text-align: left; vertical-align: top; }
th { background: #f0f0f0; }
```

`border-collapse: collapse` so adjacent cells share a single 1px line; the grey header background mirrors the existing `code` block treatment.

## Version bump

`plugins/reading/.claude-plugin/plugin.json`: `"version": "0.1.0"` → `"version": "0.1.1"`.

## Out of scope

- No changes to other plugins (architect, presentation, obsidian).
- No changes to SKILL.md prose (existing layout description still accurate; tables and frontmatter handling are bug fixes, not new features).
- No changes to README.md (no user-facing surface changed).
- No new Python dependencies (stdlib `re` is sufficient).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 plugins/reading/skills/books/scripts/md-to-pdf.py imports 're' and contains a re.sub call with the pattern '\A---' (stripping leading YAML frontmatter before markdown.markdown is invoked)
- [x] #2 Running md-to-pdf.py on a markdown file whose first 4 lines are '---\nfoo: bar\nbaz: qux\n---' produces a PDF whose first rendered content is NOT the literal text 'foo: bar baz: qux' (the frontmatter is stripped, not flattened)
- [x] #3 plugins/reading/skills/books/references/styles.css contains a 'table' rule with 'border-collapse: collapse' and a 'th, td' rule with 'border: 1px solid'
- [x] #4 plugins/reading/.claude-plugin/plugin.json version field is exactly '0.1.1'
- [x] #5 uv run ruff check . returns exit code 0
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: 1) Strip leading YAML frontmatter via regex in md-to-pdf.py before markdown conversion. 2) Add table/th/td border CSS to styles.css. 3) Bump plugin version 0.1.0 -> 0.1.1.

Commit: `d1c9a4a` - task-9: fix books PDF rendering — strip frontmatter, add table borders

Implemented: re.sub on \A--- pattern strips leading frontmatter in md-to-pdf.py; appended table/th/td CSS rules with border-collapse:collapse; bumped reading plugin 0.1.0->0.1.1. Verified: ruff clean; HTML output of <front>+#Hello yields '<h1>Hello</h1><p>This is a test.</p>' with no frontmatter leakage. task-reviewer agent: APPROVED.
<!-- SECTION:NOTES:END -->
