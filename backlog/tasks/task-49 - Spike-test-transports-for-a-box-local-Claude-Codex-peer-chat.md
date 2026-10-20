---
id: TASK-49
title: 'Spike: test transports for a box-local Claude-Codex peer chat'
status: Done
assignee: []
created_date: '2026-10-20 05:16'
updated_date: '2026-10-20 06:44'
labels: []
dependencies: []
priority: medium
ordinal: 49000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

A Claude Code and Codex pair that runs on a remote Linux box - each agent in its own zmx session, shown in
agterm panes on the Mac through `ssh -t` - cannot use the existing `peer-chat` skill. Its transport drives agterm's
control socket through `agtermctl`, an arm64 macOS binary, and that socket lives on the Mac. Bridging the socket
into the box is rejected: a box agent could then type into any agterm session on the Mac. A box-local transport
is needed, to be packaged later as a new plugin in this repo (working name `zmx-peer-chat`). Before designing it,
this spike finds out by experiment which delivery paths actually work on the box, because the answer decides the
plugin's shape.

## Context (decisions already made, do not reopen)

- Everything stays on the box; nothing forwards agterm's socket or connects back to the Mac.
- A dedicated box router, not an `agtermctl` shim (a shim would have to fake the cursor and weaken the safety checks).
- Pairing uses zmx labels: a pair id from the canonical directory and a random incarnation id set by the launcher
  when it creates a session. zmx 0.8.1 `attach --labels` relabels an existing session too (`src/main.zig`
  1581-1586), so the launcher must inspect labels before attaching.
- Messages to Claude go only through a mailbox, picked up by Claude's background wait; a send reports "queued",
  never "delivered", when no wait runs. The mailbox needs a collector lock.
