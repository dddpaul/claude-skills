---
id: TASK-61
title: Retest zmx-peer-chat against codex-cli 0.166.0 and bump its tested version
status: In Progress
assignee: []
created_date: '2026-11-03T12:53:00Z'
updated_date: '2026-11-03T15:57:00Z'
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
- [x] #1 grep -n 'TESTED_CODEX_CLI = "0.166.0"' plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/common.py matches
- [x] #2 zmx-peer-chat daemon check on the box with codex-cli 0.166.0 exits 0 and prints 'codex-cli 0.166.0 (tested with codex-cli 0.166.0); daemon ok, ...', recorded in the task notes
- [x] #3 The retest's probe commands and outputs (thread/loaded/list, thread/read, thread/name/set with the footer showing zpc-<inc>, codex queue to an idle and a busy test TUI, the codex plugin listing) are recorded in design/zmx-peer-chat.md or design/zmx-peer-chat-spike.md
- [x] #4 Every live probe used test Codex sessions started with the user's OK, recorded with their names and zmx ls before and after
- [x] #5 The version in plugins/zmx-peer-chat/.claude-plugin/plugin.json and .codex-plugin/plugin.json is one patch above the version current at merge
- [x] #6 uv run pytest and uv run ruff check . pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: interactive (Ralph's container has no ssh to the box). 1) TESTED_CODEX_CLI = "0.166.0" in zpc/common.py; tests pin via the constant. 2) Copy the branch's plugins/zmx-peer-chat to a scratch dir on the box (tar over ssh) and run its daemon check (AC2), a probe script over its Daemon client (thread/loaded/list, thread/read) and codex plugin list. 3) With the user's OK: one throwaway Codex session zpc-rt-codex in ~/zpc-retest/fresh registered by the scratch copy (thread/name/set, footer), plus a shell session zpc-rt-claude labelled as the Claude side; Z send / codex queue to the idle and the busy TUI. 4) Record commands and outputs, with placeholders, in design/zmx-peer-chat.md; zmx ls before and after; kill the zpc-rt-* sessions, keep transcripts. 5) Patch bump to 0.1.4.

AC2 (on the box, the branch's scratch copy, 2026-11-03 17:47): `zmx-peer-chat daemon check` -> 'codex-cli 0.166.0 (tested with codex-cli 0.166.0); daemon ok, 1 loaded thread(s); protocol 1', exit 0.

AC4: live probes started after the user's explicit OK in this session. Test sessions: zpc-rt-codex (Codex TUI, `codex` in ~/zpc-retest/fresh, registered by the scratch copy) and zpc-rt-claude (a plain shell labelled as the Claude side; no Claude started). zmx ls before (17:48:24) and after (17:50:28) listed only the user's two sessions; `zmx ls | grep -c zpc-rt-` after: 0. Three Codex turns (R1 idle, R2a sleep 20, R2b while busy). Both test sessions killed, ~/zpc-retest and the test pair's mailbox dir and lock removed; transcripts and the register.log line kept. The user's sessions were not touched.

Findings: thread/loaded/list, thread/read (same fields) and thread/name/set unchanged; the bind labelled after 9.1 s; 0.166.0 prints a hint line under the footer, still within the six-line footer rule; the footer keeps the thread name during a turn, so send --to codex passes while busy, and the busy turn ran after the running one. codex plugin list columns unchanged.

AC6: uv run ruff check . passes; uv run pytest: 535 passed, 1 failed - the known baseline plugins/presentation/skills/ak-style/scripts/tests/test_decision_tree_helper.py::test_helper_renders_canonical_decision_tree (un-vendored node_modules), unrelated to this task.

Commit: `cd8ce9d` - task-61: test the daemon client with codex-cli 0.166.0 and record the box retest; zmx-peer-chat 0.1.4

Review round 1 (CHANGES REQUESTED, 5): the resume path was not retested. With the user's OK a third test session, zpc-rt-codex2, ran `codex resume <thread-r>` in a recreated ~/zpc-retest/fresh (no turn). zmx ls before (18:41:48) and after (18:43:18): only the user's two sessions; grep -c zpc-rt- after: 0; session killed, scratch dir and lock removed.

Finding: with 0.166.0 the daemon had unloaded the idle test thread; the resume loaded it again and the TUI showed it, but updatedAt stayed at its last turn (17:49:44), createdAt is old, so register named no candidate and logged '18:42:48 zpc-rt-codex2: no Codex thread opened in <home>/zpc-retest/fresh in time; no label set' (code 5). A launcher resume of an unloaded thread starts unpaired with 0.166.0 (fail-closed). The user chose to keep TESTED_CODEX_CLI at 0.166.0 (every daemon call works) and fix the pick in a new task, TASK-63. Also recorded: daemon skills --cwd (exit 0, 33 skills, zmx-peer-chat:zmx-peer-chat listed); the full status output, R2a's command and output and the busy screen's hint line; the daemon unloads an idle thread within 50 minutes (the old note said it kept it until restart).

Commit: `ef98179` - task-61: record the 0.166.0 resume retest, the skill listing and the full transcript lines

Review round 2 (CHANGES REQUESTED, 5): 'For the launcher' item 4 now gives the bind time per version (under 2 s with 0.163.0, about 9 s for the 0.166.0 fresh start); the TASK-63 sentence is worded as a plan. The register.py module docstring's resume claim goes to TASK-63's Files.
<!-- SECTION:NOTES:END -->
