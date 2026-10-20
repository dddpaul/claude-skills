---
id: TASK-51
title: 'zmx-peer-chat plugin: box-local Claude-Codex peer chat'
status: To Do
assignee: []
created_date: '2026-10-20 08:38'
updated_date: '2026-10-20 08:45'
labels: []
dependencies: []
priority: medium
ordinal: 51000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

A Claude Code and Codex pair that runs on a remote Linux box, each agent in its own zmx session, cannot use the Mac's agterm-based `peer-chat` skill: its transport drives agterm's control socket, which exists only on the Mac. TASK-49's spike (`design/zmx-peer-chat-spike.md`) found by experiment which box-local delivery paths work. This task builds the `zmx-peer-chat` plugin from those findings, so the two agents can message each other on the box without agterm and without any connection back to the Mac.

The spike's distilled contract follows verbatim, then decisions carried from the design discussion before the spike, then additions from the review of the spike's results. The additions are part of the contract, and this task's acceptance criteria supersede the "Acceptance criteria sketch" inside the distilled block.

## Distilled for ralph-task

### Direction

Build a `zmx-peer-chat` plugin in this repo that lets a Claude Code session and a Codex session on the same Linux box, each in its own zmx session started by the box launcher, send each other messages without agterm and without any connection to the Mac.

### Locked decisions

| Decision | Rationale |
|----------|-----------|
| Claude to Codex goes through `codex queue --thread <UUID>` | Delivered to the idle and the busy TUI in the spike, through the daemon's queue, with no typing and no screen reading. |
| The UUID comes from the daemon: the id that appears in `thread/loaded/list` after the start and was not there before, with `thread/read` confirming its `cwd`; stored as a zmx label | A fresh TUI writes no rollout or index line before its first turn, and `codex queue` cannot resolve a name until then. `createdAt` is no start time (it read the time of the first `thread/read`), and a thread from an exited TUI stays loaded, so `cwd` alone cannot pick the new thread. |
| The sender refuses to queue when the Codex zmx session is gone | The daemon keeps the thread loaded after the TUI exits and runs a queued message headless. |
| Codex to Claude goes only through the mailbox and Claude's background wait | Already decided upstream; the spike confirmed it wakes Claude in both Happy modes and that a typed space in remote mode arms a mode switch. |
| Claude needs a running wait in each Happy mode, restarted after every mode switch | Each switch replaces the `claude` process and kills the wait; how the restart is triggered is open (see open risks). |
| The wait command takes no shell variable | In local manual mode `$PPID` triggers a "simple_expansion" approval on every start, which no allow rule can pre-approve. |
| Pairing labels are read before any attach | `zmx attach --labels` overwrites the labels of an existing session. |
| Linux `stat -c %Y` in the mailbox script | The Mac script's `stat -f %m` is BSD-only. |
| Codex packaging is part of the plugin task: a Codex catalog for this repo, `codex plugin marketplace add`, and skill discovery by Codex | TASK-49 assigned it to the plugin task; the spike did not test it, so the plugin task has to establish how Codex finds the Codex skill. |

### Scope cuts

- No `zmx send` typing path for either direction (not needed for Codex, forbidden for Claude).
- No agterm, no `agtermctl`, no socket forwarding, nothing that connects back to the Mac.
- No changes to the box's launcher or provisioning; the plugin ships its own scripts.

### Open risks

- Nothing restarts Claude's wait after a Happy mode switch. In the spike both restarts were asked for by a person (from the app in remote mode, typed into the pane in local mode). The plugin task has to design the trigger, for example a SessionStart hook if Happy's switch fires one, or the router noticing `waiting: no` and telling the person through a channel that does not type into Claude's pane (a terminal notification or the Happy app), who then asks Claude to restart it; neither was tested.
- Whether a wait restart asks for an approval in remote mode was not recorded.
- How long the Codex daemon keeps a thread loaded after its TUI exits is unknown; the sender's liveness check must not depend on it.

### Acceptance criteria sketch

1. A launcher script records the Codex thread UUID on the Codex zmx session (label) within 10 seconds of starting it, demonstrated on the box.
2. `send --to codex` queues by UUID and prints `queued`; on a Codex whose zmx session is gone it exits non-zero and queues nothing.
3. `send --to claude` drops a mailbox file and prints `delivered` when a wait runs, `queued` otherwise.
4. The Claude skill starts the wait without an approval prompt in local manual mode (no shell variable in the command, covered by one allow rule), and a wait is running again after a Happy mode switch in each direction without a person asking for it, demonstrated on the box.
5. The mailbox collect is guarded by a lock so two waits cannot both take the same message.
6. Tests cover the label read-before-attach rule, the UUID pick from the before/after difference of loaded thread ids with a matching `cwd`, the refusal on a dead session, and the mailbox lock; `uv run ruff check .` passes and `uv run pytest` has no failures other than `test_helper_renders_canonical_decision_tree`, which already fails on master.

### Implementation checklist

