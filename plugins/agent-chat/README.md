# agent-chat

Agents that work on the same project from different hosts talk through the project's room on a private Matrix homeserver that only the VPN reaches. Every agent dials out to the homeserver, so a host behind NAT and a host that accepts no inbound connection both take part, and the user reads and answers the same room in Element.

This plugin is the client for Claude Code and for Codex. Claude sends with `agent-chat send`, and a background wait run by the plugin's hooks wakes an idle interactive Claude session when a message addressed to its account arrives. Codex sends in two steps through a prepared message file, and `agent-chat watch-codex`, a long-running process, queues each message addressed to the Codex account to a Codex thread with `codex queue`. The homeserver, the accounts, the rooms and each host's config come from provisioning elsewhere; the plugin only reads them.

## agent-chat or zmx-peer-chat?

Both plugins let Claude and Codex talk; they differ in who can take part and how a message travels.

| | zmx-peer-chat | agent-chat |
|---|---|---|
| Who talks | Exactly one Claude and one Codex in the same project directory on one box, each in its own zmx session | Agents on any host, and the user |
| Transport | Local only: `codex queue` to Codex, a file mailbox to Claude | The project's room on a private Matrix homeserver |
| Identity and addressing | zmx labels set by `register` (`zpc.pair`, `zpc.role`, `zpc.inc`, `zpc.thread`); the one peer of the pair | One Matrix account per agent and host; `@name` mentions; an unaddressed top-level message from the user wakes every listener, one in a thread only the thread's agents |
| History | None; mail is consumed | The room keeps it; the user reads and answers in Element |
| Codex API | `codex queue` to send; the app-server daemon (internal) only to bind the thread at registration and for `daemon check` and `daemon skills` | `codex queue` only |

**The dependency runs one way.** In all-rooms mode, agent-chat's `watch-codex` finds the Codex thread through zmx-peer-chat's labels: the `zpc.role=codex` session whose `cwd` names the directory in the room's alias, then its `zpc.thread` and `zpc.inc`. A Codex session that `register` did not bind gets neither peer mail nor room mail. `watch-codex --thread <uuid>` reads no labels and needs no zmx-peer-chat. zmx-peer-chat knows nothing about agent-chat.

**The footer rule is shared.** Before they queue to a registered Codex session, zmx-peer-chat's `send` and `watch-codex` in all-rooms mode both refuse unless one of the last six non-empty lines of its TUI ends with `· zpc-<inc>`; `watch-codex --thread <uuid>` checks no screen. agent-chat keeps its own copy of the rule because the plugins ship separately, so a change to the Codex footer must update both copies, in both plugins together.

## Configuration

Provisioning writes `~/.config/agent-chat/config.toml` (or under `$XDG_CONFIG_HOME`):

```toml
homeserver = "https://matrix.example.test"
server_name = "example.test"
room_prefix = "agents-"
human = "@human:example.test"
agents = ["@claude-a:example.test", "@codex-a:example.test", "@claude-b:example.test", "@codex-b:example.test"]

[accounts]
claude = "@claude-a:example.test"
codex = "@codex-a:example.test"
```

Each account's access token sits in `~/.config/agent-chat/<localpart>.token`, mode 0600. A missing config or token file means the host is not configured: `hook-wait` exits silently and `send` refuses with one line. The token is read by the client and goes only into the Authorization header, never onto a command line.

With `HTTPS_PROXY` (or `https_proxy`) set, every request goes through the proxy as `CONNECT <host>:<port>` and the homeserver's name is never resolved locally. The plugin does no `NO_PROXY` or hosts-file handling.

## How it works

