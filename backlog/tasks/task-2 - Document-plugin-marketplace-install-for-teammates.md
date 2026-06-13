---
id: TASK-2
title: Document plugin marketplace install for teammates
status: Done
assignee: []
created_date: '2026-06-13 18:18'
updated_date: '2026-06-13 18:31'
labels:
  - 'feature:plugin-marketplace-distribution'
dependencies:
  - TASK-1
priority: medium
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Once TASK-1 has migrated the repo to the marketplace shape, rewrite the user-facing docs so teammates can discover the install flow and so future contributors know the layout convention. Full design rationale: `design/plugin-marketplace-distribution-brainstorm.md` (Section 5).

**README.md "Installation" section** — replace the existing `claude config add skills /path/to/claude-skills` block and settings.json snippet with:

```markdown
## Installation

These skills are distributed as Claude Code plugins via a marketplace.

### One-time setup
\`\`\`
/plugin marketplace add https://github.com/dddpaul/claude-skills
\`\`\`

### Install the plugins you want
\`\`\`
/plugin install architect@dddpaul-claude-skills      # arch-describe + arch-draw
/plugin install presentation@dddpaul-claude-skills   # pptx-core-style + pptx-arch-style
\`\`\`

### Update later
\`\`\`
/plugin marketplace update dddpaul-claude-skills
\`\`\`
```

**README.md "Project Structure" tree** — redraw to show `plugins/architect/skills/` and `plugins/presentation/skills/` (see brainstorm Section 1 for the exact tree).

**README.md per-skill summaries** — add a one-line tag (e.g., `*Plugin: architect*`) directly under each skill's heading.

**README.md "Creating New Skills" section** — change the directory template to:

```
plugins/<domain>/skills/<skill-name>/
├── SKILL.md           # Required: frontmatter + body
└── references/        # Optional
    └── *.md
```

And add a sentence: *"If the skill belongs to a new domain (e.g., `obsidian`), create a new `plugins/<domain>/` with its own `.claude-plugin/plugin.json` and register it in the root `.claude-plugin/marketplace.json`."*

**CLAUDE.md "Project-Specific" section** — add one bullet:

```markdown
- **Plugin layout:** skills live under `plugins/<domain>/skills/<name>/` — not at repo root. The repo is itself a Claude Code plugin marketplace (`.claude-plugin/marketplace.json`). When adding or modifying a skill, also bump the `version` in the owning plugin's `plugin.json` per SemVer: patch for content tweaks, minor for new skills or broadened triggers, major for renames/removals or breaking trigger narrowing.
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 README.md Installation section contains the literal string "/plugin marketplace add https://github.com/dddpaul/claude-skills" and "/plugin install architect@dddpaul-claude-skills"
- [x] #2 grep -F "claude config add skills" README.md returns no matches and grep -F "\"skills\":" README.md returns no matches (the obsolete settings.json snippet has been removed)
- [x] #3 README.md Project Structure section shows plugins/architect/skills/ and plugins/presentation/skills/ directory tree (not the flat arch-describe/ at root layout)
- [x] #4 Under each of the four skill subheadings (arch-describe, arch-draw, pptx-core-style, pptx-arch-style) in README.md, a one-line plugin tag like "Plugin: architect" or "Plugin: presentation" is present
- [x] #5 README.md Creating New Skills section shows the plugins/<domain>/skills/<skill-name>/ directory template and contains a sentence instructing readers to register new domains in .claude-plugin/marketplace.json
- [x] #6 CLAUDE.md Project-Specific section contains a bullet that mentions both the plugins/<domain>/skills/<name>/ layout and the SemVer bump rule (patch/minor/major) for the owning plugin.json version field
- [x] #7 uv run ruff check . returns exit code 0 (documentation changes do not break linting)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: Rewrite README.md Installation, Project Structure, per-skill summary tags, and Creating New Skills sections; add CLAUDE.md Project-Specific bullet about plugin layout and SemVer bump. Then run ruff check to verify AC #7.

Commit: `c1d1998` - task-2: rewrite installation docs and add plugin layout note

Implemented: README Installation/Project Structure/per-skill plugin tags/Creating New Skills sections rewritten for plugin marketplace; CLAUDE.md gained Plugin layout + SemVer bump bullet. All 7 AC verified. Task-reviewer APPROVED.
<!-- SECTION:NOTES:END -->
