---
id: TASK-60
title: Queue agent-chat mail to Codex only when its TUI shows the bound thread
status: To Do
assignee: []
created_date: '2026-11-03T12:50:00Z'
labels:
  - agent-chat
dependencies:
  - TASK-58
priority: medium
ordinal: 60000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

`agent-chat watch-codex` runs on the box as a systemd user unit (source TASK-102). It queues room mail for the host's Codex account with `codex queue --thread <zpc.thread>` to the Codex zmx session that zmx-peer-chat registered for the room's directory. It trusts the `zpc.thread` label as given. zmx-peer-chat's own router does not. Before every `codex queue` it reads the session's screen and requires the footer to end with `· zpc-<inc>` (`tui_shows()` in `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/router.py`). Otherwise it refuses with "the Codex TUI in <session> does not show thread zpc-<inc> (moved by /new or /resume, or a dialog covers the footer); nothing was queued".

In source TASK-102 (2026-11-03) register mispaired a test session: its label named a thread a killed TUI had left loaded, while the live TUI showed another one. The watcher logged `queued 1 message(s) from @claude-b ... to thread <A>` and printed success, but nothing reached the screen. The message has sat in `~/.codex/queue_1.sqlite` since, for a thread that is no longer loaded. When the labelled thread is still loaded and idle, the daemon runs such a turn headless, shell commands included, with nobody watching (design/zmx-peer-chat-spike.md, test 4). The same applies when the user moves the TUI with `/new` or `/resume`, or a dialog covers the footer.

## Scope

In scope:
- In all-rooms mode, `watch-codex` checks the matched session's screen (`zmx history <session>`) for the footer rule zmx-peer-chat's router uses before it runs `codex queue`. When the TUI does not show `zpc-<inc>`, it logs a `not queued: ...` line with the reason and queues nothing, like the existing refusals in `watch.py`.
- Reuse the same footer rule (the last non-empty lines end with `· zpc-<inc>`). Copying the few lines into agent-chat is acceptable, because the plugins ship separately. Note the shared rule in both READMEs.
- Tests in `plugins/agent-chat/skills/agent-chat/tests/test_agent_chat_codex.py` with the fake `zmx`, which gains a `history` output.
- A patch bump of agent-chat in both `plugin.json` files, and `plugins/agent-chat/README.md`'s Codex watcher paragraph.

Out of scope:
- zmx-peer-chat's register fix (a separate handoff).
- `--thread` mode, where no zmx session is involved: keep it as is and say so in the README.
- Retrying refused mail later (the README already says refused mail is not queued later).
- The source repo's box role and the box install.

## Files

- `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/watch.py` (exists): `CodexWatcher`, the session matching around `zpc.thread`, and `_command(ZMX_ENV, "zmx")` for `zmx history`
- `plugins/agent-chat/skills/agent-chat/tests/test_agent_chat_codex.py` (exists): the fake zmx (`zmx-ls.txt`) gains history output
- `plugins/agent-chat/README.md` (exists): the 'watch-codex' paragraph
- `plugins/agent-chat/.claude-plugin/plugin.json`, `plugins/agent-chat/.codex-plugin/plugin.json` (exist): version 0.2.1, after TASK-58
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/router.py` (exists): `tui_shows()`, the reference rule, read-only

## Source

Source: <source repo>@9a8593b55dc9
Source evidence (read-only context, do NOT modify): <source repo>/backlog/tasks/task-102 - Deliver-agent-chat-room-messages-to-Codex-with-codex-queue.md (the notes 'Starting the test Codex session', 'AC6' and 'Findings for follow-up')

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
- [ ] #1 A test in test_agent_chat_codex.py where the matched session's fake zmx history footer ends with '· zpc-<inc>' still queues the batch with codex queue to that session's zpc.thread
- [ ] #2 A test where the footer does not show '· zpc-<inc>' (another thread name, or a dialog over it) runs no codex queue and writes one 'not queued: ...' line naming the session and zpc-<inc> to the account log
- [ ] #3 A test where zmx history fails for the matched session runs no codex queue and logs the failure
- [ ] #4 plugins/agent-chat/README.md's watch-codex paragraph states the footer check and that it is the same rule as zmx-peer-chat's router; --thread mode is documented as unchanged
- [ ] #5 The version in plugins/agent-chat/.claude-plugin/plugin.json and .codex-plugin/plugin.json is bumped one patch above the version TASK-58 leaves
- [ ] #6 uv run pytest and uv run ruff check . pass
<!-- AC:END -->