| Piece | Behaviour |
|-------|-----------|
| Room | `#<room_prefix><basename of the physical cwd>:<server_name>`, resolved through the room directory and cached. A cached ID the server rejects, or a room the account has left, is resolved again once; the sync filter carries membership events so a lost room shows. An invited account joins on first use, and only rooms whose alias carries `room_prefix`. An alias that does not resolve means the project is not onboarded. |
| Addressing | A message addresses an account when its `m.mentions` lists it, or when its body opens with a run of mentions (`@claude-a @codex-a: …`) that includes it. An unaddressed top-level message from `human` wakes every listener; an unaddressed message from `human` in a thread wakes the thread's agents (see Threads), or every listener when none is seen or the thread could not be read. An agent's unaddressed message, in a thread too, an edit, a listener's own messages and history from before it joined wake nobody. `send --to` writes both the prefix and `m.mentions`: the prefix names an account on `server_name` by its short `@name` (`@codex-a: …`) and any other account by its full ID; `m.mentions` holds the full IDs. |
| Threads | `send --thread <id>` posts into a Matrix thread. The id is an event ID with or without one leading `$` (`[A-Za-z0-9_-]+` after it; anything else exits 2), and send's output prints IDs without `$`, so an agent never needs to quote one in Bash. `send` fetches the event: a message without `rel_type`, a rich reply included, is the root; a thread child leads to its root, which must itself be such a message, because the homeserver does not check roots. An edit, a reaction or other relation, a redacted or empty event, a non-message and an unknown id are refused. The post carries `rel_type: m.thread`, `is_falling_back: true` and `m.in_reply_to` the thread's latest message (from `/relations/<root>/m.thread/m.room.message`), or the root when it has no replies, so clients without threads show a reply; the mention prefix and `m.mentions` stay. A failed lookup fails the send like any other failure: nothing is posted and a prepared file stays. On receiving, the wait and `watch-codex` look up each thread with mail once per (room, root) per sync batch: `GET /rooms/<room>/event/<root>` and `GET /relations/<root>/m.thread?dir=b&limit=50`; nothing about threads is stored. The thread's agents are the agent accounts among the root's sender, the agents the root mentions and the senders of those newest 50 events; an agent mentioned only in a later reply is not one until it posts, and one seen only before the window no longer counts. All the lookups of a batch share one 10 s budget: each request is tried at most twice and ends by the budget, whether connecting (the proxy tunnel and TLS included), waiting for headers or reading a slow body (the hostname lookup is not bounded), an answer that completes after it counts as failed, a failure is cached for the batch, and a 401 during a lookup ends the wait or the watcher as it does on a sync; that batch's mail is not delivered, because its cursor is already saved. Once the budget is spent or a lookup fails, addressed mail is still delivered, and the user's unaddressed thread message wakes every listener. The note groups mail by thread, in the order of each thread's first mail; within a thread the room's order is kept, across threads it may change. Each thread shows its root, cut to 300 characters with `…`, as history under its sender's authority label, or `started by <me> (this account)` when the listening account wrote it; an account that has not posted in the thread also gets the last 3 replies before its first mail, in the server's order, or a line saying they were left out when that mail is outside the window. Reply hints carry full event IDs without `$`: `reply with --thread <root>` for a thread, `reply with --thread <id>; that opens a thread on it` for top-level mail, and `Thread <root> (could not be read; reply with --thread <root>)` heads the mail of a thread the lookup could not read. |
| Listening | Opt-in: `hook-wait` exits at once unless `AGENT_CHAT_LISTEN=1`. The host's launch wrappers set it for interactive sessions; `claude -p`, CI and Ralph runs must not. |
| The wait | Registered on SessionStart, UserPromptSubmit, Stop and StopFailure with `asyncRewake` and a 24 h timeout; it gives up by itself at 86100 s. One wait per (account, room) under a `flock`; the others exit at once. Mail goes to stderr with exit 2, which reaches Claude as a system reminder; everything else exits 0 silently. |
| Cursor | The first run starts from now (a sync with a timeline limit of 0). The cursor is saved before the mail is written, so nothing is delivered twice. |
| Owner | The wait serves the nearest `claude` / `claude.exe` process above it, found from `/proc` on Linux and from `ps` on macOS. Each sync long-polls for at most 30 s; once the owner is gone the wait exits without saving the cursor, and a new session's wait takes over the lock of such an orphan instead of exiting. |
| Sender authority | The note labels each message: from `human` the user speaking, from another agent account peer mail with no approval authority, from anyone else unexpected and to be reported, not acted on. |
| Errors | `hook-wait` never fails: network failures are retried with backoff inside its deadline and only while its Claude lives, a 401 is logged once and the wait ends. `send` fails loudly: any failure is one line and a non-zero exit. A send retry reuses its transaction ID, so the server never posts it twice. |

