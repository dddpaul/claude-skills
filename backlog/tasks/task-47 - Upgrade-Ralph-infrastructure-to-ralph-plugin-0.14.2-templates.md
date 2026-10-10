---
id: TASK-47
title: Upgrade Ralph infrastructure to ralph plugin 0.14.2 templates
status: Done
assignee: []
created_date: '2026-10-09 12:05'
updated_date: '2026-10-10 06:20'
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
- [x] #1 ralph-init upgrade flow (U1-U5) completed; every outdated or missing managed file the user approved matches the 0.14.2 template, and managed-file-drift.sh check . exits 0 or names only files the user skipped, or .claude/settings.local.json differing only in the container sandbox.enabled=false override (the read-only host copy is merged in TASK-48)
- [x] #2 CLAUDE.md from ## Project-Specific to EOF is byte-for-byte unchanged (git diff master shows no change in that region)
- [x] #3 .claude/brainstorm-rules.md from ## Project additions to EOF is byte-for-byte unchanged
- [x] #4 settings.local.json keeps the pptx helper rules (Step 3.10 verification prints PASS) and the U5 summary lists any removed dead helper rules
- [x] #5 uv run ruff check . passes, and uv run pytest has no failures other than test_helper_renders_canonical_decision_tree, which already fails on master
- [x] #6 npm view @anthropic-ai/claude-code@<pinned CLAUDE_CODE_VERSION> version resolves (exit 0) and the result is recorded in the notes, together with a note that UV_VERSION is inert until the Dockerfile uv pin patch is applied
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: run ralph-init U1-U5 from plugin 0.14.2 on task-47; autonomous run, so batch question answered 'all' (task scope authorizes it) and every confirm-only Dockerfile patch declined (no explicit yes available).

Commit: `3505ab0` - task-47: sync Ralph infrastructure with ralph plugin 0.14.2 templates

Verification: drift check names only .claude/settings.local.json, and the only difference is sandbox.enabled=false. That file is untracked; this container uses the old .claude volume copy (host copy is read-only at /workspace-host-claude) and has no bwrap, so the container copy keeps the sandbox off on purpose (the new container-settings.local.json bind does the same once the container is recreated). The host's own settings.local.json still needs the same merge, run from the host. Step 3.10 PASS. Dead helper rules removed: Bash(bash $HOME/.claude/skills/ralph-run/scripts/preflight.sh:*), Bash(bash $HOME/.claude/skills/ralph-run/scripts/wait-heartbeat.sh:*), Bash(bash $HOME/.claude/skills/ralph-status/scripts/utc-to-moscow.sh:*). Dockerfile patches declined in the unattended run (early claude-code arg, floating uv copy, stale runtime copy, broad sudoers chown), so UV_VERSION in devcontainer.json is inert until the Dockerfile is patched. ruff clean; pytest 243 passed, 1 failed (test_helper_renders_canonical_decision_tree, the failure already on master).

Review round 1 (CHANGES REQUESTED, 2 blocking) addressed: (1) CLAUDE_CODE_VERSION follows the skill rule (project value 'latest' takes the template pin 2.1.283). npm view @anthropic-ai/claude-code@2.1.283 version -> 2.1.283, exit 0. The current image runs 2.1.296 because it was built from 'latest', so a rebuild installs 2.1.283; to stay on a newer CLI, bump the pin per the skill's Bump procedure (npm view @anthropic-ai/claude-code version = 2.1.296 today); this makes devcontainer.json show as drift until the template catches up. After a rebuild, verify on the host with: docker image inspect --format '{{ index .Config.Labels "dev.ralph.claude-code-version" }}' <image>; the label only exists once the Dockerfile version-pin patch is applied, otherwise run claude --version in the container. UV_VERSION=0.12.19 is INERT: the Dockerfile still copies ghcr.io/astral-sh/uv:latest because the uv pin patch was declined in the unattended run. (2) AC#1 reworded to allow the container-only sandbox override; host settings.local.json merge deferred to TASK-48 (host .claude is read-only in this container).

task-reviewer round 2: APPROVED (0 blocking, 1 minor — commit TASK-48 and the task file before merge, done). Host follow-ups: run TASK-48 on the host, then recreate the devcontainer (Dev Containers: Rebuild Container); after merge, run git checkout -- .claude on the host so its .claude matches HEAD (the container wrote .claude through its volume copy).
<!-- SECTION:NOTES:END -->
