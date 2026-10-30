# agent-chat

Agents that work on the same project from different hosts talk through the project's room on a private Matrix homeserver that only the VPN reaches. Every agent dials out to the homeserver, so a host behind NAT and a host that accepts no inbound connection both take part, and the user reads and answers the same room in Element.

This plugin is the client for Claude Code and for Codex. Claude sends with `agent-chat send`, and a background wait run by the plugin's hooks wakes an idle interactive Claude session when a message addressed to its account arrives. Codex sends in two steps through a prepared message file, and `agent-chat watch-codex`, a long-running process, queues each message addressed to the Codex account to a Codex thread with `codex queue`. The homeserver, the accounts, the rooms and each host's config come from provisioning elsewhere; the plugin only reads them.

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
| Addressing | A message addresses an account when its `m.mentions` lists it, or when its body opens with a run of mentions (`@claude-a @codex-a: …`) that includes it. An unaddressed message from `human` wakes every listener; an agent's unaddressed message, an edit and a listener's own messages wake nobody. `send --to` writes both the prefix and `m.mentions`. |
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
- **Rules.** Copy `codex/rules/agent-chat.rules` into `~/.codex/rules/`, or merge its lines into `~/.codex/rules/default.rules`. A send reaches the homeserver over the network, which Codex's sandbox does not allow; the rules let exactly `agent-chat prepare-message` and `agent-chat send --as codex --message-file` run outside it without a per-call approval. Check them with `codex execpolicy check --rules codex/rules/agent-chat.rules agent-chat prepare-message x.txt`.

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

Each batch of mail for one room becomes one `codex queue --thread <id> --message <text>`. The text is the same note Claude gets: the sender's authority for each message, and how to reply from Codex. The addressing rule, the own-sender guard and "the first run starts from now" are Claude's. The history a server sends with a newly joined room is skipped. When no registered session matches a room, when several do, or when the match has no bound thread, the watcher logs the reason and queues nothing; it never queues to any other thread, and it never starts, registers, types into or kills a session.

The cursor is saved before the delivery, so a crash never delivers a message twice, and a failed `codex queue` is logged and not retried. Every delivery, refusal and failure is one line in the account's `log` and on stderr. One watcher runs per cursor (`watch-codex.cursor`, or `watch-codex-<room>.cursor` with `--thread`); a second one exits with an error. SIGTERM or SIGINT abandons a sync in progress and lets a delivery in progress finish, then the watcher exits 0. Under systemd, use `KillMode=mixed`, so that SIGTERM reaches only the watcher and not a `codex queue` it is running. A refused token ends the watcher with exit 1; a network outage is retried for as long as it lasts.

A supervisor's `PATH` may lack `codex` or `zmx`: `AGENT_CHAT_CODEX` and `AGENT_CHAT_ZMX` name the binaries. The token never reaches a command line; the message text on `codex queue`'s command line is room content, not a secret.

## Checks

```sh
agent-chat status             # the account, the project room, whether a wait listens
agent-chat status --as codex  # the same for the Codex account
uv run pytest plugins/agent-chat
```

The tests run against an in-process fake homeserver, a fake CONNECT proxy, fake process tables in both the `/proc` and the `ps` form, and fake `codex` and `zmx` binaries that record their command lines. When `codex` is installed, they also check the rules with `codex execpolicy check`.
