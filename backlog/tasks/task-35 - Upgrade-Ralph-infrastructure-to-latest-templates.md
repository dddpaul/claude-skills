---
id: TASK-35
title: Upgrade Ralph infrastructure to latest templates
status: In Progress
assignee: []
created_date: '2026-06-23 06:07'
updated_date: '2026-06-23 06:08'
labels: []
dependencies: []
priority: medium
ordinal: 35000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Periodic refresh of Ralph infrastructure files from the latest user-global `ralph-init` templates. Catches updates to ralph.sh, CLAUDE.md generic block, git hooks (post-commit, commit-msg, pre-commit), .devcontainer files, .claude/settings.json, .claude/hooks/*, .claude/settings.local.json, .claude/brainstorm-rules.md.

## Scope

In scope:
- Run `/ralph-init upgrade` and apply all updates it proposes (or skip with explicit reason per file).
- Verify the post-upgrade U4 narrow-rule merge for `settings.local.json` (6 rules per Step 3.7b for all projects; if pptx-style helpers are present, 2 more per Step 3.7c).
- Smoke-check build / lint / tests still pass after the refresh.

Out of scope:
- Editing CLAUDE.md Project-Specific block (preserved by U4 special-merge).
- Editing .claude/brainstorm-rules.md Project additions block (preserved by U4 section-aware merge).
- Editing any task files, design docs, or skill SKILL.md files.
- Bumping any plugin version (infrastructure refresh, no plugin code touched).

## Files

- `ralph.sh` (exists) — refresh from `templates/root/ralph.sh`
- `CLAUDE.md` (exists) — refresh generic block from `templates/root/CLAUDE.md`; preserve Project-Specific
- `.git/hooks/post-commit` (exists) — refresh
- `.git/hooks/commit-msg` (exists) — refresh
- `.git/hooks/pre-commit` (exists) — refresh
- `.claude/settings.json` (exists) — refresh
- `.claude/hooks/*-guard.sh`, `task-validator.sh` (exist) — refresh
- `.claude/settings.local.json` (exists) — refresh + re-merge narrow rules (Step 3.7b + 3.7c gated on project type)
- `.claude/brainstorm-rules.md` (exists) — section-aware merge
- `.devcontainer/Dockerfile` (exists) — skipped per template (assembled, not diffable)
- `.devcontainer/devcontainer.json` (exists) — refresh
- `.devcontainer/init-firewall.sh` (exists) — refresh
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Run /ralph-init upgrade on this branch; flow completes successfully with batch summary printed
- [ ] #2 All outdated files updated (or explicit per-file skip with reason logged in task notes); U5 summary shows no surprise 'skipped' entries beyond Dockerfile/.gitignore
- [ ] #3 .claude/settings.local.json contains all 6 narrow rules per Step 3.7b verification block (3 absolute-path + 3 $HOME-form for preflight.sh / wait-heartbeat.sh / utc-to-moscow.sh)
- [ ] #4 CLAUDE.md Project-Specific block preserved byte-for-byte; .claude/brainstorm-rules.md content from '## Project additions' onward preserved byte-for-byte (verify via diff against pre-upgrade snapshot)
- [ ] #5 uv run pytest exits 0; uv run ruff check . exits 0 after the refresh
- [ ] #6 task-reviewer agent on git diff master..HEAD returns APPROVED before merge
<!-- AC:END -->
