---
id: TASK-78
title: agent-chat hub coverage in Codex status and hub doc gaps
status: Done
assignee: []
created_date: '2026-11-10T18:08:00Z'
updated_date: '2026-11-10T18:24:00Z'
labels:
  - feature:agent-chat-hub
dependencies:
  - TASK-77
priority: medium
ordinal: 78000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The cumulative review of the agent-chat hub (TASK-74 to TASK-77, verdict Aligned) found one code gap and three doc gaps. They should be fixed before the hub rollout, because the rollout relies on `agent-chat status` to confirm that every host listens to the hub. The review is saved as `design/agent-chat-hub-review-2026-11-10.md`, which is still untracked; this task commits it.

**The code gap: `status --as codex` cannot show hub coverage.** `cmd_status` (cli.py, around line 443) prints `hub: <alias>: <coverage>` from `hub_coverage(state, alias, waiting)`. That function reads `<slug>.hub` next to the hook-wait lock `WaitLock(state, alias_slug(alias))`. Only Claude's wait (`Listener`, listen.py) takes that lock and writes that file: `covered` after `_hub` joins the hub, `unavailable: <why>` from `_hub_down`, and it is removed in `Listener.wait`'s `finally`. The Codex account never runs hook-wait. `CodexWatcher` (watch.py) holds its own lock, `watch-codex` in all-rooms mode or `watch-codex-<slug>` with `--thread` (`self.lock_name`), and writes no coverage file. So on a Codex host the line always reads `hub: #agents-hub:…: not covered (no wait listens)`, even while watch-codex serves the hub. Meanwhile the README's Checks section says `status --as codex` shows "the same for the Codex account".

Fix, mirroring the Listener:

- `CodexWatcher` writes `<lock_name>.hub` in the account's state directory (`watch-codex.hub`, or `watch-codex-<slug>.hub` with `--thread`), using the same `_write_text` helper as listen.py:
  - `covered\n` when `_join_hub` joins the hub;
  - `unavailable: <why>\n` from `_hub_failed`, including the "this account left it" path in `_hub_routes`;
  - the file is removed when the watcher exits, whether it stops normally, after an error, or after a refused token.
- A `--thread` watcher that serves no hub writes no file. That is the case when `self.project` is None, or when the config has no `hub`.
- `status --as codex` takes its `hub:` line from the watcher instead of the hook-wait lock. It checks `watch-codex-<slug>` for this directory's project first, then `watch-codex`, and uses the first lock that is held. The line then reads:
  - the file's content (`covered`, or `unavailable: <why>`);
  - `unknown (watch-codex does not report the hub)` when the lock is held but there is no file;
  - `not covered (no watch-codex runs)` when neither lock is held.
- `status` for Claude (without `--as codex`) keeps its current output and wording.
- The `.owner` pid file format and the lock and cursor names do not change.

**Doc gaps (plugins/agent-chat/README.md):**

1. The rollout order paragraph (`**Rollout order.**`, in the hub section) never tells the operator to confirm coverage. Add a final step: on every host, `agent-chat status` and `agent-chat status --as codex` print `hub: <hub alias>: covered` before anyone relies on the hub.
2. The Checks section's `status --as codex` line says "the same for the Codex account". Make it say that the hub line comes from the running watch-codex.
3. The hub table's `Waits` row says where `status` gets coverage for Claude. The `watch-codex` row, or the watch-codex section, gets the Codex counterpart: the `<lock name>.hub` file.
4. Add one sentence to the watch-codex section: running `watch-codex --thread <uuid>` and all-rooms `watch-codex` for the same account on one host is unsupported. Their locks and cursors differ, so both may queue the same hub mail.
5. The `Sending` row's refusal list lacks the bare `--hub` refusal. `_check_hub_flags` refuses `--hub` with neither `--project` nor `--thread`, with `--hub needs --project, or --thread to answer the user; nothing was sent`. Add it to the list.

The Codex skill (`plugins/agent-chat/codex-skills/agent-chat/SKILL.md`) stays as it is. It tells Codex that `status` needs the user's approval and that hub mail arriving is the sign the hub is on. The Claude skill also stays as it is.

