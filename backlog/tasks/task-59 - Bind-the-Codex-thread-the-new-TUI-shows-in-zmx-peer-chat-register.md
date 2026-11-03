---
id: TASK-59
title: Bind the Codex thread the new TUI shows in zmx-peer-chat register
status: To Do
assignee: []
created_date: '2026-11-03T12:50:00Z'
labels:
  - zmx-peer-chat
dependencies: []
priority: medium
ordinal: 59000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

On the box, the `agent` launcher runs `zmx-peer-chat register --role codex ...` before it creates a Codex zmx session, and register labels the session with the thread the new Codex TUI opened (`zpc.thread`, named `zpc-<inc>`). Both Codex peers, zmx-peer-chat's router and agent-chat's `watch-codex`, queue to that label. In source TASK-102 (2026-11-03) a new session came out unpaired or mispaired on every start: four starts in a row. In the mispaired case the label named a thread the TUI did not show, so mail queued to it never reached the screen.

Two causes were observed, with codex-cli 0.163.0 on the box:

1. **A leftover thread is taken for a resumed one.** A Codex TUI that is killed before its first turn leaves its thread loaded in the app-server daemon. Until it is persisted, `thread/read` reports that thread's `createdAt` and `updatedAt` as the moment of the read. `_candidates()` in `register.py` then sees `updated_at >= reg.since and updated_at > old` on every poll and binds it, while the new TUI shows a different thread. The thread/name/set that follows persists the leftover with its real times, and the next leftover (the current TUI's turn-less thread, once killed) repeats the problem. So in that directory it recurs until the daemon restarts. register.log examples from the box:
   - `15:27:20 agent-chat-test-codex: labelled zpc.inc=9f499fc6 ... zpc.thread=<A>`, while the TUI footer showed no `zpc-9f499fc6`
   - `15:32:33 agent-chat-test-codex: labelled zpc.inc=5b02c4d4 ...`; the daemon then had the bound thread (no TUI) plus a second, unnamed thread the TUI showed
2. **The new TUI opens its thread too late.** codex 0.166.0 is out, so a 0.163.0 TUI first shows "Update available ... Skip / Skip until next version", plus "Trust this folder?" in a new directory. Even with both answered by a script at 1.0 s and 1.2 s, the TUI's thread was not in `thread/loaded/list` within the bind window: `15:38:29 agent-chat-test2-codex: no Codex thread opened in <home>/agent-chat-test2 in time; no label set`. It was loaded shortly after. The same message for a real project's Codex session on 2026-11-02 shows it happens to real sessions too.

## Scope

In scope:
- In `register.py`, stop counting a thread whose times only read as "now" as resumed, or started, unless the new TUI actually shows it. The router already has the right test: `tui_shows()` in `router.py` checks the footer for `· zpc-<inc>`. Name the candidate, then confirm the footer shows the name before `zmx set` writes `zpc.thread`. When it does not, either try the next candidate or log why and set no thread label.
- Give the bind enough time for a TUI that opens behind a startup dialog: `register --timeout` defaults to a named constant `BIND_SECONDS = 60` (was 10 s). The bind runs in the background, so the longer window costs the launcher nothing. An explicit shorter `--timeout` still works and stays testable.
- Tests in `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/test_zpc_register.py`, using the fakes in `zpc_fakes.py`.
- A patch bump of the plugin version in both `plugin.json` files, and the README or design doc updated where the bind is described.

Out of scope:
- agent-chat's `watch-codex` (a separate handoff).
- Installing the new version on the box, the source repo's box role, and the live check there: the source repo does those.
- Restarting the user's Codex daemon.
- Answering Codex's update or trust prompts automatically.

## Files

- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/register.py` (exists): `_snapshot`, `_candidates`, `_find_thread`, `bind`
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/router.py` (exists): `tui_shows()`, to reuse rather than copy
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/test_zpc_register.py` (exists), `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/zpc_fakes.py` (exists)
- `plugins/zmx-peer-chat/.claude-plugin/plugin.json`, `plugins/zmx-peer-chat/.codex-plugin/plugin.json` (exist): version 0.1.0
- `plugins/zmx-peer-chat/README.md`, `design/zmx-peer-chat.md` (exist): the bind description

## Source

Source: <source repo>@9a8593b55dc9
Source evidence (read-only context, do NOT modify): <source repo>/backlog/tasks/task-102 - Deliver-agent-chat-room-messages-to-Codex-with-codex-queue.md (the notes 'Starting the test Codex session' and 'Findings for follow-up')

## Before starting (destination Claude validation checklist)

Before running this task, verify:
1. All `(exists)` file paths in the Files section still exist in this repo.
2. Each AC is objectively pass/fail (a grep, test invocation, build command, or visible behavior - not "works correctly").
3. All dependencies in the task's frontmatter are status=Done.
4. Out-of-scope items are not accidentally pulled in by ambiguous AC.

If anything is unclear or any check fails: STOP and ask the user. Do NOT start work blindly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test in test_zpc_register.py where the fake daemon keeps a turn-less leftover thread loaded in the session directory, its createdAt and updatedAt reading as the time of each thread/read, ends with zpc.thread naming the new TUI's thread, not the leftover
- [ ] #2 A test where the only candidate thread's zpc-<inc> name never shows in the fake session footer (zmx history) ends with no zpc.thread label and a register.log line saying why
- [ ] #3 A test where the new TUI's thread first appears in thread/loaded/list 15 s after the session does is bound with the default window, and register's --timeout defaults to a named constant BIND_SECONDS = 60; a test with a shorter explicit timeout still ends with no label
- [ ] #4 register reuses router.tui_shows (or one shared helper), so the footer rule exists in one place: grep -n 'def tui_shows' finds exactly one definition under plugins/zmx-peer-chat
- [ ] #5 The version in plugins/zmx-peer-chat/.claude-plugin/plugin.json and .codex-plugin/plugin.json is bumped to 0.1.1, and plugins/zmx-peer-chat/README.md or design/zmx-peer-chat.md describes the new bind rule
- [ ] #6 uv run pytest and uv run ruff check . pass
<!-- AC:END -->
