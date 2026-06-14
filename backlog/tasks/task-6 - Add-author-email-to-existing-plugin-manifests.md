---
id: TASK-6
title: Add author email to existing plugin manifests
status: Done
assignee: []
created_date: '2026-06-14 14:58'
updated_date: '2026-06-14 15:34'
labels:
  - chore
dependencies: []
priority: low
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add `"email": "dddpaul@gmail.com"` to the `author` block of every existing plugin manifest, and bump each plugin's version per CLAUDE.md (patch for content tweaks).

## Files to change

- `plugins/architect/.claude-plugin/plugin.json` — author becomes `{ "name": "Pavel Derendyaev", "email": "dddpaul@gmail.com" }`; bump version 0.1.0 → 0.1.1.
- `plugins/presentation/.claude-plugin/plugin.json` — same author edit; bump version 0.1.0 → 0.1.1.
- `plugins/obsidian/.claude-plugin/plugin.json` — same author edit; bump version 0.2.0 → 0.2.1.

## Out of scope

- No changes to `.claude-plugin/marketplace.json` (it does not carry per-plugin author/version).
- No changes to skill files or README.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 plugins/architect/.claude-plugin/plugin.json author block contains "email": "dddpaul@gmail.com" and version is "0.1.1"
- [x] #2 plugins/presentation/.claude-plugin/plugin.json author block contains "email": "dddpaul@gmail.com" and version is "0.1.1"
- [x] #3 plugins/obsidian/.claude-plugin/plugin.json author block contains "email": "dddpaul@gmail.com" and version is "0.2.1"
- [x] #4 All three plugin.json files remain valid JSON (python -m json.tool succeeds)
- [x] #5 uv run ruff check . returns exit code 0
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: edit each plugin.json to add email to author block and bump patch version per spec. Validate JSON with python -m json.tool. Run ruff.

Commit: `859454c` - task-6: add author email and bump versions in plugin manifests

Implemented: added email to author block in architect, presentation, obsidian plugin.json; bumped versions 0.1.0->0.1.1, 0.1.0->0.1.1, 0.2.0->0.2.1. JSON valid, ruff clean. task-reviewer: APPROVED.
<!-- SECTION:NOTES:END -->
