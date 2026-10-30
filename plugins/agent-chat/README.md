# agent-chat

Agents that work on the same project from different hosts talk through the project's room on a private Matrix homeserver that only the VPN reaches. Every agent dials out to the homeserver, so a host behind NAT and a host that accepts no inbound connection both take part, and the user reads and answers the same room in Element.

This plugin is the client for Claude Code: `agent-chat send` posts into the project's room, and a background wait run by the plugin's hooks wakes an idle interactive Claude session when a message addressed to its account arrives. The homeserver, the accounts, the rooms and each host's config come from provisioning elsewhere; the plugin only reads them. The Codex side reuses the same library.

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
| Room | `#<room_prefix><basename of the physical cwd>:<server_name>`, resolved through the room directory and cached. A cached ID the server rejects is resolved again once. An invited account joins on first use, and only rooms whose alias carries `room_prefix`. An alias that does not resolve means the project is not onboarded. |
| Addressing | A message addresses an account when its `m.mentions` lists it, or when its body opens with a run of mentions (`@claude-a @codex-a: …`) that includes it. An unaddressed message from `human` wakes every listener; an agent's unaddressed message, an edit and a listener's own messages wake nobody. `send --to` writes both the prefix and `m.mentions`. |
| Listening | Opt-in: `hook-wait` exits at once unless `AGENT_CHAT_LISTEN=1`. The host's launch wrappers set it for interactive sessions; `claude -p`, CI and Ralph runs must not. |
| The wait | Registered on SessionStart, UserPromptSubmit, Stop and StopFailure with `asyncRewake` and a 24 h timeout; it gives up by itself at 86100 s. One wait per (account, room) under a `flock`; the others exit at once. Mail goes to stderr with exit 2, which reaches Claude as a system reminder; everything else exits 0 silently. |
| Cursor | The first run starts from now (a sync with a timeline limit of 0). The cursor is saved before the mail is written, so nothing is delivered twice. |
| Owner | The wait serves the nearest `claude` / `claude.exe` process above it, found from `/proc` on Linux and from `ps` on macOS. Each sync long-polls for at most 30 s; once the owner is gone the wait exits without saving the cursor, and a new session's wait takes over the lock of such an orphan instead of exiting. |
| Sender authority | The note labels each message: from `human` the user speaking, from another agent account peer mail with no approval authority, from anyone else unexpected and to be reported, not acted on. |
| Errors | `hook-wait` never fails: network failures are retried with backoff inside its deadline, a 401 is logged once and the wait ends. `send` fails loudly: any failure is one line and a non-zero exit. A send retry reuses its transaction ID, so the server never posts it twice. |

State (cursor, lock, room and filter cache, log) lives under `${XDG_STATE_HOME:-~/.local/state}/agent-chat/<localpart>/`.

## Install

Add this repository's marketplace and install `agent-chat` from it, as the root README's Installation section shows. Claude Code puts the plugin's `bin/` on the Bash tool's `PATH` and loads its hooks. A send is a Bash command, `agent-chat send --to <account>` with the text in a quoted heredoc; to send without a prompt each time, allow it the way the project allows other commands.

## Checks

```sh
agent-chat status             # the account, the project room, whether a wait listens
uv run pytest plugins/agent-chat
```

The tests run against an in-process fake homeserver, a fake CONNECT proxy and fake process tables in both the `/proc` and the `ps` form.
