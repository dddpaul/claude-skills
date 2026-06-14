---
id: TASK-4
title: Document offdesk skill and obsidian plugin in README
status: Done
assignee: []
created_date: '2026-06-14 06:13'
updated_date: '2026-06-14 07:18'
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
- [x] #1 README.md Skills section contains a new subheading for offdesk (level matching architect/arch-describe) with the literal text '*Plugin: obsidian*' beneath it
- [x] #2 README.md Project Structure tree contains a line showing plugins/obsidian/skills/offdesk/ and a line showing references/setup.md under it
- [x] #3 README.md Installation block contains the literal string '/plugin install obsidian@dddpaul-claude-skills'
- [x] #4 uv run ruff check . returns exit code 0
- [x] #5 README.md Skills section's offdesk subsection contains both 'положи это в offdesk' and 'посмотри оффдеск фидбэк' (a RU push trigger and a RU pull trigger matching the SKILL.md frontmatter)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: 1) Add offdesk skill entry in Skills section (after pptx-arch-style); use the suggested heading, plugin tag, summary, Usage, Example with RU triggers. 2) Extend Project Structure tree with obsidian plugin subtree showing skills/offdesk/ and references/setup.md. 3) Add obsidian install line to Installation. 4) Verify ruff and AC literal strings match.

Commit: `cc8c72d` - task-4: document offdesk skill and obsidian plugin in README

Implementation: README.md updated with offdesk Skills section entry, Project Structure tree extended with obsidian plugin subtree, and obsidian install line added to Installation block. Tree rebalanced so architect/presentation use ├── and obsidian uses └── as the last sibling. All 5 AC verified literally with grep. uv run ruff check . passes. Task-reviewer agent APPROVED.
<!-- SECTION:NOTES:END -->