- [ ] Port `peer-mail.sh` (Linux `stat`, owner found from the process tree, collector lock).
- [ ] Daemon client for `thread/loaded/list`, `thread/read` and `thread/name/set` over `codex app-server proxy` (WebSocket framing, stdlib only).
- [ ] Launcher wrapper: read labels, list the loaded thread ids, start the session, take the new id with a matching `cwd`, record it as a label, name the thread.
- [ ] Router `send`: liveness check via `zmx ls`/`zmx get`, `codex queue` for Codex, mailbox for Claude, `queued`/`delivered` reporting.
- [ ] Claude skill: start the wait at session start; a trigger that restarts it after a mode switch; never type into a pane.
- [ ] Codex skill: how Codex sends to Claude through the router, and its packaging for Codex (catalog, `codex plugin marketplace add`, discovery), which the spike did not test.
- [ ] Tests, README entry, plugin manifest, Claude marketplace entry (`.claude-plugin/marketplace.json`).

## Decisions carried from the design discussion (do not reopen)

- Everything stays on the box: no agterm socket forwarding, no `agtermctl` shim, nothing that connects back to the Mac.
- Pairing uses zmx labels: a pair id derived from the canonical full directory, never its basename (`/a/foo` and `/b/foo` collide under the box launcher's current session naming), an explicit pair id option for several pairs in one directory, and a random incarnation id set when the session is created. Zero or several matching sessions: refuse, never pick the first.
- Every message carries a protocol version; both sides refuse a mismatch.
- Mail addressed to an earlier incarnation is quarantined and reported, never silently consumed or discarded.
- The mailbox is private to the login uid, written atomically, and collected under a single lock.
- Ownership: this repo owns the transport, both SKILL.md files, an example Codex rules fragment (`prefix_rule` lines that allow the router's send commands), the label and protocol contract, and the tests. The provisioning repo later wires the box's `agent` launcher to a register helper shipped here, merges the Codex rules and installs the plugin. So the plugin ships a register helper with a documented CLI and exit codes, and documents the contract the launcher implements against.

## Additions from the review of the spike

1. **A candidate trigger for restarting Claude's wait.** Claude Code hooks accept `asyncRewake`. The hook schema in the binary describes it as: "If true, hook runs in background and wakes the model on exit code 2 (blocking error). Implies async." The string is present in claude-code 2.1.280 on the box and in the SDK claude that happy-coder 1.1.9 bundles; it has not been tried. A plugin `SessionStart` hook with `asyncRewake: true` that runs the mailbox wait would start in every new `claude` process, including the one Happy spawns on each mode switch, and would need no Bash approval. Unverified:
   - whether the SDK-run claude in Happy's remote mode loads plugin hooks;
   - whether a rewake reaches an idle session in remote mode;
   - how the wait re-arms after each message (for example a `Stop` hook with `asyncRewake`).

   Test this first. If no mechanism makes the restart criterion pass, stop and ask the user. Do not weaken the criterion.
2. **Remote mode runs a different Claude.** In remote mode happy-coder 1.1.9 runs its bundled `@anthropic-ai/claude-agent-sdk-linux-x64/claude`, version 2.1.141. Local mode runs the box's claude-code 2.1.280. Everything on the Claude side must work in both.
3. **Codex thread switch.** `/new` or `/resume` in the Codex TUI keeps the zmx session alive but moves the TUI to another thread. The old thread stays loaded in the app-server daemon, and a message queued to it would run headless, shell commands included. A live zmx session is therefore not enough. Find a way to tell which thread the TUI shows, for example:
   - the daemon's thread status or subscriptions;
   - the thread name in the TUI footer, read with `zmx history`;
   - the newest rollout for the session directory.

   Never start a turn on a thread that no TUI shows.
4. **Concurrent start.** Two Codex sessions started at the same time in the same directory make the before/after difference of loaded thread ids ambiguous. The register helper refuses: non-zero exit and no label.
5. **App-server fragility.** `thread/loaded/list`, `thread/read` and `thread/name/set` over `codex app-server proxy` are an internal, undocumented JSON-RPC-over-WebSocket API of codex-cli 0.163.0. The client fails closed on any unexpected handshake or response, and the plugin records the codex-cli version it was tested with, so the provisioning repo's update step can smoke-test it after a Codex upgrade.
6. **Never `happy --version` or a bare `happy`** in scripts, hooks or checks. Both start a session, and without `HAPPY_SERVER_URL` they contact happy's public default server with the machine's credentials. `happy doctor` is safe: it prints the server URL and sends nothing.

## How to run it

- Interactive only: Ralph's devcontainer has no ssh access to the box.
- The box: Linux (WSL2 Ubuntu 24.04), reached with `ssh agentbox` from the Mac. The `agent <dir> [claude|codex|shell] [-n NAME]` launcher in `/usr/local/bin` starts a tool in a zmx session; claude runs under Happy.
- Ask the user for an explicit OK before starting any Claude or Codex session on the box (it spends their quota). Happy mode switches need the user to act from the Happy phone app.
- Use only throwaway zmx sessions with a recognisable prefix in a scratch directory. Never type into, queue to or kill the user's own sessions (`zmx ls` shows them). Kill the throwaway sessions at the end, and leave the transcripts.
- Get the plugin onto the box by copying the working tree into the scratch directory over ssh; do not push to GitHub for it. For the demonstrations, install it from that copy temporarily: for Claude at project scope inside the scratch directory where that works, for Codex with `codex plugin marketplace add <scratch copy>`. Remove every such install at the end and record the install and removal commands in `design/zmx-peer-chat.md`.
- This repo is public: docs and tests carry no IP address, host name, user name, home path, token or conversation text. Use placeholders as the spike doc does.

## Scope

In scope:
- The plugin (Claude skill, Codex skill, scripts, hooks, tests), its manifest, its marketplace entry and its README entry.
- The contract doc and the box demonstrations required by the acceptance criteria.
- An example Codex rules fragment shipped with the plugin.

Out of scope:
- Any lasting change to the box's launcher, provisioning, config or installed plugins: the provisioning repo does that in a later task. The temporary demonstration installs described under "How to run it" are allowed and removed at the end.
- Typing into either agent's pane (`zmx send`) for message delivery.
- agterm, `agtermctl`, socket forwarding.
- Changes to other plugins.

## Files

- `design/zmx-peer-chat-spike.md` (exists) - the spike's evidence; read it in full.
- `.claude-plugin/marketplace.json` (exists) - gets the plugin's entry.
- `README.md` (exists) - gets the plugin's entry.
- `plugins/zmx-peer-chat/` (to-create) - `.claude-plugin/plugin.json`, the Claude and Codex skills, scripts (router, mailbox, register helper, daemon client), hooks and tests, following the existing `plugins/<domain>/skills/<name>/{scripts,tests}` layout.
- `design/zmx-peer-chat.md` (to-create) - the contract (label keys, register helper CLI and exit codes, protocol version, mailbox layout) and the box demonstrations.
- Mac reference implementation, read-only and outside this repo: `~/.config/agterm/scripts/peer-chat-route.sh`, `peer-mail.sh`, `peer-chat.py`, `~/.claude/skills/peer-chat/SKILL.md`, `~/.codex/skills/peer-chat/SKILL.md`, `~/.codex/rules/default.rules`.
- `~/Private/Projects/mycloud/ansible/roles/agentbox/README.md` (exists, outside this repo, read-only) - the box, the `agent` launcher and zmx sessions ("Agents in zmx sessions").

## Source

Source: ~/Private/Projects/mycloud@c15c84b40276

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
- [ ] #1 On the box, the plugin's register helper records the Codex thread UUID as a label on the Codex zmx session within 10 seconds of start, shown with zmx get; command and output recorded in design/zmx-peer-chat.md
- [ ] #2 On the box, send --to codex queues by UUID and prints queued; with the Codex zmx session gone it exits non-zero and queues nothing; recorded in design/zmx-peer-chat.md
- [ ] #3 On the box, after /new and after /resume in the Codex TUI, send --to codex never starts a turn on a thread that no TUI shows (it refuses, or re-binds to the shown thread); commands and observed behaviour recorded in design/zmx-peer-chat.md
- [ ] #4 send --to claude drops a mailbox file and prints delivered when a wait runs and queued otherwise
- [ ] #5 On the box, the Claude-side wait starts without an approval prompt in Claude Code's local manual mode (no shell variable in the command; one allow rule or a hook covers it); recorded in design/zmx-peer-chat.md
- [ ] #6 On the box, after a Happy mode switch to remote and another back to local, a wait is running again in each mode without a person asking for it (remote mode runs happy-coder's bundled SDK claude 2.1.141); commands and output recorded in design/zmx-peer-chat.md
- [ ] #7 On the box, with the plugin installed from the scratch copy through codex plugin marketplace add (or a fallback documented in the plugin README), codex plugin list shows the plugin and skills/list for the scratch directory, sent through the plugin's daemon client, lists the plugin's Codex skill; commands and output recorded in design/zmx-peer-chat.md
- [ ] #8 Tests cover label read-before-attach, the UUID pick (before/after difference of loaded thread ids with a matching cwd), refusal on zero or several candidates, refusal on a dead Codex session, the mailbox lock, protocol-version mismatch, quarantine of earlier-incarnation mail, and fail-closed handling of an unexpected daemon response; uv run ruff check . passes and uv run pytest has no failures other than test_helper_renders_canonical_decision_tree
- [ ] #9 plugins/zmx-peer-chat/.claude-plugin/plugin.json exists with version 0.1.0, the plugin ships an example Codex rules file whose prefix_rule lines allow the router's send commands, .claude-plugin/marketplace.json and README.md list the plugin, and design/zmx-peer-chat.md documents the label keys, the register helper's CLI and exit codes, the protocol version, the mailbox layout and the codex-cli version the daemon client was tested with
- [ ] #10 grep -rnE '([0-9]{1,3}\.){3}[0-9]{1,3}|/home/[a-z]|/Users/[a-z]' design/zmx-peer-chat.md plugins/zmx-peer-chat prints nothing
- [ ] #11 At the end, ssh agentbox zmx ls lists none of the throwaway sessions and the temporary Claude and Codex plugin installs on the box are removed; the removal commands and a listing after them are recorded in design/zmx-peer-chat.md
<!-- AC:END -->
