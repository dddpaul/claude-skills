---
id: TASK-52
title: Upgrade Ralph infrastructure to ralph plugin 0.14.7 templates
status: To Do
assignee: []
created_date: '2026-10-20 11:20'
labels: []
dependencies: []
priority: medium
ordinal: 52000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Periodic maintenance: the installed ralph plugin is now 0.14.7, and `/ralph-run` preflight reports five managed files behind its templates: `CLAUDE.md` (generic section), `.git/hooks/post-commit`, `.claude/settings.json`, `.claude/hooks/task-validator.sh` and `.devcontainer/devcontainer.json`. Sync them with the templates without losing this project's customizations.

## Scope

In scope:
- Run the ralph-init upgrade flow (U1-U5) from plugin 0.14.7 on this task branch.
- Apply the template updates to every outdated or missing managed file.
- Apply any confirm-only `.devcontainer/Dockerfile` patch the flow offers on an explicit yes only (TASK-48 already applied all four, so none is expected).
- Preserve the project-specific blocks: `CLAUDE.md` from `## Project-Specific` down, `.claude/brainstorm-rules.md` from `## Project additions` down, the custom permissions and pptx helper rules in `.claude/settings.local.json`, and the project's own `runArgs` in `devcontainer.json`.

Out of scope:
- Feature or code changes to the plugins.
- Editing the `CLAUDE.md` project block or the brainstorm-rules `## Project additions` block.
- Changing `CLAUDE_CODE_VERSION` (2.1.283) or `UV_VERSION` (0.12.19) in `devcontainer.json`; the 0.14.7 template pins the same values.

## Files

- `CLAUDE.md` (exists): generic section above `## Project-Specific` only.
- `.git/hooks/post-commit` (exists).
- `.claude/settings.json` (exists): hook registration; hook commands move to the `"$CLAUDE_PROJECT_DIR"/.claude/hooks/<name>.sh` form.
- `.claude/hooks/task-validator.sh` (exists).
- `.devcontainer/devcontainer.json` (exists): gains `--add-host=host.docker.internal:host-gateway` in `runArgs`; the container must be recreated afterwards (`/ralph-run rebuild=true`).
- `.devcontainer/Dockerfile` (exists): checked only, patched in place only on confirmation.

After the merge, the next Ralph launch needs `rebuild=true`, because `runArgs` apply only when the container is created.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The ralph-init upgrade flow (U1-U5) from ralph plugin 0.14.7 completed, and bash ~/.claude/plugins/cache/dddpaul-ralph/ralph/0.14.7/skills/ralph-init/scripts/managed-file-drift.sh check . exits 0 or names only files the user skipped
- [ ] #2 CLAUDE.md from ## Project-Specific to EOF is byte-for-byte unchanged (git diff master..HEAD shows no change in that region)
- [ ] #3 .claude/brainstorm-rules.md from ## Project additions to EOF is byte-for-byte unchanged
- [ ] #4 The Step 3.10 pptx check prints PASS, and the U5 summary lists every removed dead helper rule or says no dead helper rules were found
- [ ] #5 early-claude-arg.sh, floating-uv-copy.sh, stale-runtime-copy.sh and broad-sudoers-chown.sh check .devcontainer/Dockerfile each exit 0, and .devcontainer/devcontainer.json still pins CLAUDE_CODE_VERSION 2.1.283 and UV_VERSION 0.12.19
- [ ] #6 uv run ruff check . passes, and uv run pytest has no failures other than test_helper_renders_canonical_decision_tree, which already fails on master
<!-- AC:END -->