- Candidate for Claude-to-Codex: `codex queue --thread <UUID-or-exact-name> --message <TEXT>` ("Queue a message for
  an existing session", codex-cli 0.163.0). Known only from `--help`: delivery to a running TUI, wakeup and thread
  binding are unproven.
- Fallback for Claude-to-Codex: typing with `zmx send <name> <text>` after reading the screen with
  `zmx history <name> --vt`.

## Environment

- The box: WSL2 Ubuntu 24.04, reached from the Mac with `ssh agentbox`. The `agent <dir> [claude|codex|shell]
  [-n NAME]` launcher in `/usr/local/bin` starts a tool inside a zmx session; claude runs under Happy
  (happy-coder). See "Agents in zmx sessions" in the mycloud README listed under Files.
- Expected versions (record what the box actually reports): codex-cli 0.163.0, zmx 0.8.1, claude-code 2.1.280,
  happy-coder 1.1.9.
- Mac reference implementation, read-only: `~/.config/agterm/scripts/peer-chat-route.sh`, `peer-mail.sh`,
  `peer-chat.py` (vendored agterm cookbook two-agent-chat @fe1948b), `~/.claude/skills/peer-chat/SKILL.md`,
  `~/.codex/skills/peer-chat/SKILL.md`, `~/.codex/rules/default.rules`. `peer-mail.sh` uses BSD `stat -f %m`;
  on the box use the Linux equivalent.

## How to run it

- Interactive only: Ralph's devcontainer cannot reach the box.
- Ask the user for an explicit OK before starting any Claude or Codex session on the box (it spends their quota).
  The Happy local/remote switch in AC #5 needs the user to act from the Happy phone app.
- Use only throwaway zmx sessions named `spike-*` in a scratch directory on the box. Never type into, queue to or
  kill the user's own sessions (`zmx ls` shows them). Kill the `spike-*` sessions at the end; leave the transcripts
  in `~/.claude/projects` and `~/.codex/sessions`.
- This repo is public: the doc carries no IP address, host name, user name, home path, token or conversation text.
  Trim or replace such output with placeholders.

## Scope

In scope:
- Experiments on the box listed in the acceptance criteria.
- `design/zmx-peer-chat-spike.md` with commands, trimmed output, verdicts and a recommendation.

Out of scope:
- Any plugin, `SKILL.md`, script or test under `plugins/`, and any `plugin.json` version bump.
- Codex packaging: `codex plugin marketplace add`, a Codex catalog for this repo, skill discovery by Codex. That
  belongs to the plugin task.
- Changes to the box beyond the throwaway sessions and the scratch directory: no config, launcher or mycloud edits.
- Deleting the throwaway sessions' transcripts.

## Files

- `design/zmx-peer-chat-spike.md` (to-create) - the spike's findings, the only repo artifact.
- `~/Private/Projects/mycloud/ansible/roles/agentbox/README.md` (exists, outside this repo, read-only) -
  the box, the `agent` launcher and zmx sessions.

## Source

Source: ~/Private/Projects/mycloud@2a4766b64146

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
- [x] #1 design/zmx-peer-chat-spike.md exists and opens with a version table of codex-cli, zmx, claude-code and happy-coder exactly as their version commands report them on the box
- [x] #2 The doc records codex queue --thread <id> --message <text> against a throwaway Codex TUI in a spike-* zmx session in three cases (Codex idle, Codex busy mid-turn, an id matching no session), each with the exact command, trimmed output and the observed TUI behaviour
- [x] #3 The doc states how a launcher learns the thread UUID or exact name of the Codex session it started, with the command that demonstrates it on the box
- [x] #4 If codex queue does not deliver to a running TUI, the doc records zmx history --vt observation of a throwaway Codex session (current screen vs scrollback, cursor position, empty vs occupied composer, an approval dialog, Codex exited to a shell) and a marker typed with zmx send, read back and removed before any submit; if it does deliver, the doc says this check was skipped and why
- [x] #5 The doc records whether a background mailbox waiter wakes a throwaway Claude session under Happy on the box when a message file lands in its inbox, in local mode and after the user switches to remote mode and back, with the commands used
- [x] #6 The doc ends with a recommended transport for each direction and a 'Distilled for ralph-task' section (direction, locked decisions with rationale, scope cuts, acceptance criteria sketch, implementation checklist) for the zmx-peer-chat plugin task
- [x] #7 grep -nE '([0-9]{1,3}\.){3}[0-9]{1,3}|/home/[a-z]|/Users/[a-z]' design/zmx-peer-chat-spike.md prints nothing
- [x] #8 ssh agentbox zmx ls lists no session whose name starts with spike-
- [x] #9 git diff --stat master -- plugins is empty, uv run ruff check . passes, and uv run pytest has no failures other than test_helper_renders_canonical_decision_tree, which already fails on master
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: interactive run on the host over ssh agentbox (Ralph's container has no ssh key/alias). 1) versions; 2) codex queue --help and thread-id discovery (codex session files / codex resume listing); 3) throwaway spike-codex TUI in a scratch dir via the agent launcher or zmx directly, then codex queue idle / busy / bogus id, observing the TUI with zmx history --vt; 4) zmx send fallback only if queue does not deliver; 5) throwaway spike-claude under Happy with a background mailbox waiter (Linux stat), file drop in local mode and after a remote/local switch by the user; 6) design/zmx-peer-chat-spike.md with placeholders for host/user/paths; 7) kill spike-* sessions, AC greps, ruff, pytest, review, merge.

Commit: `2d909f7` - task-49: record the zmx peer-chat transport spike on the box

Ran interactively on the host over ssh (Ralph's devcontainer reaches the box's port but has no ssh key or alias). Findings: codex queue delivers through the app-server daemon's queue to the idle TUI (new turn at once) and the busy TUI (next turn after the current one, no steer); random UUID and unknown name exit 1 with nothing queued; by name only after the first turn, by UUID from the start. The launcher learns the UUID from the daemon over codex app-server proxy (JSON-RPC over WebSocket: thread/loaded/list + thread/read, matched on cwd and createdAt), before any rollout exists. After the TUI exits the daemon keeps the thread loaded and runs queued messages headless, so the sender must check the zmx session first. zmx send fallback skipped (AC #4). Mailbox wait wakes Claude under Happy in local and remote mode, but each mode switch kills the wait; messages stay queued until a new wait starts; $PPID in the wait command forces an approval on every start. AC #8: ssh agentbox zmx ls lists only the user's own session after cleanup. AC #9: no plugins diff; ruff clean; pytest 243 passed, 1 failed (test_helper_renders_canonical_decision_tree, as on master).

Review round 1: CHANGES REQUESTED (B1 exact commands for the no-session case; B2 the $PPID approval was observed only in local manual mode, remote-mode approval not recorded; B3 Codex packaging cut contradicted the checklist and TASK-49's assignment of it to the plugin task; B4 createdAt is not the thread start time (it read the first thread/read time), so the UUID rule is the before/after difference of loaded ids with a matching cwd; m1 no trigger restarted the wait after a mode switch, now an open risk; m2 N=10 s; m3 pytest carve-out). Correction to the earlier note: '$PPID in the wait command forces an approval on every start' holds for local manual mode only.

Commit: `0995507` - task-49: correct the spike's UUID rule, approval scope and Codex packaging, add open risks

Commit: `5035b30` - task-49: count every local wait prompt and name the router's channel for a restart request

task-reviewer round 2: APPROVED, score 8, 0 blocking; both minor notes fixed (five local prompts, not three; the router's restart request goes through a non-typing channel to the person). Final: AC #7 grep prints nothing; no plugins diff; ruff clean; pytest 243 passed, 1 failed (test_helper_renders_canonical_decision_tree, as on master). Box: no spike-* sessions; scratch dir, transcripts, the scratch trust entry and the spike thread name remain as the task allows. Next: create the zmx-peer-chat plugin task from the doc's 'Distilled for ralph-task' section (ralph-task).
<!-- SECTION:NOTES:END -->
