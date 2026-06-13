---
id: TASK-1
title: Convert repo into Claude Code plugin marketplace
status: Done
assignee: []
created_date: '2026-06-13 18:16'
updated_date: '2026-06-13 18:27'
labels:
  - 'feature:plugin-marketplace-distribution'
dependencies: []
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Repackage the flat skill layout under a Claude Code plugin marketplace shape so teammates can install via `/plugin marketplace add` + `/plugin install`. Full design rationale and option analysis: `design/plugin-marketplace-distribution-brainstorm.md`. This task covers the file migration and three manifest files only; README/CLAUDE.md updates live in a follow-on task.

**Marketplace manifest** — write to `.claude-plugin/marketplace.json`:

```json
{
  "name": "dddpaul-claude-skills",
  "owner": { "name": "Pavel Derendyaev" },
  "plugins": [
    {
      "name": "architect",
      "source": "./plugins/architect",
      "description": "Architecture documentation and diagramming skills — describe IT systems with ASCII diagrams (arch-describe) and generate draw.io XML diagrams (arch-draw)."
    },
    {
      "name": "presentation",
      "source": "./plugins/presentation",
      "description": "Presentation style guides for the pptx skill — corporate core-style and architecture-committee arch-style."
    }
  ]
}
```

**Plugin manifests** — write to `plugins/architect/.claude-plugin/plugin.json` and `plugins/presentation/.claude-plugin/plugin.json`. Same shape, substitute `name` and `description`:

```json
{
  "name": "architect",
  "description": "Architecture documentation and diagramming skills",
  "version": "0.1.0",
  "author": { "name": "Pavel Derendyaev" },
  "homepage": "https://github.com/dddpaul/claude-skills",
  "repository": "https://github.com/dddpaul/claude-skills",
  "license": "Apache-2.0"
}
```

For `presentation`: `name": "presentation`, `description": "Presentation style guides for architectural decks`. Everything else identical.

**Migration commands** (use git mv to preserve blame):

```bash
mkdir -p .claude-plugin
mkdir -p plugins/architect/.claude-plugin    plugins/architect/skills
mkdir -p plugins/presentation/.claude-plugin plugins/presentation/skills

git mv arch-describe    plugins/architect/skills/arch-describe
git mv arch-draw        plugins/architect/skills/arch-draw
git mv pptx-core-style  plugins/presentation/skills/pptx-core-style
git mv pptx-arch-style  plugins/presentation/skills/pptx-arch-style
```

No internal path rewrites required — every relative link inside a `SKILL.md` (e.g., `arch-draw/SKILL.md` → `references/cheatsheet.md`) stays relative to its skill directory and survives the move.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 .claude-plugin/marketplace.json exists, parses as valid JSON, and has fields name="dddpaul-claude-skills" and a plugins array of length 2 listing architect and presentation
- [x] #2 plugins/architect/.claude-plugin/plugin.json exists, parses as valid JSON, has version="0.1.0", name="architect", license="Apache-2.0", author.name="Pavel Derendyaev", and both homepage and repository equal to https://github.com/dddpaul/claude-skills
- [x] #3 plugins/presentation/.claude-plugin/plugin.json exists with the same field set as architect but name="presentation"
- [x] #4 plugins/architect/skills/arch-describe/SKILL.md and plugins/architect/skills/arch-draw/SKILL.md both exist and start with a --- frontmatter block containing a name: field matching the directory name
- [x] #5 plugins/presentation/skills/pptx-core-style/SKILL.md and plugins/presentation/skills/pptx-arch-style/SKILL.md both exist and start with a --- frontmatter block containing a name: field matching the directory name
- [x] #6 plugins/architect/skills/arch-draw/references/ contains cheatsheet.md and agent-prompt.md; plugins/architect/skills/arch-describe/references/ contains architectures.md
- [x] #7 Root-level directories arch-describe, arch-draw, pptx-core-style, pptx-arch-style no longer exist (verified by ls -d arch-describe arch-draw pptx-core-style pptx-arch-style returning errors for all four)
- [x] #8 uv run ruff check . returns exit code 0
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: 1) Create directory structure for .claude-plugin and plugins/{architect,presentation}/{skills,.claude-plugin}; 2) git mv four skill directories to their new homes; 3) Write three manifest files (marketplace + 2 plugin.json); 4) Verify AC with ls/jq/ruff; 5) Spawn task-reviewer agent.

Commit: `7489069` - task-1: convert repo into Claude Code plugin marketplace

Reviewed by task-reviewer agent: APPROVED. All 8 AC pass. Migration complete with no internal-path rewrites required.
<!-- SECTION:NOTES:END -->
