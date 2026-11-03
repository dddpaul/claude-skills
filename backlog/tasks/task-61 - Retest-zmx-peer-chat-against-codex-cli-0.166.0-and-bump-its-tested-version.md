---
id: TASK-61
title: Retest zmx-peer-chat against codex-cli 0.166.0 and bump its tested version
status: To Do
assignee: []
created_date: '2026-11-03T12:53:00Z'
updated_date: '2026-11-03T13:05:00Z'
labels:
  - zmx-peer-chat
dependencies:
  - TASK-59
priority: medium
ordinal: 61000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

zmx-peer-chat drives an undocumented codex-cli API (the app-server daemon's JSON-RPC over the `codex app-server proxy`), so it fails closed. `zmx-peer-chat daemon check` exits 1 when `codex --version` is not `TESTED_CODEX_CLI` (`"0.163.0"` in `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/common.py`). The source repo's box role runs that check at the end of every codex concern, and a non-zero exit fails the play.

On 2026-11-03 the user moved the box to codex-cli 0.166.0, the Mac's version (source TASK-110). The box's app-server daemon had already updated itself to 0.166.0 (`~/.codex/packages/app-server-daemon/releases/0.166.0-x86_64-unknown-linux-musl`). zmx-peer-chat's register, thread naming and `codex queue` worked against that 0.166.0 daemon from a 0.163.0 CLI that same day (TASK-102 notes). Until zmx-peer-chat is retested with codex-cli 0.166.0 and released, the box's runs skip the check (`--skip-tags zmx-peer-chat-check`).

## Scope

In scope:
- Retest the daemon client against codex-cli 0.166.0 on the box. Re-run the probes design/zmx-peer-chat-spike.md and design/zmx-peer-chat.md rely on: thread/loaded/list, thread/read (cwd, status, createdAt, updatedAt, name), thread/name/set and the footer showing `zpc-<inc>`, `codex queue` to an idle and a busy TUI, and the codex plugin listing the role parses. Record each command and its output.
- Set `TESTED_CODEX_CLI = "0.166.0"`, update the tests that pin it, and record the retest in the design doc.
- A patch bump of the plugin version in both `plugin.json` files, one above whatever version is current when this merges (TASK-59 may bump it first).

Out of scope:
- The register bind fix (TASK-59) and agent-chat's watch-codex (TASK-60).
- The source repo's box role, and installing the release on the box: the source repo does that, then drops its --skip-tags zmx-peer-chat-check.
- Restarting the user's Codex daemon.
- Starting Codex sessions on the box without the user's explicit OK, which spends quota. Never type into, queue to, register or kill the user's own zmx sessions; use test sessions only.

## Files

- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/common.py` (exists): `TESTED_CODEX_CLI`
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/daemon.py` (exists): the RPC calls the retest exercises
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/` (exists): tests that pin the tested version
- `design/zmx-peer-chat.md`, `design/zmx-peer-chat-spike.md` (exist): where the retest is recorded
- `plugins/zmx-peer-chat/.claude-plugin/plugin.json`, `plugins/zmx-peer-chat/.codex-plugin/plugin.json` (exist): version

## Source

Source: <source repo>@9a8593b55dc9
Source context (read-only, do NOT modify): <source repo>/backlog/tasks/task-110 (the codex pin bump), and <source repo>/ansible/roles/<box role>/README.md, section 'The daemon check, and a codex bump'

## Before starting (destination Claude validation checklist)

Before running this task, verify:
1. All `(exists)` file paths in the Files section still exist in this repo.
2. Each AC is objectively pass/fail (a grep, test invocation, build command, or visible behavior - not "works correctly").
3. All dependencies in the task's frontmatter are status=Done.
4. Out-of-scope items are not accidentally pulled in by ambiguous AC.
5. The box runs codex-cli 0.166.0 (`codex --version` there), that is, source TASK-110 is deployed. The live retest needs it.

If anything is unclear or any check fails: STOP and ask the user. Do NOT start work blindly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 grep -n 'TESTED_CODEX_CLI = "0.166.0"' plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/common.py matches
- [ ] #2 zmx-peer-chat daemon check on the box with codex-cli 0.166.0 exits 0 and prints 'codex-cli 0.166.0 (tested with codex-cli 0.166.0); daemon ok, ...', recorded in the task notes
- [ ] #3 The retest's probe commands and outputs (thread/loaded/list, thread/read, thread/name/set with the footer showing zpc-<inc>, codex queue to an idle and a busy test TUI, the codex plugin listing) are recorded in design/zmx-peer-chat.md or design/zmx-peer-chat-spike.md
- [ ] #4 Every live probe used test Codex sessions started with the user's OK, recorded with their names and zmx ls before and after
- [ ] #5 The version in plugins/zmx-peer-chat/.claude-plugin/plugin.json and .codex-plugin/plugin.json is one patch above the version current at merge
- [ ] #6 uv run pytest and uv run ruff check . pass
<!-- AC:END -->
