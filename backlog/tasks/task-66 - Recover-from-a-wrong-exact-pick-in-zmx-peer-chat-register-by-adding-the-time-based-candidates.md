---
id: TASK-66
title: >-
  Recover from a wrong exact pick in zmx-peer-chat register by adding the
  time-based candidates
status: Done
assignee: []
created_date: '2026-11-04T06:43:00Z'
updated_date: '2026-11-04T06:54:00Z'
labels:
  - zmx-peer-chat
dependencies: []
priority: medium
ordinal: 66000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Since TASK-64, `register` in zmx-peer-chat picks the Codex thread from the session's command (`cmd=` in `zmx ls`). `_exact()` in `register.py` returns a poll for that thread: the `thread/started` threads of the directory for `codex`, the answer of one `Daemon.latest_thread()` call for `codex resume --last`, or the named id for `codex resume <id>`. While `_exact()` returns a poll, `_find_thread()` tries only its candidates and never the TASK-63 pick (`_candidates()`).

So when the exact answer is wrong, the bind cannot recover. It names that thread `zpc-<inc>`, the footer does not show it within `CONFIRM_SECONDS` (5 s), it gets its name back, and the same thread is tried again, until `BIND_SECONDS` (60 s) runs out with `named but not bound` (code 5). The session starts unpaired, and the wrong thread is renamed about twelve times. TASK-64's review named the ways the `--last` answer can be wrong:
- it is stale: the query ran once at the bind's start;
- it names a thread another TUI shows;
- a profile or a session flag picked a model provider that `config/read` does not report, so the TUI's own lookup filtered differently.

A `thread/started` from another TUI starting a thread in the same directory at the same moment can likewise be the only exact candidate for a while.

## Scope

In scope:
- In `_find_thread()`: once an exact candidate has failed one footer check, add the TASK-63 candidates (`_candidates()`, with its `FALLBACK_SECONDS` timer as now) to the rotation after the exact candidates. The rotation stays as it is, least recently tried first, so the exact candidate is tried again in turn. A correct exact candidate whose footer a startup dialog hid is still bound once the dialog closes.
- For `codex resume --last`: after the first failed footer check, run `latest_thread()` once more and add its answer if it names another thread.
- Log the switch, so `register.log` explains a bind that left the exact pick. For example, append `(after the exact pick)` to the `labelled` line.
- Tests in `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/test_zpc_register.py` with the fakes in `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/zpc_fakes.py`.
- The "Register helper" section of `design/zmx-peer-chat.md` (the exact-pick table and the text after it), `plugins/zmx-peer-chat/README.md` where it describes the pick, and a patch bump in both `plugin.json` files.

Out of scope:
- A box retest: the failing cases cannot be staged on demand, and the fakes cover them.
- Any change to the exact signals themselves, the footer rule, `send` or agent-chat.

## Files

- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/register.py` (exists): `_exact`, `_find_thread`, `_candidates`, `bind_in_background`
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/daemon.py` (exists): `Daemon.latest_thread`, read only
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/test_zpc_register.py`, `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/zpc_fakes.py` (exist)
- `design/zmx-peer-chat.md`, `plugins/zmx-peer-chat/README.md` (exist)
- `plugins/zmx-peer-chat/.claude-plugin/plugin.json`, `plugins/zmx-peer-chat/.codex-plugin/plugin.json` (exist): version 0.1.7
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A test where the --last answer names a thread the footer never shows while the TUI shows another thread of the directory ends with zpc.thread naming the shown thread before the deadline, and the --last thread gets its previous name back
- [x] #2 A test where the first latest_thread() answer is stale and the second, run after the first failed footer check, names the shown thread binds that thread
- [x] #3 A test where the exact candidate is right but a dialog hides the footer for longer than CONFIRM_SECONDS still binds it once the footer shows its name
- [x] #4 A test where cmd is codex and the only thread/started for the directory belongs to another TUI binds the thread the footer shows through the added time-based candidates
- [x] #5 A test where the exact candidate is shown at once never names a time-based candidate
- [x] #6 The version in both zmx-peer-chat plugin.json files is one patch above the version current at merge
- [x] #7 uv run ruff check . passes and uv run pytest passes, except the known test_decision_tree_helper failure (un-vendored node_modules)
- [x] #8 The register.log labelled line says when the bind left the exact pick
- [x] #9 design/zmx-peer-chat.md (Register helper) and plugins/zmx-peer-chat/README.md describe the recovery from a wrong exact pick
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: in _find_thread, track whether an exact candidate failed a footer check; then merge _candidates() after the exact ones in the least-recently-tried rotation; _exact's poll takes that flag and re-runs latest_thread() once for --last; Registration.left_exact drives the '(after the exact pick)' log suffix. Tests with FakeDaemon.last accepting a list of answers.

Commit: `647887a` - task-66: add the time-based candidates after a failed exact pick in register

Commit: `2ace42c` - task-66: say when a wrong exact pick names another TUI's thread or waits FALLBACK_SECONDS

Implemented: after an exact candidate fails one footer check, _find_thread adds _candidates() after the exact ones in the least-recently-tried rotation; --last re-queries latest_thread() once; Registration.left_exact adds '(after the exact pick)' to the labelled log line. Docs and README updated; version 0.1.8. task-reviewer: CHANGES REQUESTED (bind-time and other-TUI sentences, docstring wrap) then APPROVED after 2ace42c.
<!-- SECTION:NOTES:END -->
