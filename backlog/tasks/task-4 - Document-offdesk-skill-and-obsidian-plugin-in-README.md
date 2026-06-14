---
id: TASK-4
title: Document offdesk skill and obsidian plugin in README
status: To Do
assignee: []
created_date: '2026-06-14 06:13'
updated_date: '2026-06-14 06:47'
labels:
  - 'feature:offdesk'
dependencies:
  - TASK-3
priority: medium
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
After TASK-3 lands the obsidian plugin and offdesk skill, the README must surface them so teammates can install and use them. Mirror the structural pattern already established for the architect and presentation plugins (see README.md as it currently exists in this repo).

## Skills section — add new entry

Add a new entry for offdesk, immediately under the existing architect/presentation entries. Follow the format of the others: heading, plugin tag, 1-2 sentence summary, Usage, optional Capabilities or Covers bullet list, Example block.

Suggested heading and tag:

```markdown
### offdesk

*Plugin: obsidian*

Push markdown files from any project into a Syncthing-synced Obsidian vault on phone/tablet for off-desk reading, then pull annotated `>[!ai]` callouts back to the source file. P2P only — no cloud, no bot.

**Usage**: Ask Claude to send a doc to offdesk for review, or to check feedback from your phone.

**Example**:
\`\`\`
положи это в offdesk
посмотри оффдеск фидбэк
\`\`\`
```

## Project Structure section — extend the tree

Extend the existing project-structure tree to include the new plugin subtree:

```text
plugins/
├── architect/
├── presentation/
└── obsidian/
    ├── .claude-plugin/
    │   └── plugin.json
    └── skills/
        └── offdesk/
            ├── SKILL.md
            └── references/
                └── setup.md
```

## Installation section — add obsidian install line

Add the obsidian install line alongside the existing architect and presentation lines:

```text
/plugin install obsidian@dddpaul-claude-skills    # offdesk
```

## Out of scope

- No changes to "Creating New Skills" section (the existing convention still applies to obsidian).
- No changes to the marketplace.json file (TASK-3 owns that).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 README.md Skills section contains a new subheading for offdesk (level matching architect/arch-describe) with the literal text '*Plugin: obsidian*' beneath it
- [ ] #2 README.md Project Structure tree contains a line showing plugins/obsidian/skills/offdesk/ and a line showing references/setup.md under it
- [ ] #3 README.md Installation block contains the literal string '/plugin install obsidian@dddpaul-claude-skills'
- [ ] #4 uv run ruff check . returns exit code 0
- [ ] #5 README.md Skills section's offdesk subsection contains both 'положи это в offdesk' and 'посмотри оффдеск фидбэк' (a RU push trigger and a RU pull trigger matching the SKILL.md frontmatter)
<!-- AC:END -->
