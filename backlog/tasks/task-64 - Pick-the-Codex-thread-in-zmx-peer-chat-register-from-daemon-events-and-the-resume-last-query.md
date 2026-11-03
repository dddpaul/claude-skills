---
id: TASK-64
title: >-
  Pick the Codex thread in zmx-peer-chat register from daemon events and the
  resume --last query
status: To Do
assignee: []
created_date: '2026-11-03T16:47:00Z'
updated_date: '2026-11-03T17:36:00Z'
labels:
  - zmx-peer-chat
dependencies:
  - TASK-63
priority: medium
ordinal: 64000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

`register` in zmx-peer-chat infers the Codex thread a new TUI shows from `createdAt` and `updatedAt`, and every codex-cli release has bent that inference: TASK-59 (a leftover thread reads as now), TASK-62 (no daemon at registration), TASK-63 (codex-cli 0.166.0 moves no time on a resume, so a newly loaded thread is a candidate whatever its times and idle snapshot threads are a fallback after 20 s). The footer check keeps a wrong pick from being bound, but the pick itself is a guess, a still-loaded resume binds only after `FALLBACK_SECONDS`, and the fallback can briefly rename another TUI's thread.

The codex-cli 0.166.0 source (github.com/openai/codex, tag `rust-v0.166.0`) gives exact signals instead:

- **Fresh start.** `thread/start` makes the daemon send a `thread/started` notification, carrying the new thread (id, cwd), to every initialized client connection that has not opted out of it: `codex-rs/app-server/src/request_processors/thread_processor.rs` sends it through the global `OutgoingMessageSender::send_server_notification`, and `codex-rs/app-server/src/transport.rs` (`route_outgoing_envelope`, `OutgoingEnvelope::Broadcast`) delivers it to every initialized connection. A register client that stays connected during the bind therefore learns the fresh TUI's thread id directly.
- **`codex resume --last`.** The TUI picks the thread with one `thread/list` call (`codex-rs/tui/src/lib.rs`, `lookup_latest_session_target_with_app_server` and `latest_session_lookup_params`): `limit` 1, `sortKey` updated-at, a cwd filter of the session directory, the interactive source kinds (`resume_source_kinds(false)`), `archived` false, the history model provider, first with `useStateDbOnly` true and then false, and the first thread whose rollout file exists. Register can send the same query for the session directory and know which thread `--last` resumes, loaded or not.
- **`codex resume <id>`** names the thread outright.
- **Reload.** A thread that goes from not loaded to loaded makes the daemon broadcast `thread/status/changed` (`codex-rs/app-server/src/thread_status.rs`), a cross-check for an unloaded resume.
- **Not usable:** Codex's `SessionStart` hook is queued at session creation but runs only at the start of the first turn (`codex-rs/core/src/hook_runtime.rs`, `run_pending_session_start_hooks`, called from `codex-rs/core/src/session/turn.rs`), so a hook cannot bind an idle TUI.

## Scope

In scope:
- The register bind reads the new session's command from `zmx ls` (`cmd=`, as the launcher starts it: `codex`, `codex resume --last` or `codex resume <id>`) and picks the thread from it:
  - `codex`: the first `thread/started` notification whose thread's cwd is the session directory, received on a daemon connection that register opens before the TUI starts and keeps for the bind;
  - `codex resume --last`: the thread the TUI's own `thread/list` query returns for the session directory;
  - `codex resume <id>`: that id.
  The thread is named `zpc-<inc>` and bound only when the footer shows the name, as now.
- When the exact signal is missing (no daemon at registration, so the `thread/started` came before register could connect; an unknown command; a query that returns nothing), the bind falls back to the TASK-63 pick, unchanged.
- The daemon client keeps the notifications it reads (today `Daemon.call` skips them) and gains the `thread/list` call. The request's params match the TUI's; check the wire names and enum values in `codex-rs/app-server-protocol` at the same tag, and how the TUI derives the history model provider.
- Tests in `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/` with fakes for the notification stream, the `thread/list` answer and the session's `cmd=`.
- The live box retest is TASK-65, run interactively after this task merges (Ralph's container cannot reach the box).
- `design/zmx-peer-chat.md` ("Register helper", the pick table, the retest section) and `plugins/zmx-peer-chat/README.md`; a patch bump in both `plugin.json` files.

Out of scope:
- The box launcher and the installed plugin version: the source repo owns them.
- Removing the TASK-63 pick: it stays as the fallback.
- The footer rule, `send`, agent-chat, `TESTED_CODEX_CLI`.
- Starting Codex sessions on the box without the user's explicit OK, which spends quota. Never type into, queue to, register or kill the user's own zmx sessions.

## Files

- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/register.py` (exists): `prepare`, `_find_thread`, `bind`, `_candidates` (the fallback)
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/daemon.py` (exists): `Daemon.call`, `_message`, a new `thread/list` call and notification buffer
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/zmx.py` (exists): `Session` and `zmx ls` parsing, for `cmd=`
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/test_zpc_register.py`, `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/test_zpc_daemon.py`, `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/zpc_fakes.py` (exist)
- `design/zmx-peer-chat.md`, `plugins/zmx-peer-chat/README.md` (exist)
- `plugins/zmx-peer-chat/.claude-plugin/plugin.json`, `plugins/zmx-peer-chat/.codex-plugin/plugin.json` (exist)

Public repo: the design doc carries no IP address, host name, user name, home path, token or conversation text; use the retest section's placeholders (`<box>`, `<home>`, `<uid>`, `<pair-id>`, `<thread-r>`).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test where the session's cmd is codex and the fake daemon sends a thread/started notification for the session directory ends with zpc.thread naming that thread, while a leftover thread in the directory whose times read as now is never named
- [ ] #2 A test where the session's cmd is codex resume --last binds the thread the fake thread/list answer returns, though it was loaded at the snapshot with unmoved times, and names no other thread
- [ ] #3 A test where the session's cmd is codex resume <id> binds that id
- [ ] #4 A test where no exact signal is available (the daemon came up after the session, or the cmd is unknown) still binds through the TASK-63 pick
- [ ] #5 A test pins the thread/list request params to the TUI's --last query (limit 1, updated-at sort, the cwd filter, interactive source kinds, not archived), with a comment naming codex-rs/tui/src/lib.rs latest_session_lookup_params at rust-v0.166.0
- [ ] #6 design/zmx-peer-chat.md (Register helper and the pick table) and plugins/zmx-peer-chat/README.md describe the exact pick and the fallback
- [ ] #7 The version in both zmx-peer-chat plugin.json files is one patch above the version current at merge
- [ ] #8 uv run ruff check . passes and uv run pytest passes, except the known test_decision_tree_helper failure (un-vendored node_modules)
<!-- AC:END -->
