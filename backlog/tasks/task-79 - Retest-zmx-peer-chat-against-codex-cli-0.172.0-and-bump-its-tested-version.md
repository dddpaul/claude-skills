---
id: TASK-79
title: Retest zmx-peer-chat against codex-cli 0.172.0 and bump its tested version
status: In Progress
assignee: []
created_date: '2026-11-24T17:18:00Z'
updated_date: '2026-11-24T17:57:00Z'
labels:
  - zmx-peer-chat
dependencies: []
priority: medium
ordinal: 79000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

zmx-peer-chat drives an undocumented codex-cli API (the app-server daemon's JSON-RPC through `codex app-server proxy`), so it fails closed: `zmx-peer-chat daemon check` exits 1 when `codex --version` is not `TESTED_CODEX_CLI` (`"0.166.0"` in `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/common.py`, set by TASK-61). The source repo's box role runs that check on every real run after the codex concern, and a non-zero exit fails the play before the later concerns run.

On 2026-11-24 the user asked to move the box's codex-cli from 0.166.0 to 0.172.0. The source repo held that bump back until zmx-peer-chat is retested against codex-cli 0.172.0 and released; only the claude-code bump went ahead (source TASK-137). The box's app-server daemon has already updated itself: on 2026-11-24 `~/.codex/packages/app-server-daemon/releases/` there holds 0.171.0 and 0.172.0, and the running daemon is the 0.172.0 one, while the CLI on PATH is still 0.166.0. So the box today already runs zmx-peer-chat against a 0.172.0 daemon from a 0.166.0 CLI.

## Scope

In scope:
- Retest the daemon client against codex-cli 0.172.0, as TASK-61 did for 0.166.0. A way to get a 0.172.0 CLI on the box without touching its global install (which the source repo's role owns): a scratch npm prefix, for example `npm install --prefix ~/zpc-retest/codex @openai/codex@0.172.0`, put first on PATH for the probes only. Re-run the probes design/zmx-peer-chat-spike.md and design/zmx-peer-chat.md rely on: thread/loaded/list, thread/read (cwd, status, createdAt, updatedAt, name), thread/name/set and the footer showing `zpc-<inc>`, `codex queue` to an idle and a busy TUI, the resume path (`codex resume <id>`), and the `codex plugin list` output the source role parses. Record each command and its output.
- Set `TESTED_CODEX_CLI = "0.172.0"`, update the tests that pin it, and record the retest in the design doc.
- A patch bump of the zmx-peer-chat version in both `plugin.json` files, one above the version current at merge (0.1.9 today).

Out of scope:
- The source repo's box role and its codex pin: the source repo bumps it to 0.172.0 after this release, and its next run upgrades the box's zmx-peer-chat plugin.
- The global codex install on the box, and restarting the user's codex daemon.
- agent-chat, and any zmx-peer-chat behaviour change the retest does not require.
- Starting Codex sessions on the box without the user's explicit OK, which spends quota. Never type into, queue to, register or kill the user's own zmx sessions; use test sessions only, and remove the scratch prefix afterwards.

## Files

- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/common.py` (exists): `TESTED_CODEX_CLI`
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/daemon.py` (exists): the RPC calls the retest exercises
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/tests/` (exists): tests that pin the tested version (test_zpc_daemon.py, test_zpc_cli.py, test_zpc_register.py)
- `plugins/zmx-peer-chat/README.md` (exists): names the tested codex-cli
- `design/zmx-peer-chat.md`, `design/zmx-peer-chat-spike.md` (exist): where the retest is recorded
- `plugins/zmx-peer-chat/.claude-plugin/plugin.json`, `plugins/zmx-peer-chat/.codex-plugin/plugin.json` (exist): version

## Source

Source: <projects>/mycloud@78925cf0c013
Source context (read-only, do NOT modify): <projects>/mycloud/ansible/roles/<box>/README.md, section "The daemon check, and a codex bump"; <projects>/mycloud/ansible/roles/<box>/tasks/zpc_check.yml

## Before starting (destination Claude validation checklist)

Before running this task, verify:
1. All `(exists)` file paths in the Files section still exist in this repo.
2. Each AC is objectively pass/fail (a grep, test invocation, build command, or visible behavior - not "works correctly").
3. All dependencies in the task's frontmatter are status=Done.
4. Out-of-scope items are not accidentally pulled in by ambiguous AC.
5. The box's running app-server daemon is 0.172.0 (`ls ~/.codex/packages/app-server-daemon/releases/` there, and the daemon process path), and codex-cli 0.172.0 is on npm (`npm view @openai/codex@0.172.0 version`).

If anything is unclear or any check fails: STOP and ask the user. Do NOT start work blindly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 grep -n 'TESTED_CODEX_CLI = "0.172.0"' plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/common.py matches
- [x] #2 zmx-peer-chat daemon check on the box with codex-cli 0.172.0 first on PATH exits 0 and prints 'codex-cli 0.172.0 (tested with codex-cli 0.172.0); daemon ok, ...', recorded in the task notes
- [x] #3 The retest's probe commands and outputs (thread/loaded/list, thread/read, thread/name/set with the footer showing zpc-<inc>, codex queue to an idle and a busy test TUI, codex resume <id>, the codex plugin listing) are recorded in design/zmx-peer-chat.md or design/zmx-peer-chat-spike.md
- [x] #4 Every live probe used test Codex sessions started with the user's OK, recorded with their names and zmx ls before and after, and the scratch codex prefix is removed afterwards
- [x] #5 The version in plugins/zmx-peer-chat/.claude-plugin/plugin.json and .codex-plugin/plugin.json is one patch above the version current at merge
- [x] #6 uv run pytest plugins/zmx-peer-chat and uv run ruff check . pass
- [x] #7 latest_params sends the thread/list params of latest_session_lookup_params at rust-v0.172.0 for a resume (currentAccountOnly true, modelProviders empty), pinned by test_latest_params_are_the_tuis_resume_last_query, and a codex resume --last of a thread the daemon had unloaded binds on the box through the exact pick, recorded in design/zmx-peer-chat.md
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: interactive on the host over ssh <box> (Ralph's devcontainer has no ssh access to the box). AC #6 rescoped with the user's OK to uv run pytest plugins/zmx-peer-chat plus ruff, because the whole-repo suite has the unrelated test_decision_tree_helper failure. 1) TESTED_CODEX_CLI = 0.172.0, the test_zpc_cli pin, version 0.1.10. 2) On the box: scratch prefix ~/zpc-retest/codex with @openai/codex@0.172.0 first on PATH for the probes only (the login shell's codex function execs codex from PATH, so its proxy stays); the branch's plugin copied to ~/zpc-retest/copy with tar. 3) With the user's OK, throwaway zpc-retest-* sessions only: daemon check, thread/loaded/list and thread/read via a probe script that prints only scratch threads, register + thread/name/set + footer, codex queue to an idle and a busy TUI, codex resume <id> and --last, codex plugin list, daemon skills; zmx ls before and after. 4) Record in design/zmx-peer-chat.md as 'Retest with codex-cli 0.172.0', with placeholders for home paths, host names, thread ids and the user's session names. 5) Kill the test sessions, remove ~/zpc-retest and the scratch mail-root entries.

Retest on the box 2026-11-24 (recorded in design/zmx-peer-chat.md, "Retest with codex-cli 0.172.0"). AC #2, with codex-cli 0.172.0 from the scratch prefix ~/zpc-retest/codex first on PATH and the branch copy as Z: `Z daemon check` -> `codex-cli 0.172.0 (tested with codex-cli 0.172.0); daemon ok, 4 loaded thread(s); protocol 1`, exit 0. The installed 0.166.0 CLI against the new pin: `codex-cli 0.166.0 (tested with codex-cli 0.172.0); daemon ok, 4 loaded thread(s); protocol 1`, exit 1. Probes: fresh start bound in 1.62 s (thread/started), footer zpc-<inc>; codex queue to an idle and a busy TUI worked; resume --last and resume <id> of a loaded thread bound in 1.61 s; codex plugin list (binary, no proxy) unchanged from 0.166.0, the stderr 403 warning from the remote catalog shows with both versions; daemon skills lists both plugins. Finding: latest_session_lookup_params changed in 0.172.0 (resume: all model providers, current_account_only true). With the user's OK latest_params now sends currentAccountOnly true and modelProviders [], and the config/read history-provider lookup is gone; checked live: Daemon.latest_thread answered the test thread, and an unloaded resume --last bound in 1.61 s. Sessions, with the user's OK: zpc-retest-claude, zpc-retest-codex, -codex2, -codex3, -codex4; the user's 11 sessions identical by name before and after; ~/zpc-retest (the scratch prefix included) and the test pair's mail-root entries removed; the global codex stays 0.166.0.

Commit: `3b4144e` - task-79: test zmx-peer-chat against codex-cli 0.172.0 and follow its resume --last query

Scope: AC #7 added after the retest found that 0.172.0 changed the TUI's resume --last query; the user chose to follow it in this task (latest_params, config/read lookup removed), so this behaviour change is in scope. Box-only ACs (#2, #4, the live half of #7): they ran over ssh from the host in the interactive session, with the user's explicit OK for the zpc-retest-* Codex sessions; Ralph's devcontainer and a review environment cannot reach the box, so a review checks the records (task notes, design/zmx-peer-chat.md). Re-check from the host: `ssh <box> 'bash -l'`; `npm install --prefix ~/zpc-retest/codex @openai/codex@0.172.0` and put ~/zpc-retest/codex/node_modules/.bin first on PATH; copy this tree to ~/zpc-retest/copy and run `~/zpc-retest/copy/bin/zmx-peer-chat daemon check` (expect exit 0, `codex-cli 0.172.0 (tested with codex-cli 0.172.0); daemon ok, ...`); cleanup: `zmx ls | grep -c zpc-retest` (expect 0) and `test ! -e ~/zpc-retest`. Re-checked at 20:57: 0 zpc-retest sessions, no ~/zpc-retest, the user's 11 sessions still there. Review fixes: design table manifest version 0.1.10, README bind time names 0.172.0, the record notes the re-copy of the tree before the new-query probes.
<!-- SECTION:NOTES:END -->
