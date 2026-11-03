---
id: TASK-62
title: Bind a Codex session in zmx-peer-chat register when no Codex daemon runs yet
status: In Progress
assignee: []
created_date: '2026-11-03T13:52:00Z'
updated_date: '2026-11-03T14:02:00Z'
labels:
  - zmx-peer-chat
dependencies: []
priority: medium
ordinal: 62000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

On a freshly booted box no Codex app-server daemon runs until the first Codex TUI starts one (`daemon_auto_start`). The box's `agent` launcher runs `zmx-peer-chat register --role codex ...` before it starts the TUI, and `prepare()` in `register.py` opens the daemon through `codex app-server proxy` to snapshot the loaded threads (`_snapshot`). With no daemon, `Daemon.open` raises `DaemonError` (exit 3) right there: no background bind starts, nothing reaches `register.log`, and the launcher, which discards register's output, starts the session unpaired.

Observed on 2026-11-03 with codex-cli 0.166.0 and zmx-peer-chat 0.1.0 installed on the box. The box booted at 16:25. At 16:47 agterm restored a claude and a codex pane in one directory: the claude session was labelled at 16:47:38; the codex session, started at 16:47:39, got no `zpc.*` labels and no `register.log` line; the daemon processes started at 16:47:40 and 16:47:41, from the TUI. Afterwards `zmx-peer-chat daemon check` reached the daemon (`daemon ok, 1 loaded thread(s); protocol 1`), so the client works once a daemon runs.

No daemon means no thread is loaded, so an empty snapshot is the correct one. Since TASK-59 the bind confirms a candidate in the TUI footer (`· zpc-<inc>`) before it writes `zpc.thread`, so a candidate the snapshot would have excluded still cannot be bound by mistake.

## Scope

In scope:
- `prepare()` for role `codex`: when the `open_daemon` callable raises `DaemonError`, keep the registration with an empty snapshot (`before` and `busy` empty, `since` as now) and record on the `Registration` that no snapshot was taken, instead of raising. A `DaemonError` raised after a successful open (an unexpected answer to `thread/loaded/list` or `thread/read`) still fails closed, as today. Bad arguments (exit 2) and a concurrent registration (exit 4) are unchanged.
- The background bind: `_find_thread` opens the daemon itself. When that open raises `DaemonError`, retry it (every 0.3 to 0.5 s) until the bind deadline (`BIND_SECONDS`, 60 s by default), then fail with a message that says no Codex daemon was reachable and names the last error. Once open, everything works as TASK-59 left it: candidates, footer confirmation, rename-away.
- The `register.log` line of a session labelled without a snapshot says so, for example `labelled ... (no Codex daemon at registration)`.
- Tests in `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/test_zpc_register.py` with the fakes in `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/zpc_fakes.py`.
- The bind description in `plugins/zmx-peer-chat/README.md` or `design/zmx-peer-chat.md`, and a patch bump in both `plugin.json` files.

Out of scope:
- The box launcher, which sends register's output to `/dev/null` and prints only the exit code: the source repo owns it.
- Starting a daemon from register: register only reads the daemon the TUI starts.
- The tested codex-cli version (TASK-61) and agent-chat.
- Re-pairing sessions that already started unpaired: register leaves an existing session's labels alone.

## Files

- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/register.py` (exists): `Registration`, `prepare`, `_snapshot`, `_find_thread`, `bind`, `bind_in_background`
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/daemon.py` (exists): `DaemonError` (exit 3) and `Daemon.open`, read only
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/test_zpc_register.py` (exists), `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/zpc_fakes.py` (exists)
- `plugins/zmx-peer-chat/.claude-plugin/plugin.json`, `plugins/zmx-peer-chat/.codex-plugin/plugin.json` (exist): version 0.1.2
- `plugins/zmx-peer-chat/README.md`, `design/zmx-peer-chat.md` (exist): the bind description
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A test where the daemon is unreachable at prepare() and for the first bind polls, then comes up with the new TUI's thread named in the fake footer, ends with zpc.thread naming that thread and a register.log line saying no Codex daemon ran at registration
- [x] #2 A test where the daemon never becomes reachable before the bind deadline ends with no labels on the session and a register.log line saying no Codex daemon was reachable
- [x] #3 A test where the daemon is unreachable at prepare() and then comes up with a turn-less leftover thread (createdAt and updatedAt reading as now) loaded next to the new TUI's thread ends with zpc.thread naming the new TUI's thread
- [x] #4 uv run ruff check . passes and uv run pytest passes, except the known test_decision_tree_helper failure (un-vendored node_modules)
- [x] #5 A test where open_daemon raises DaemonError in prepare() for role codex gets a Registration with an empty snapshot, and prepare() raises nothing
- [x] #6 A test where the daemon opens in prepare() but thread/loaded/list raises DaemonError still gets a ZpcError with exit code 3
- [x] #7 plugins/zmx-peer-chat/README.md or design/zmx-peer-chat.md describes the no-daemon case
- [x] #8 The version in both zmx-peer-chat plugin.json files is one patch above the version current at merge
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: Registration gets a snapshot flag; prepare() catches DaemonError only from the open_daemon() call and keeps an empty snapshot. _find_thread opens the daemon through a retry helper (0.4 s apart until the bind deadline, then exit 5 naming the last error). bind_in_background appends '(no Codex daemon at registration)' to the labelled line. Fakes: an opener that fails N times. README bind paragraph + patch bump to 0.1.3.

Commit: `4347986` - task-62: register a Codex session with an empty snapshot when no Codex daemon runs yet
<!-- SECTION:NOTES:END -->
