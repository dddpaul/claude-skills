# zmx-peer-chat

Box-local peer chat between a Claude Code session and a Codex session that run on the same Linux box, each in its own zmx session started by the box launcher. No agterm and no connection back to the Mac: Claude sends with `codex queue` by thread UUID, Codex sends into Claude's private mailbox, and a background wait run by the plugin's hooks wakes Claude when mail arrives.

The contract (labels, the register helper's CLI and exit codes, the protocol version, the mailbox layout, the tested codex-cli version) and the box demonstrations are in `design/zmx-peer-chat.md` at the repo root.

## How a pair comes about

1. The launcher runs `zmx-peer-chat register --role claude|codex --session NAME --dir DIR` just before `zmx attach NAME <tool>` creates a session. The helper labels the new session with `zpc.pair` (from the directory's full path), `zpc.role`, `zpc.inc` and `zpc.proto`; for Codex it also finds the thread the new TUI opened through the local Codex app-server daemon, names it `zpc-<inc>` and stores its UUID as `zpc.thread`. An existing session keeps its labels.
2. Claude's hooks keep a wait running for its session in every `claude` process, including the ones Happy starts on a mode switch.
3. Either side sends with `zmx-peer-chat send`; it finds the one peer with the same pair id and the other role, and refuses when there is none, more than one, or another protocol version.

## Install

### Claude Code

```text
/plugin marketplace add https://github.com/dddpaul/claude-skills
/plugin install zmx-peer-chat@dddpaul-claude-skills
```

Claude Code puts the plugin's `bin/` on the Bash tool's `PATH` and loads its hooks. The wait runs as a hook, so it needs no Bash approval in manual mode. A reply is a Bash command, `zmx-peer-chat send --to codex --stdin` with the text in a quoted heredoc; to send without a prompt each time, allow it the way the project allows other commands.

### Codex

```sh
codex plugin marketplace add <a clone of this repo>
codex plugin add zmx-peer-chat@dddpaul-claude-skills
```

Codex reads `.agents/plugins/marketplace.json`, installs the plugin and lists its skill as `zmx-peer-chat:zmx-peer-chat`. Two more steps are needed on the box:

- **PATH.** Codex runs commands in its app-server daemon, with a shell snapshot taken from a login shell, so `zmx-peer-chat` must be on the login shell's `PATH`; a `PATH` set for the TUI alone does not reach them. Link the installed plugin's `bin/zmx-peer-chat` (under `~/.codex/plugins/cache/dddpaul-claude-skills/zmx-peer-chat/<version>/`) into a directory on that `PATH`.
- **Rules.** Copy `codex/rules/zmx-peer-chat.rules` into `~/.codex/rules/` or merge its lines into `~/.codex/rules/default.rules`. The router talks to zmx and to the mailbox, which Codex's sandbox does not allow; the rules let `status`, `prepare-message` and `send --to claude --message-file` run outside it without a per-call approval.

The Codex manifest points `hooks` at the empty `codex/hooks.json`: otherwise Codex loads the Claude hooks from `hooks/hooks.json` and a new TUI stops at a "Hooks need review" dialog. If plugins are unavailable, copying `codex-skills/zmx-peer-chat/` to `~/.codex/skills/zmx-peer-chat/` gives Codex the skill under its plain name; the `PATH` and rules steps stay the same.

### The launcher

Call the register helper for `claude` and `codex` sessions only, right before the session is created, and start one session per directory at a time. It returns at once and labels the session from a detached child within about two seconds; failures are logged to `register.log` in the mail root (`/tmp/zmx-peer-chat-<uid>`). See the exit codes in `design/zmx-peer-chat.md`.

## Checks

```sh
zmx-peer-chat status          # this session's labels, its peer, whether Claude's wait runs
zmx-peer-chat daemon check    # the codex-cli version against the tested one, and the daemon
uv run pytest plugins/zmx-peer-chat
```
