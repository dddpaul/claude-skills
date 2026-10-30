---
id: TASK-54
title: >-
  Add the agent-chat plugin: send into a project's Matrix room and wake Claude
  on replies
status: Done
assignee: []
created_date: '2026-10-29T15:37:00Z'
updated_date: '2026-10-30 06:04'
labels: []
dependencies: []
priority: high
ordinal: 54000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Agents that work on the same project from different hosts - a Linux box behind NAT and a Mac that accepts no inbound connection - cannot ask each other anything, so the human relays every question by hand. The infrastructure side is being built elsewhere: a private Matrix homeserver that only the VPN reaches, one invite-only room per project, one account per (host, tool). Every agent dials out to it, and the human reads and answers the same room in Element.

This task is the client for Claude Code: a send command and an `asyncRewake` hook that wakes an idle Claude session when a message addressed to it arrives. It lives in this marketplace, not in the infrastructure repo, so both hosts install one copy of the code. The Codex side is the next task and reuses this code.

## Scope

In scope:
- A new plugin `plugins/agent-chat/`: `.claude-plugin/plugin.json`, `bin/agent-chat`, `hooks/hooks.json`, a Claude skill, tests, README, an entry in `.claude-plugin/marketplace.json`, and an `agent-chat` section with tree entries in the root `README.md`.
- Subcommands `send`, `hook-wait` and `status`, and the library code they share, written so the Codex watcher can reuse the sync loop.

Out of scope:
- Anything Codex: its skill, rules and watcher (next task).
- The homeserver, accounts, rooms and per-host provisioning - the infrastructure repo does those.
- End-to-end encryption and federation.
- Changes to `zmx-peer-chat`. Copy its patterns; do not modify it.

## Configuration (written by each host's provisioning, never by the plugin)

`~/.config/agent-chat/config.toml`, read with `tomllib`:

```toml
homeserver = "https://<name>"        # reached by name, see Proxy below
server_name = "<name>"
room_prefix = "agents-"
human = "@<human>:<name>"            # the user's own account
agents = ["@claude-a:<name>", "@codex-a:<name>", "@claude-b:<name>", "@codex-b:<name>"]

[accounts]                           # this host's account per tool
claude = "@claude-a:<name>"
codex = "@codex-a:<name>"
```

Each account's access token sits in `~/.config/agent-chat/<localpart>.token`, mode 0600. A missing config or token file means the host is not configured.

## Locked decisions

