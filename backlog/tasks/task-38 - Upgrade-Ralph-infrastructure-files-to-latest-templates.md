---
id: TASK-38
title: Upgrade Ralph infrastructure files to latest templates
status: In Progress
assignee: []
created_date: '2026-06-28 15:48'
updated_date: '2026-06-28 16:13'
labels: []
dependencies: []
priority: medium
ordinal: 38000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Periodic maintenance: sync this project's Ralph infrastructure files (ralph.sh, CLAUDE.md generic section, git hooks, .claude/ hooks + settings, brainstorm-rules) against the latest user-global ralph-init templates so the project picks up template improvements without losing project-specific customizations.

## Scope

In scope:
- Run the ralph-init upgrade flow (U1-U5) on a task branch.
- Apply approved template updates to outdated managed files.
- Preserve project-specific blocks: CLAUDE.md ## Project-Specific section, brainstorm-rules.md ## Project additions section, custom permissions in settings.local.json.

Out of scope:
- Any feature/code changes to plugins.
- Editing the project-specific CLAUDE.md block or the brainstorm-rules ## Project additions block.

## Files

- ralph.sh (exists) - thin shim, overwrite from template if outdated
- CLAUDE.md (exists) - generic section above ## Project-Specific only
- .git/hooks/* (exists) - post-commit, commit-msg, pre-commit
- .claude/settings.json (exists) - hook registration
- .claude/hooks/* (exists) - guard scripts
- .claude/settings.local.json (exists) - permissions, narrow-rule merge preserved
- .claude/brainstorm-rules.md (exists) - pre-heading region only
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 ralph-init upgrade flow completed; all outdated managed files updated to latest template versions
- [x] #2 CLAUDE.md ## Project-Specific block preserved byte-for-byte after upgrade
- [x] #3 .claude/brainstorm-rules.md ## Project additions block (publish doc-parity rule) preserved byte-for-byte after upgrade
- [x] #4 settings.local.json narrow rules verification prints PASS (no missing rules)
<!-- AC:END -->
