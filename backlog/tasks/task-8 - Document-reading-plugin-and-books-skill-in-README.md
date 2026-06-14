---
id: TASK-8
title: Document reading plugin and books skill in README
status: Done
assignee: []
created_date: '2026-06-14 15:26'
updated_date: '2026-06-14 15:43'
labels:
  - 'feature:reading-books'
dependencies:
  - TASK-7
priority: medium
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
After TASK-7 lands the reading plugin and books skill, README.md must surface them following the structural pattern already established for architect/presentation/obsidian (see current README.md).

## Skills section — add new entry

Add a new entry for `books`, immediately under the existing offdesk entry. Follow the format of the others: heading, plugin tag, 1-2 sentence summary, Usage, Example block.

Suggested heading and tag:

```markdown
### books

*Plugin: reading*

Push markdown files from any project to Apple Books on iPad as PDF for off-desk reading with Apple Pencil annotations. iCloud Drive → tap to open in Books. Push-only — pen marks stay with the human.

**Usage**: Ask Claude to send a doc to books for review on iPad.

**Example**:
```
send to books
положи это в books
почитаю на айпаде
```
```

## Project Structure section — extend the tree

Extend the existing project-structure tree to include the new plugin subtree (rebalance the branch glyphs so `reading` becomes the last sibling with `└──`):

```text
plugins/
├── architect/
├── presentation/
├── obsidian/
│   ├── .claude-plugin/
│   │   └── plugin.json
│   └── skills/
│       └── offdesk/
│           ├── SKILL.md
│           └── references/
│               └── setup.md
└── reading/
    ├── .claude-plugin/
    │   └── plugin.json
    └── skills/
        └── books/
            ├── SKILL.md
            ├── references/
            │   └── styles.css
            └── scripts/
                └── md-to-pdf.py
```

## Installation section — add reading install line

Add the reading install line alongside the existing architect, presentation, and obsidian lines:

```text
/plugin install reading@dddpaul-claude-skills    # books
```

## Out of scope

- No changes to 'Creating New Skills' section (existing convention still applies).
- No changes to marketplace.json (TASK-7 owns that).
- No changes to skills in other plugins.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 README.md Skills section contains a new subheading for 'books' (level matching existing skill subheadings) with the literal text '*Plugin: reading*' beneath it
- [x] #2 README.md Project Structure tree contains a line showing plugins/reading/skills/books/ and lines showing references/styles.css and scripts/md-to-pdf.py under it
- [x] #3 README.md Installation block contains the literal string '/plugin install reading@dddpaul-claude-skills'
- [x] #4 README.md Skills section's books subsection contains all three literal triggers: 'send to books', 'положи это в books', 'почитаю на айпаде'
- [x] #5 uv run ruff check . returns exit code 0
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: Update README.md to add (1) books skill entry under offdesk in Skills section with required triggers, (2) extend Project Structure tree with plugins/reading/skills/books/ including references/styles.css and scripts/md-to-pdf.py, (3) add /plugin install reading line in Installation block. Then run ruff to verify lint passes.

Commit: `3e494de` - task-8: document reading plugin and books skill in README

Implemented: README.md updates — books skill entry under offdesk in Skills section (heading + Plugin tag + summary + Usage + Example with three triggers), Project Structure tree extended with plugins/reading/skills/books/ subtree (references/styles.css, scripts/md-to-pdf.py), and reading install line added to Installation block. Lint passes. task-reviewer: APPROVED.
<!-- SECTION:NOTES:END -->