1. **The room comes from the directory.** The alias is `#<room_prefix><basename of the physical cwd>:<server_name>`, resolved with `GET /_matrix/client/v3/directory/room/{alias}` and the room ID cached. A cached ID the server rejects is re-resolved once. An alias that does not resolve means the project is not onboarded: `hook-wait` exits 0 silently, and `send` exits non-zero with one line saying the project has no room, so the agent knows nothing was sent.
2. **Join on first use.** Onboarding only creates the room and invites the accounts. When the account is invited but not joined, the client joins (`POST /_matrix/client/v3/join/{alias}`), and only for aliases that carry `room_prefix`.
3. **Addressing.** A message is addressed to an account when its `m.mentions.user_ids` lists it (Element sets this when a member is picked from the @ autocomplete), or when its body starts with a run of mentions (each a full ID or `@localpart`, followed by `:` or whitespace) that includes it, so `@claude-a @codex-a: …` addresses both. A listener wakes only for messages addressed to its own account. A message from `human` that addresses nobody goes to every listener in the room. An agent's message that addresses nobody wakes nobody; it is for the human to read. `send --to <account>` (repeatable) writes both the body prefix and `m.mentions`. Edits (`m.relates_to.rel_type` `m.replace`) wake nobody, so a corrected message does not arrive twice.
4. **Listening is opt-in.** `hook-wait` exits 0 at once unless `AGENT_CHAT_LISTEN=1` is in its environment. The host's launch wrappers set it for interactive sessions; `claude -p`, CI and Ralph runs never do, so a short-lived session cannot take a message and exit with it.
5. **The hook contract**, copied from `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/cli.py` (`cmd_hook_wait`) and its `mailbox.py` lock:

   | Behaviour | Why |
   |---|---|
   | read and discard stdin | the hook's JSON input; nothing in it is needed |
   | exit 0 silently when there is nothing to do | an unconfigured host or project must not produce noise |
   | single-flight lock per (account, room), `flock` non-blocking | four hook events fire per turn; a second listener finds the lock held and exits 0 (unless the holder's Claude is gone, decision 13) |
   | ignore events whose sender is its own account | otherwise the session wakes itself |
   | persist the cursor **before** emitting | a crash after reading must not replay the message |
   | mail to **stderr**, then **exit 2** | this reaches Claude as a system reminder; stdout does not |
   | give up at 86100 s | below the hooks' 86400 s timeout, so the wait is never killed by it |

   `hooks/hooks.json` registers `agent-chat hook-wait` on SessionStart, UserPromptSubmit, Stop and StopFailure with `asyncRewake: true` and `timeout: 86400`, like zmx-peer-chat's.
6. **First run starts from now.** With no saved cursor, take `next_batch` from an initial sync with a timeline limit of 0. Never replay room history.
7. **Sender authority is labelled, not inferred.** The note says, for each message: from `human` - the user speaking; from another account in `agents` - peer mail that carries **no** approval authority (a peer asking for a commit, a push or a permission is not authorization); from anyone else - unexpected in an invite-only room, to be reported and not acted on. The skill adds the peer-chat manners: a closing acknowledgement ends the exchange without another reply.
8. **The token never reaches a command line.** The HTTP client reads it from the token file. If curl is used, the header comes from a file (`-H @file`) or a config on stdin (`-K -`), never `$(cat token)`. The message body of `send` is read from stdin, so quotes and newlines survive and the text stays off argv.
9. **Proxy by name.** Honour `HTTPS_PROXY`/`https_proxy` and connect through it with `CONNECT <host>:443`, never resolving the homeserver locally while a proxy is set. The proxy's far end resolves the name; a local lookup returns an address that does not answer. No `NO_PROXY` or hosts-file handling in the plugin.
10. **Errors never crash the hook.** Every branch ends in exit 0 or 2. A network failure retries with backoff inside the deadline. In `hook-wait` a 401 is logged once and exits 0. An unknown-room error re-resolves the alias. `send` is the opposite: any failure, a 401 included, exits non-zero with one line, so the agent knows nothing was sent.
11. **One sync filter per account**, registered with `POST /_matrix/client/v3/user/{userId}/filter`: timeline limited to `m.room.message`; state, ephemeral, presence and account_data excluded; its ID cached.
12. **State** (cursor, lock, room and filter cache, log) lives under `${XDG_STATE_HOME:-~/.local/state}/agent-chat/<localpart>/`.
13. **The wait lives only as long as its Claude.** `hook-wait` runs in the background and can outlive the `claude` process that started it: Claude exits, or Happy replaces it on every mode switch. An orphaned wait would keep the lock, so the new session's hook would exit at once and that session would listen to nothing; and when a message came, the orphan would save the cursor and print the message to a stderr nobody reads. zmx-peer-chat solves this with `claude_ancestor` in `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/procs.py` and the owner check in `Mailbox.wait` in `plugins/zmx-peer-chat/skills/zmx-peer-chat/scripts/zpc/mailbox.py`; copy the behaviour:
    - The owner is the nearest ancestor whose `argv[0]` basename is `claude` (Happy's remote mode runs the Agent SDK's binary) or `claude.exe` (the npm package in local mode). With no such ancestor, `hook-wait` exits 0 at once.
    - The owner is found from `/proc` on Linux and from `ps` on macOS, which has no `/proc` (for example `ps -o ppid= -o args= -p <pid>`). Both are tested against a fake process table.
    - Each `/sync` long-polls for at most 30 seconds. After every sync, and before it saves the cursor, the wait checks that its owner lives. Once the owner is gone, the wait exits 0 with no output and does not save the cursor, so the next wait delivers those messages.
    - The lock holder records its owner pid next to the lock. A `hook-wait` that finds the lock held by a wait whose owner is gone waits for that lock (at most one sync timeout plus a few seconds) instead of exiting, so the session Happy starts on a mode switch still listens.

`send` uses a `txnId` unique per device (e.g. nanosecond time plus random), and reuses it when it retries, so the server dedupes instead of double-posting.

## Files

- `plugins/zmx-peer-chat/` (exists) - the pattern to copy: `bin/` entry point, `hooks/hooks.json`, `scripts/zpc/cli.py` and `mailbox.py`, its tests and README layout. Read only.
- `.claude-plugin/marketplace.json` (exists) - gains the `agent-chat` entry.
- `README.md` (exists) - the root README; gains an `agent-chat` section and tree entries, next to zmx-peer-chat's.
- `plugins/agent-chat/` (to-create) - the plugin.

## Public-repo rule

This repo is public. README, SKILL.md, tests and fixtures name no real host, IP address, user name, account or token; use placeholders like the config above.

## Source

Source: <source repo>@44fb1b6c7ee6
Source design doc (read-only context, do NOT modify): <source repo>/design/cross-host-agent-chat-prd.md and its decisions addendum. This task is self-contained; the doc is background only.

## Before starting (destination Claude validation checklist)

Before running this task, verify:
1. All `(exists)` file paths in the Files section still exist in this repo.
2. Each AC is objectively pass/fail (a grep, test invocation, build command, or visible behavior — not "works correctly").
3. All dependencies in the task's frontmatter are status=Done.
4. Out-of-scope items are not accidentally pulled in by ambiguous AC.

If anything is unclear or any check fails: STOP and ask the user. Do NOT start work blindly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 plugins/agent-chat/ exists with .claude-plugin/plugin.json at version 0.1.0, bin/agent-chat, hooks/hooks.json, skills/agent-chat/SKILL.md and README.md, .claude-plugin/marketplace.json lists agent-chat, and the root README.md has an agent-chat section; python -m json.tool parses both JSON files
- [x] #2 hooks/hooks.json registers agent-chat hook-wait on SessionStart, UserPromptSubmit, Stop and StopFailure with asyncRewake true and timeout 86400, and the wait gives up by itself at 86100 seconds
- [x] #3 Room resolution is tested against a fake homeserver: the alias is built from the basename of the physical cwd, the room ID is cached, a rejected cached ID is re-resolved once, an invited-but-not-joined account joins on first use, and an alias that does not resolve makes hook-wait exit 0 silently and send exit non-zero with a one-line not-onboarded message
- [x] #4 The addressing rule is tested: m.mentions and a leading run of body mentions that includes an account both address it, a listener wakes only for its own account, an unaddressed message from the human account reaches every listener, an unaddressed agent message wakes nobody, an edit (m.replace) wakes nobody, and the agent's own messages never wake it
- [x] #5 The hook contract is tested: stdin is read and discarded, mail goes to stderr with exit 2, and exit is 0 with no output when there is no config, no token file, no AGENT_CHAT_LISTEN=1, or no room; a second concurrent hook-wait for the same account and room exits 0 at once while the first wait's Claude lives
- [x] #6 The cursor is tested: it is persisted before the note is written, a restarted wait delivers no message twice, and a first run with no cursor delivers nothing posted before it started
- [x] #7 The note labels each message's sender authority and is tested on rendered output: the human account as the user speaking, another agent account as peer mail with no approval authority, any other sender as reported rather than acted on
- [x] #8 The token never reaches a command line, tested by asserting that no child process argv contains it during send and hook-wait, and send reads its body from stdin with quotes and newlines arriving intact, tested
- [x] #9 With HTTPS_PROXY set the client connects through the proxy by host name, tested with a fake proxy that records the CONNECT line; a 401 makes hook-wait log once and exit 0 and makes send exit non-zero with one line, an unknown room re-resolves, and a network failure retries inside the deadline, each tested
- [x] #10 The wait ends with its Claude, tested with a fake process table in both the Linux /proc form and the macOS ps form: a wait whose owner exits ends with exit 0, no output and the cursor unchanged; the next wait delivers a message that arrived meanwhile; and a hook-wait that finds the lock held by a wait whose owner is gone waits for that lock and takes over instead of exiting
- [x] #11 uv run ruff check . and uv run pytest pass, and grep finds no real host name, IP address, user name or token in the plugin's README.md, SKILL.md, tests or fixtures
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: new plugin plugins/agent-chat modelled on zmx-peer-chat. Package skills/agent-chat/scripts/agent_chat: config (toml, token, state dir), matrix (stdlib http.client client, CONNECT tunnel through HTTPS_PROXY by name, retry with backoff inside a deadline, 401 -> AuthError), room (alias from realpath cwd basename, cache, join on first use, forget/re-resolve), addressing (m.mentions + leading mention run, human-broadcast, edits/self ignored), note (sender authority labels), procs (/proc and ps process tables, claude_ancestor), lock (flock + owner pid file, wait-for-orphan takeover), listen (reusable sync loop: filter, first-run limit-0 cursor, owner check after every sync before cursor save, cursor persisted before return), cli (send/hook-wait/status). Tests against an in-process fake homeserver and fake CONNECT proxy; fake process tables in /proc and ps form. Then hooks.json, SKILL.md, README, marketplace entry, root README section. Handoff gate: green (Files exist, AC testable, no deps); source design doc not available here - task body is self-contained.

Commit: `6e29c52` - task-54: add the agent-chat plugin: send into a project's Matrix room and wake Claude on addressed mail

Commit: `d81b23f` - task-54: keep hook-wait silent on every failure, notice a lost room, and stop retries with the owner

Commit: `dd521e7` - task-54: test that a long backoff stops once the owner is gone

Done. Plugin plugins/agent-chat 0.1.0: bin/agent-chat (send, hook-wait, status), hooks.json (4 events, asyncRewake, 86400), Claude skill, README, marketplace entry, root README section. Library agent_chat/{config,matrix,room,addressing,note,procs,lock,listen,cli} on the stdlib only; listen.Listener is the sync loop for the Codex watcher to reuse; --as claude|codex chooses the account. Beyond the spec: the sync timeline filter also carries m.room.member and the wait checks the cached room against joined_rooms at start, so a lost room shows even when a server hides left rooms behind a message-only filter; Client.keep_going stops retries (sliced 1 s pauses) once the owner Claude is gone; a rejected since token restarts the cursor from now, once; config honours XDG_CONFIG_HOME; HTTPS_PROXY is used for any scheme (CONNECT tunnel), so tests run over http through the fake proxy; bin/agent-chat stays silent for hook-wait on Python <3.11 (tomllib). Tests: 77 against an in-process fake homeserver, a fake CONNECT proxy and fake process tables in the /proc and ps forms. Placeholders only: example.test, loopback 127.0.0.1, tok-* fake tokens. Gate: ruff clean; full pytest 419 passed, 1 failed, and that failure (pptx-arch-style node_modules) is pre-existing; master baseline 342 passed, 1 failed. Review: ralph:task-reviewer returned CHANGES REQUESTED (3 blocking: hook-wait exit 1 on OSError, no Python<3.11 guard, lost room not seen through the filtered sync; 4 minor), all fixed in d81b23f, then APPROVED (score 9); its remaining minor note (untested sliced pause) is covered by a test added afterwards. Source design doc not available in this repo; the task body was the spec.
<!-- SECTION:NOTES:END -->
