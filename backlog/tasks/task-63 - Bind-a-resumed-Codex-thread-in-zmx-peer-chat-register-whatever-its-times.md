---
id: TASK-63
title: Bind a resumed Codex thread in zmx-peer-chat register whatever its times
status: Done
assignee: []
created_date: '2026-11-03T15:59:00Z'
updated_date: '2026-11-03T16:46:00Z'
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
  4. fallback (new): the idle threads that were loaded at the snapshot and whose times did not move, the most recently updated first (the one `--last` picks), added after 1 to 3 once `FALLBACK_SECONDS` (20 s) have passed in the bind. This covers a resume of a still-loaded thread if 0.166.0 does not move its `updatedAt` either; the delay lets a starting TUI's own thread, which loads a few seconds after the session appears, be tried before any older thread is renamed.
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
- [x] #1 A test where a thread not loaded at the snapshot is loaded during the bind with createdAt and updatedAt both before the snapshot, and the fake footer shows its name once named, ends with zpc.thread naming that thread
- [x] #2 A test with two threads newly loaded during the bind, both with old times, where the footer shows only one, binds the shown one and gives the other its previous name back
- [x] #3 A test where no started, newly loaded or resumed thread exists and an idle thread loaded at the snapshot with unmoved times is the one the footer shows ends with zpc.thread naming it
- [x] #4 The register.py module docstring, the pick table in design/zmx-peer-chat.md and plugins/zmx-peer-chat/README.md (where it describes the pick) state the new candidate rule, and grep finds no remaining claim that a resume always moves updatedAt
- [x] #5 With the user's explicit OK, a box retest with throwaway zpc-rt- sessions resumes a thread the daemon has unloaded and one it still has loaded, each ends labelled with zpc.thread naming the resumed thread, and design/zmx-peer-chat.md records the commands, outputs and zmx ls before and after
- [x] #6 The version in both zmx-peer-chat plugin.json files is one patch above the version current at merge
- [x] #7 uv run ruff check . passes and uv run pytest passes, except the known test_decision_tree_helper failure (un-vendored node_modules)
- [x] #8 A test shows that a started or newly loaded candidate is named before any fallback thread
- [x] #9 A test shows that a thread seen running a turn is never named, as a fallback or otherwise
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: _candidates() orders started, newly loaded (not in the snapshot, any times), resumed, then (after FALLBACK_SECONDS = 20 s in the bind) the idle snapshot threads, most recent first; busy threads never. The fallback waits so a starting TUI's own thread is tried before an older thread is renamed (a plain fallback broke four existing tests that way); the task's Scope item 4 was reworded to match. Tests for AC1-5 plus mutation checks; docs; 0.1.5; then the box retest with the user's OK.

Commit: `9cc073b` - task-63: try a thread newly loaded in the directory whatever its times, and idle snapshot threads after FALLBACK_SECONDS; zmx-peer-chat 0.1.5

AC #5 (run from the Mac over ssh, since only the Mac reaches the box; with the user's OK, branch copy 0.1.5, 2026-11-03): zmx ls before 19:17:12 and after 19:18:03 listed only the user's two sessions; grep -c zpc-rt- after: 0. zpc-rt-codex3 resumed the unloaded test thread: labelled after 7.63 s (newly loaded; times unmoved). zpc-rt-codex4 resumed it while still loaded: updatedAt did not move either, labelled after 20.7 s through the fallback. Both footers showed the new zpc-<inc>. Sessions killed; ~/zpc-retest and the lock removed; transcripts and register.log lines kept. Recorded in design/zmx-peer-chat.md 'Resume after TASK-63'.

AC #7: ruff clean; pytest 539 passed, 1 failed - the known baseline test_decision_tree_helper (un-vendored node_modules).

Commit: `023bb94` - task-63: record both 0.166.0 resumes binding on the box

Review round 1 (CHANGES REQUESTED, 4): fixed the Architecture flow's pick, the old-demo bullet (now notes TASK-63 reopened it and cites the renamed test), the launcher item's bind times and the fallback's brief rename of another TUI's idle thread, the cut probe output, and the AC labels in these notes (AC #5 box, AC #7 tests). Added test_the_candidate_order_once_the_fallback_has_joined and test_only_an_idle_snapshot_thread_is_a_fallback (both mutation-checked). zmx-peer-chat tests 119 passed; ruff clean.

Commit: `2d4ea35` - task-63: align the design doc with the new pick and test the fallback's order and idle-only rule

Review round 2 (CHANGES REQUESTED, 5): 'For the launcher' item 4 now says sends to that TUI refuse meanwhile (only sends to a Codex TUI read its footer).

Commit: `472ce2b` - task-63: say that sends to a TUI whose thread is briefly renamed refuse

Done. register tries, in order: started, newly loaded (any times), resumed, and after FALLBACK_SECONDS (20 s) the idle snapshot threads, most recent first; busy threads never; the footer check decides. Box retest (0.166.0): unloaded resume bound in 7.6 s, still-loaded resume in 20.7 s via the fallback. zmx-peer-chat 0.1.5. task-reviewer: APPROVED (score 10) after three rounds. Final: ruff clean; pytest 542 passed, 1 failed - the known test_decision_tree_helper baseline. Follow-up: an exact pick from daemon events and the --last query (next task).
<!-- SECTION:NOTES:END -->
