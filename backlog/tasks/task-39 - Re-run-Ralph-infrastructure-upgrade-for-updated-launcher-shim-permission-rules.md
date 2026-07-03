---
id: TASK-39
title: Re-run Ralph infrastructure upgrade for updated launcher-shim permission rules
status: In Progress
assignee: []
created_date: '2026-07-02 20:36'
updated_date: '2026-07-03 05:09'
labels: []
dependencies: []
priority: medium
ordinal: 39000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

The ralph-init skill changed since TASK-38. Its Step 3.7b now expects settings.local.json to carry narrow bash-launcher-shim rules (preflight.sh, wait-heartbeat.sh) because the ralph-run skill invokes 'bash <path>/preflight.sh' and 'bash <path>/wait-heartbeat.sh' directly. TASK-38 (old skill) instead seeded 'Bash(uv run:*)' and dropped the shim rules, so the next /ralph-run would trip permission prompts. Re-run the upgrade flow (U2-U5) to reconcile local infra files with the current templates.

## Scope

In scope:
- Run upgrade U2 status table across all managed files; update every outdated tracked file from its current template.
- Re-run the Step 3.7b narrow-rule merge into settings.local.json (preflight.sh + wait-heartbeat.sh + utc-to-moscow.sh literal-$HOME rules) plus Step 3.7c pptx rules (Mixed project).
- Preserve project-specific customizations (CLAUDE.md ## Project-Specific, brainstorm-rules ## Project additions, custom permissions).

Out of scope:
- Fixing the stale canonical-ralph.sh preflight check in the ralph-init skill itself (that lives in ~/.claude/skills, not this repo).
- Any feature/code changes unrelated to Ralph infra file sync.

## Files

- ralph.sh (tracked) - overwrite from template if outdated
- CLAUDE.md (tracked) - section-aware merge, preserve ## Project-Specific
- .git/hooks/{post-commit,commit-msg,pre-commit} - overwrite if outdated
- .claude/settings.json + .claude/hooks/* - overwrite if outdated
- .claude/settings.local.json (gitignored, local-only) - overwrite + narrow-rule + pptx merge
- .claude/brainstorm-rules.md (tracked) - section-aware merge, preserve ## Project additions
- .devcontainer/{devcontainer.json,init-firewall.sh} - overwrite if outdated
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Upgrade U2 status table built for all managed files; every outdated tracked file is updated to its current template and no file remains outdated at U5 except intentionally skipped ones
- [x] #2 CLAUDE.md ## Project-Specific section (and everything below it) is preserved byte-for-byte through any section-aware merge
- [x] #3 .claude/brainstorm-rules.md ## Project additions heading and all content below it preserved byte-for-byte
- [x] #4 settings.local.json Step 3.10 verification prints PASS for all 3 narrow rules (preflight.sh + wait-heartbeat.sh + utc-to-moscow.sh, literal $HOME) and PASS for both pptx helper rules
<!-- AC:END -->



## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: (1) Build U2 status table — diff each managed file vs its current template (redirect temp files to $TMPDIR, not /tmp, per prior sandbox lesson). (2) For CLAUDE.md + brainstorm-rules, diff only the pre-heading generic region. (3) Apply U4 updates to outdated tracked files; section-aware merge for CLAUDE.md + brainstorm-rules. (4) Overwrite settings.local.json from template, then re-run 3.7b narrow-rule merge (preflight.sh + wait-heartbeat.sh + utc-to-moscow.sh, literal $HOME) + 3.7c pptx merge, preserving existing custom permissions via jq unique. settings.local.json is gitignored — local-only, never committed. (5) Run Step 3.10 verification → expect PASS. (6) task-reviewer on git diff master..HEAD (settings.local.json excluded as gitignored). (7) build/lint/test gates, Done, merge.
<!-- SECTION:NOTES:END -->
