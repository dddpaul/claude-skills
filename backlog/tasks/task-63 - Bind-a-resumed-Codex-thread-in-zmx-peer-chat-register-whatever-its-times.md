---
id: TASK-63
title: Bind a resumed Codex thread in zmx-peer-chat register whatever its times
status: To Do
assignee: []
created_date: '2026-11-03T15:59:00Z'
updated_date: '2026-11-03T15:59:00Z'
labels:
  - zmx-peer-chat
dependencies: []
priority: medium
ordinal: 63000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

The box launcher runs `codex resume --last` in every directory with an interactive Codex rollout, so most Codex sessions start as a resume. The TASK-61 retest (design/zmx-peer-chat.md, "Retest with codex-cli 0.166.0", subsection "Resume") found that with codex-cli 0.166.0 such a session does not bind when the daemon no longer has the thread loaded, which is the case after a reboot or about 50 minutes after the last TUI on it ended. The resume loads the thread again and the TUI shows it, but `thread/read` keeps `updatedAt` at the thread's last turn and `createdAt` at its creation. `_candidates()` in `register.py` takes a thread that was not loaded at the snapshot only when `createdAt >= since` (started) and any thread only when `updatedAt` moved past the snapshot (resumed), so it names no candidate and the bind ends with `no Codex thread opened in <dir> in time; no label set` (code 5). The session starts unpaired; sends to it refuse, so nothing goes to a wrong thread. A resume of a thread that is still loaded was not retested with 0.166.0.

Since TASK-59 the times are only a filter: the bind names one candidate at a time and binds it only when the session footer shows `· zpc-<inc>`, and a candidate the footer does not show gets its previous name back (or `zpc-<inc>-unbound`). So a wider candidate set cannot bind a wrong thread; it can only rename a thread briefly.

## Scope

In scope:
- `_candidates()` (or its caller in `_find_thread`) takes these threads of the session directory, never a thread seen running a turn (`busy`), in this order:
  1. started: not loaded at the snapshot, `createdAt` at or after it (as today);
  2. newly loaded: not loaded at the snapshot, whatever its times (new);
  3. resumed: loaded at the snapshot, `updatedAt` moved past it (as today);
  4. fallback, only while none of 1 to 3 exists: an idle thread that was loaded at the snapshot and whose times did not move (new). This covers a resume of a still-loaded thread if 0.166.0 does not move its `updatedAt` either.
  The footer check, the rename-away and the rotation until the deadline stay as TASK-59 left them.
- With no snapshot (TASK-62, no daemon at registration) every thread in the directory is newly loaded, so it is a candidate.
- The module docstring of `register.py` (it still says resuming moves `updatedAt` "whether the daemon still had it loaded or loads it again"), the pick table and the paragraph "Being newly loaded is not enough" / "The times are a filter, not the proof" in `design/zmx-peer-chat.md`, and `plugins/zmx-peer-chat/README.md` where it describes the pick.
- Tests in `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/test_zpc_register.py` with the fakes in `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/zpc_fakes.py`.
- A live box retest, run interactively (Ralph's container cannot reach the box): copy the working tree to a scratch directory on the box, as TASK-61 did; with the user's explicit OK, start throwaway Codex sessions (prefix `zpc-rt-`) in a scratch directory; resume a thread the daemon has unloaded and a thread it still has loaded; record each in the design doc's retest section with `zmx ls` before and after. No turn needs to run.
- A patch bump of zmx-peer-chat in both `plugin.json` files.

Out of scope:
- The box launcher and the installed plugin version: the source repo owns them.
- Any change to the footer rule, `send`, agent-chat or `TESTED_CODEX_CLI`.
- Starting Codex sessions on the box without the user's explicit OK, which spends quota. Never type into, queue to, register or kill the user's own zmx sessions.

## Files

- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/register.py` (exists): module docstring, `Registration`, `_candidates`, `_find_thread`
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/test_zpc_register.py`, `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/zpc_fakes.py` (exist)
- `design/zmx-peer-chat.md` (exists): "Register helper" (the pick table and the two paragraphs after it) and "Retest with codex-cli 0.166.0"
- `plugins/zmx-peer-chat/README.md` (exists)
- `plugins/zmx-peer-chat/.claude-plugin/plugin.json`, `plugins/zmx-peer-chat/.codex-plugin/plugin.json` (exist): version 0.1.4

Public repo: the design doc carries no IP address, host name, user name, home path, token or conversation text; use the placeholders the retest section uses (`<box>`, `<home>`, `<uid>`, `<pair-id>`, `<thread-r>`).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test where a thread not loaded at the snapshot is loaded during the bind with createdAt and updatedAt both before the snapshot, and the fake footer shows its name once named, ends with zpc.thread naming that thread
- [ ] #2 A test with two threads newly loaded during the bind, both with old times, where the footer shows only one, binds the shown one and gives the other its previous name back
- [ ] #3 A test where no started, newly loaded or resumed thread exists and an idle thread loaded at the snapshot with unmoved times is the one the footer shows ends with zpc.thread naming it
- [ ] #4 The register.py module docstring, the pick table in design/zmx-peer-chat.md and plugins/zmx-peer-chat/README.md (where it describes the pick) state the new candidate rule, and grep finds no remaining claim that a resume always moves updatedAt
- [ ] #5 With the user's explicit OK, a box retest with throwaway zpc-rt- sessions resumes a thread the daemon has unloaded and one it still has loaded, each ends labelled with zpc.thread naming the resumed thread, and design/zmx-peer-chat.md records the commands, outputs and zmx ls before and after
- [ ] #6 The version in both zmx-peer-chat plugin.json files is one patch above the version current at merge
- [ ] #7 uv run ruff check . passes and uv run pytest passes, except the known test_decision_tree_helper failure (un-vendored node_modules)
- [ ] #8 A test shows that a started or newly loaded candidate is named before any fallback thread
- [ ] #9 A test shows that a thread seen running a turn is never named, as a fallback or otherwise
<!-- AC:END -->