The command needs Python 3.11 or later (for `tomllib`); on an older `python3`, `hook-wait` exits 0 silently and the other commands refuse with one line.

State (cursor, lock, room and filter cache, log) lives under `${XDG_STATE_HOME:-~/.local/state}/agent-chat/<localpart>/`.

## Install

### Claude Code

Add this repository's marketplace and install `agent-chat` from it, as the root README's Installation section shows. Claude Code puts the plugin's `bin/` on the Bash tool's `PATH` and loads its hooks. A send is a Bash command, `agent-chat send --to <account>` with the text in a quoted heredoc; to send without a prompt each time, allow it the way the project allows other commands.

### Codex

```sh
codex plugin marketplace add <a clone of this repo>
codex plugin add agent-chat@dddpaul-claude-skills
```

Codex reads `.agents/plugins/marketplace.json`, installs the plugin and lists its skill as `agent-chat:agent-chat`. The Codex manifest points `hooks` at the empty `codex/hooks.json`, so Codex does not load the Claude hooks and a new TUI does not stop at "Hooks need review". Two more steps are needed on each host:

- **PATH.** Codex runs commands in its app-server daemon, with a shell snapshot taken from a login shell, so `agent-chat` must be on the login shell's `PATH`. Link the installed plugin's `bin/agent-chat` (under `~/.codex/plugins/cache/dddpaul-claude-skills/agent-chat/<version>/`) into a directory on that `PATH`.
- **Rules.** Copy `codex/rules/agent-chat.rules` into `~/.codex/rules/`, or merge its lines into `~/.codex/rules/default.rules`. A send reaches the homeserver over the network, which Codex's sandbox does not allow; the rules let exactly `agent-chat prepare-message` and `agent-chat send --as codex --message-file` run outside it without a per-call approval; `--to` and `--thread` come after the file name, so the same rule covers a thread reply. Check them with `codex execpolicy check --rules codex/rules/agent-chat.rules agent-chat prepare-message x.txt`.

Codex sends in two steps, because its prefix rules cannot match a command with a heredoc, stdin, redirection or a substitution:

```sh
agent-chat prepare-message ac-codex-7f3a.txt     # prints the empty file's absolute path
# Codex fills that file with apply_patch
agent-chat send --as codex --message-file ac-codex-7f3a.txt --to claude-b
```

`prepare-message` creates the file with mode 0600 in a private outbox, `/tmp/agent-chat-<uid>/outbox` (mode 0700; `AGENT_CHAT_TMP` replaces the `/tmp/agent-chat-<uid>` part). The outbox lies under `/tmp` because Codex's sandbox can write there and cannot write the state directory. An existing name is refused. `send --message-file` refuses a missing file and anything but a plain file of this user, posts as the `codex` account and removes the file once the homeserver has confirmed the post; after a failure the file stays, so the same send can run again.

### The Codex watcher

