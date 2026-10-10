---
id: TASK-48
title: Merge host .claude/settings.local.json with ralph 0.14.2 template
status: In Progress
assignee: []
created_date: '2026-10-10 06:20'
updated_date: '2026-10-10 08:30'
labels: []
dependencies: []
ordinal: 48000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Follow-up of TASK-47. The upgrade ran inside the devcontainer, where the host .claude is mounted read-only at /workspace-host-claude, so the untracked host .claude/settings.local.json was not merged. Run on the HOST (not in the container): the ralph-init U4 settings.local.json step (template overwrite + merge of existing allow rules + Step 3.7b pptx rules + dead helper rule strip), then the Step 3.10 check. Currently missing template rules: Bash(git log:*), Bash(git status:*), Bash(git diff:*), Bash(git show:*), Bash(git rev-parse:*), Bash(git ls-files:*). Dead rules to strip: the three Bash(bash $HOME/.claude/skills/ralph-(run|status)/scripts/...) rules. Also: after merging TASK-47, recreate the devcontainer (Dev Containers: Rebuild Container) so the new mounts apply.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 On the host, bash <plugin>/skills/ralph-init/scripts/managed-file-drift.sh check . exits 0
- [x] #2 Step 3.10 pptx check prints PASS on the host file
- [x] #3 None of the three dead $HOME/.claude/skills/ralph-* helper rules remain in the host file
- [x] #4 The upgrade's Dockerfile patches (early claude-code arg, floating uv copy, stale runtime copy, broad sudoers chown) were each offered with a diff and applied or declined as the user answered; the four check scripts exit 0 for every applied patch
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: run /ralph:ralph-init upgrade on the host on branch task-48-ralph-upgrade. U2 status table, apply the settings.local.json step (template + merged allow rules + pptx rules, dead helper rules stripped), offer each Dockerfile patch with its diff and apply on the user's yes, then Step 3.10, drift check, ruff and pytest.

Applied on the host with the user's per-change approval: settings.local.json (6 template git rules added; dead rules removed: Bash(bash $HOME/.claude/skills/ralph-run/scripts/preflight.sh:*), Bash(bash $HOME/.claude/skills/ralph-run/scripts/wait-heartbeat.sh:*), Bash(bash $HOME/.claude/skills/ralph-status/scripts/utc-to-moscow.sh:*); pptx rules kept). Dockerfile: version pin patched (default-less ARG CLAUDE_CODE_VERSION next to the guarded npm RUN + label, which also clears the early-ARG check), uv pin patched (global ARG UV_VERSION + uv-bin stage + guarded uv block with uv python install 3.14), stale python:3.14 runtime copy replaced with the current python fragment, sudoers narrowed to chown node:node /workspace/.venv with visudo -cf. All four Dockerfile checks exit 0; managed-file-drift.sh check . exits 0; Step 3.10 PASS. Also rebuilt the host .venv (the TASK-47 container had repointed it at /usr/bin/python3 3.11). ruff clean; pytest 243 passed, 1 failed (test_helper_renders_canonical_decision_tree, same as master).
<!-- SECTION:NOTES:END -->