**Version:** 0.5.4, a patch release. It goes in both `plugins/agent-chat/.claude-plugin/plugin.json` and `plugins/agent-chat/.codex-plugin/plugin.json`, and in the pin in `test_agent_chat_codex.py` (`assert codex["version"] == claude["version"] == "0.5.3"`).

**Constraints:** this repo is public. Docs and tests carry no IP address, host name, user name, home path, token or conversation text. Use the placeholders the existing hub tests use: `example.test`, `@codex-a`, projects alpha/beta, `#agents-hub`.

**Files:**

- `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/watch.py`
- `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/cli.py`
- `plugins/agent-chat/skills/agent-chat/tests/test_agent_chat_codex.py` (the watcher's coverage file, Codex status, the doc pins, the version pin)
- `plugins/agent-chat/README.md`
- `plugins/agent-chat/.claude-plugin/plugin.json`
- `plugins/agent-chat/.codex-plugin/plugin.json`
- `design/agent-chat-hub-review-2026-11-10.md` (commit as is)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 watch-codex writes <lock_name>.hub in the account's state directory: covered after it joins the hub, unavailable: <why> after a hub failure (the account leaving the hub included); a test against the fake homeserver checks both, for all-rooms and --thread mode
- [x] #2 watch-codex removes its .hub file when it exits, after a normal stop and after an error; a --thread watcher that serves no hub writes none; tests check each case
- [x] #3 status --as codex prints the hub line from the held watcher lock (watch-codex-<slug> first, then watch-codex): the file's content, 'unknown (watch-codex does not report the hub)' with a held lock and no file, 'not covered (no watch-codex runs)' with no lock held; a test checks each of the three
- [x] #4 status without --as codex keeps its current output; the existing status tests in test_agent_chat_hub_wait.py pass unchanged, and the .owner pid format and the lock and cursor names are unchanged
- [x] #5 README rollout order ends with confirming hub: <hub alias>: covered from agent-chat status and agent-chat status --as codex on every host, and the Checks line for status --as codex says its hub line comes from the running watch-codex
- [x] #6 README says running watch-codex --thread and all-rooms watch-codex for the same account on one host is unsupported, because both may queue the same hub mail
- [x] #7 README's hub Sending row lists the refusal of --hub with neither --project nor --thread
- [x] #8 A doc test in test_agent_chat_codex.py pins the rollout confirmation step, the unsupported-watcher-pair sentence and the bare --hub refusal in README.md
- [x] #9 Both plugin.json files and the version pin in test_agent_chat_codex.py read 0.5.4
- [x] #10 design/agent-chat-hub-review-2026-11-10.md is committed; uv run ruff check . is clean and uv run pytest plugins/agent-chat passes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: CodexWatcher gets hub_file (<lock_name>.hub, None when it serves no hub), written via listen._write_text in _join_hub/_hub_failed and removed in a finally around run(); cmd_status --as codex picks the first held of watch-codex-<slug>, watch-codex and reads watch_coverage(); README rollout/Checks/watch-codex row/unsupported pair/bare --hub refusal; doc test; 0.5.4.

Commit: `e3e5ab7` - task-78: report watch-codex hub coverage in status --as codex and close the hub doc gaps

Commit: `1a10ba9` - task-78: reflow the hub review's prose, drop its commit range, make write_text public

Done: CodexWatcher writes <lock_name>.hub (covered / unavailable: <why>, the account leaving included) and removes it in a finally around run(); a --thread watcher serving no hub has hub_file None. status --as codex reads the first held of watch-codex-<slug>, watch-codex via watch_coverage(); Claude's status untouched. README: rollout confirmation step, Checks line, watch-codex row coverage file, unsupported watcher pair, bare --hub refusal; doc test pins them. 0.5.4. Test helper Running now records thread exceptions so error-exit tests leave no warnings. listen._write_text made public write_text. Deviation from 'commit as is': the design review was reflowed (R-DOCS-3) and its SHA range dropped (R-DOCS-2) at the task-reviewer's request. ruff clean; pytest plugins/agent-chat 281 passed, 7 skipped. Review: APPROVED (task-reviewer, re-review of 1a10ba9).
<!-- SECTION:NOTES:END -->