Codex has no hook that can block and then hand it a message, so each host runs `agent-chat watch-codex` under a supervisor (a systemd user unit or a launchd agent, which the host's provisioning writes). It runs the same sync loop as Claude's wait, for the `codex` account:

| Mode | Rooms | Thread |
|------|-------|--------|
| `watch-codex --thread <uuid>` | The room of the working directory's project; the account joins it on first use. | Always `<uuid>`. |
| `watch-codex` | Every room the account has joined whose alias carries `room_prefix`. Every 5 minutes it also joins the rooms of registered Codex sessions it was invited to. | From `zmx ls`: the one session labelled `zpc.role=codex` (zmx-peer-chat's launcher registered it) whose `cwd=` names the directory in the room's alias, and its `zpc.thread` label. |

Each batch of mail for one room becomes one `codex queue --thread <id> --message <text>`, or several when the note is too long (see below). The text is the same note Claude gets, grouped by thread with each thread's root and reply hint (see Threads), and its reply line is Codex's: `agent-chat prepare-message <fresh-name>`, fill the file with `apply_patch`, then `agent-chat send --as codex --message-file <fresh-name> --thread <id> --to <sender>`. The watcher checks that it serves a room before it looks up any of its threads, and it makes every lookup of a batch before its first delivery, so neither a room it does not serve nor a slow `codex queue` spends the batch's lookup budget. Each room's alias lookup, for a room not in the room cache, has its own 10 s; when it fails the room's mail in that batch is logged as not delivered and every other room's mail still is. `codex queue` takes the note only as one `--message` argument, which Linux caps at 128 KiB, so a note stays within 100000 UTF-8 bytes: one that is too long drops every thread's earlier replies and left-out line, and if it is still too long, the batch arrives as several notes, each with its own header, holding consecutive whole messages in the room's order. A message too long for a note on its own is cut on a character boundary, and its quoted text is followed by an unquoted line, `[cut by agent-chat: <N> more bytes of this message were left out; it is event <id>. Ask in its thread or tell the user.]`; the Codex skill tells the agent to ask or tell the user, never to guess the rest. Each note is its own `codex queue` call, in order, logged `queued … (part k of n)`; at the first failure the watcher logs `not queued: … (parts k-n of n)` and queues none of the rest. The addressing rule, the own-sender guard and "the first run starts from now" are Claude's. The history a server sends with a newly joined room is skipped. Before it queues to a registered session, `watch-codex` reads that session's screen with `zmx history` and requires one of the last six non-empty lines to end with `· zpc-<inc>` (the session's `zpc.inc` label): the same footer rule zmx-peer-chat's router applies before its own `codex queue`, copied because the plugins ship separately. A TUI that `/new` or `/resume` moved to another thread, or a dialog over the footer, would otherwise leave the mail on a thread nobody watches, which the Codex daemon may run headless. `--thread` mode involves no zmx session and checks no screen; it queues to `<uuid>` as before. When no registered session matches a room, when several do, when the match has no bound thread, when its footer does not show the thread, or when `zmx history` fails, the watcher logs a `not queued: ...` line with the reason and queues nothing; it never queues to any other thread, and it never starts, registers, types into or kills a session.

The cursor is saved before the delivery, so a crash never delivers a message twice, and a failed `codex queue` is logged and not retried. Every delivery, refusal and failure, a failure to start included, is one line in the account's `log` and on stderr; only a bad `--thread` or a missing config or token, found before there is an account to log for, shows on stderr alone. One watcher runs per cursor (`watch-codex.cursor`, or `watch-codex-<room>.cursor` with `--thread`); a second one exits with an error. SIGTERM or SIGINT abandons a sync in progress and lets a delivery in progress finish, then the watcher exits 0. Under systemd, use `KillMode=mixed`, so that SIGTERM reaches only the watcher and not a `codex queue` it is running. A refused token ends the watcher with exit 1; a network outage is retried for as long as it lasts.

A supervisor's `PATH` may lack `codex` or `zmx`: `AGENT_CHAT_CODEX` and `AGENT_CHAT_ZMX` name the binaries. The token never reaches a command line; the message text on `codex queue`'s command line is room content, not a secret.

## Checks

```sh
agent-chat status             # the account, the project room, whether a wait listens
agent-chat status --as codex  # the same for the Codex account, and whether watch-codex runs
uv run pytest plugins/agent-chat
```

The tests run against an in-process fake homeserver, a fake CONNECT proxy, fake process tables in both the `/proc` and the `ps` form, and fake `codex` and `zmx` binaries that record their command lines. When `codex` is installed, they also check the rules with `codex execpolicy check`.
