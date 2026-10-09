---
id: TASK-47
title: Upgrade Ralph infrastructure to ralph plugin 0.14.2 templates
status: To Do
assignee: []
created_date: '2026-10-09 12:05'
labels: []
dependencies: []
priority: medium
ordinal: 47000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Periodic maintenance: sync this project's Ralph infrastructure files with the templates shipped in the installed
ralph plugin (0.14.2), so the project picks up template improvements without losing its own customizations.

## Scope

In scope:
- Run the ralph-init upgrade flow (U1-U5) on this task branch.
- Apply approved template updates to outdated and missing managed files, refine.sh and
  .devcontainer/container-settings.local.json included.
- Apply the confirm-only .devcontainer/Dockerfile patches the flow offers, on an explicit yes only.
- Preserve the project-specific blocks: CLAUDE.md from ## Project-Specific down, brainstorm-rules.md from
  ## Project additions down, custom permissions and the pptx helper rules in settings.local.json, and the project's
  own runArgs in devcontainer.json.

Out of scope:
- Feature or code changes to the plugins.
- Editing the CLAUDE.md project block or the brainstorm-rules ## Project additions block.

## Files

- ralph.sh (exists): thin shim, overwritten from the template if outdated.
- refine.sh (to-create): refine-loop shim, created from the template.
- CLAUDE.md (exists): generic section above ## Project-Specific only.
- .git/hooks/post-commit, commit-msg, pre-commit (exist).
- .claude/settings.json (exists): hook registration.
- .claude/hooks/*.sh (exist; filename-length-guard.sh may be missing).
- .claude/settings.local.json (exists): permissions; pptx helper rules merged back (Mixed project).
- .claude/brainstorm-rules.md (exists): pre-heading region only.
- .devcontainer/devcontainer.json, init-firewall.sh (exist); .devcontainer/container-settings.local.json
  (to-create); .devcontainer/Dockerfile (exists, patched in place only on confirmation).
- .gitignore (exists): append-only.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ralph-init upgrade flow (U1-U5) completed; every outdated or missing managed file the user approved matches the 0.14.2 template, and managed-file-drift.sh check . exits 0 or names only files the user skipped
- [ ] #2 CLAUDE.md from ## Project-Specific to EOF is byte-for-byte unchanged (git diff master shows no change in that region)
- [ ] #3 .claude/brainstorm-rules.md from ## Project additions to EOF is byte-for-byte unchanged
- [ ] #4 settings.local.json keeps the pptx helper rules (Step 3.10 verification prints PASS) and the U5 summary lists any removed dead helper rules
- [ ] #5 uv run ruff check . passes, and uv run pytest has no failures other than test_helper_renders_canonical_decision_tree, which already fails on master
<!-- AC:END -->
