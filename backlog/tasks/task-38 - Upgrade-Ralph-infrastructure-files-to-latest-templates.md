---
id: TASK-38
title: Upgrade Ralph infrastructure files to latest templates
status: Done
assignee: []
created_date: '2026-06-28 15:48'
updated_date: '2026-06-28 16:18'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Commit: `08b8322` - task-38: upgrade ralph.sh shim to Python-only orchestrator

Ran /ralph-init upgrade on task branch. Only two managed files were outdated: ralph.sh (removed RALPH_IMPL bash-fallback dispatch; now Python-only shim execing ralph_orchestrator.py) and .claude/settings.local.json (gitignored, local-only — re-merged uv-run + utc-to-moscow narrow rules and pptx helper rules; preserved 3 customs xxd/awk-Project-additions/WebFetch-github; dropped 3 superseded narrow rules usage-check/preflight/wait-heartbeat now covered by uv run). All other managed files already current; CLAUDE.md ##Project-Specific and brainstorm-rules ##Project additions preserved untouched. Gates: ruff clean, pytest 97/97. task-reviewer APPROVED.
<!-- SECTION:NOTES:END -->
