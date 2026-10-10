---
id: TASK-48
title: Merge host .claude/settings.local.json with ralph 0.14.2 template
status: To Do
assignee: []
created_date: '2026-10-10 06:20'
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
- [ ] #1 On the host, bash <plugin>/skills/ralph-init/scripts/managed-file-drift.sh check . exits 0
- [ ] #2 Step 3.10 pptx check prints PASS on the host file
- [ ] #3 None of the three dead $HOME/.claude/skills/ralph-* helper rules remain in the host file
<!-- AC:END -->
