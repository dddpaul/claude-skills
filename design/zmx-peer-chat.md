# zmx peer chat: contract and box demonstrations

The `zmx-peer-chat` plugin lets a Claude Code session and a Codex session on the same Linux box, each in its own zmx session started by the box launcher, send each other messages without agterm and without any connection to the Mac. This document is the contract the box's provisioning implements against (labels, the register helper's CLI and exit codes, the protocol version, the mailbox layout, the PATH and rules the Codex side needs) and the record of the TASK-51 demonstrations on the box. The transport choices come from the spike in [[zmx-peer-chat-spike]].

Placeholders: `<box>` is the ssh alias, `<home>` the box user's home, `<uid>` its uid, `<pair-id>` a pair id (a hash of a directory path), `<thread-1>`, `<thread-2>`, … Codex thread UUIDs.

## Architecture

Everything runs on the box under one login uid. The launcher starts each agent in its own zmx session and, just before that, calls the plugin's register helper, which labels the session; two sessions with the same pair id and different roles are a pair. Claude sends with `codex queue`, which the shared Codex app-server daemon runs as the next turn of the bound thread. Codex sends into Claude's private mailbox, where a wait that Claude's plugin hooks keep running in every `claude` process picks the mail up and wakes Claude.

The first diagram shows the pieces, the second the flows. `NAME` is a session's zmx name (the launcher's `-n NAME`, by default `<basename of dir>-<tool>`), `<dir>` the session directory, `P` the pair id, `I1` and `I2` the incarnations, `T` the Codex thread UUID, and `.` in a footer stands for the TUI's middle dot `·`. `[prov]` marks what the provisioning repo sets up, and `(!n)` points at known risk n below.

```text
+----------------------------------- Linux box, one login uid -------------------------------------+
| +-- zmx session NAME, role claude ---------+        +-- zmx session NAME, role codex ----------+ |
| | labels  zpc.pair=P   zpc.role=claude     |        | labels  zpc.pair=P   zpc.role=codex      | |
| |         zpc.inc=I1   zpc.proto=1         |        |         zpc.inc=I2   zpc.proto=1         | |
| |                                          |        |         zpc.thread=T                     | |
| | happy claude                             |        |                                          | |
| |   local mode : claude.exe (claude-code)  |        | codex TUI (a client of the daemon)       | |
| |   remote mode: claude (Agent SDK)        |        |   footer: model . <dir> . zpc-I2  (!1)   | |
| | plugin hooks, asyncRewake:               |        |                                          | |
| |   SessionStart  UserPromptSubmit         |        |                                          | |
| |   Stop  StopFailure                      |        |                                          | |
| |     `-> zmx-peer-chat hook-wait          |        |                                          | |
| |         (background; exit 2 = wake)      |        |                                          | |
| +------------------------------------------+        +------------------------------------------+ |
|   hook-wait waits on                                  shows thread T                             |
|   |                                                   |                                          |
|   v                                                   v                                          |
| +-- mailbox, mode 0700 --------------------+        +-- Codex app-server daemon (shared) ------+ |
| | /tmp/zmx-peer-chat-<uid>/                |        | threads (thread T), turn queue           | |
| |   P/inbox/<ns>-<pid>-<rand>.msg          |        | JSON-RPC via app-server proxy  (!2)      | |
| |   P/quarantine/   P/waiter (heartbeat)   |        | runs Codex's shell commands with         | |
| |   P/waiter.lock   P/collect.lock         |        |   login-shell PATH + link [prov] (!3)    | |
| |   outbox/<name>   register.log           |        |   CODEX_THREAD_ID=T, in the sandbox;     | |
| |                                          |        |   rules [prov] free 3 commands (!3)      | |
| +------------------------------------------+        +------------------------------------------+ |
|                                                                                                  |
| zmx-peer-chat = the plugin's bin/, stdlib Python: register, send, prepare-message,               |
|   status, hook-wait, wait, waiting, collect, daemon check|skills                                 |
| box launcher [prov]: agent <dir> claude|codex -n NAME -> register, then zmx attach (!3)          |
|                                                                                                  |
| [prov] set up by the provisioning repo, not by the plugin     (!n) known risk n, see below       |
+--------------------------------------------------------------------------------------------------+
```

```text
Registration                       (the launcher [prov], just before the session exists)
  launcher   zmx-peer-chat register --role codex --session NAME --dir <dir>
               zmx ls: NAME already exists? -> leave its labels alone, exit 0
               lock <dir>; note the time S; snapshot the loaded threads           (!2)
                 (thread/loaded/list, thread/read)
               fork a detached bind, return at once
  launcher   zmx attach NAME codex            -> the TUI starts or resumes thread T
  bind         wait for NAME to appear in zmx ls
               poll the daemon for the one thread in <dir>: a new id created after S, (!2)
                 or one whose updatedAt moved past S; never one seen running a turn
               thread/name/set T "zpc-I2"     -> the footer shows zpc-I2
               zmx set NAME zpc.pair=P zpc.role=codex zpc.inc=I2 zpc.proto=1 zpc.thread=T

Claude -> Codex
  claude     zmx-peer-chat send --to codex --stdin <<'EOF' ... EOF
               me = $ZMX_SESSION; peer = the one live session with pair P and role codex
               refuse unless proto matches, zpc.thread is a UUID and the footer       (!1)
                 (zmx history NAME) ends with ". zpc-I2"
               codex queue --thread T --message "Chat from Claude: ..."  -> prints "queued"
  daemon     runs it as the next turn of T, which the TUI shows

Codex -> Claude
  codex      zmx-peer-chat prepare-message F       (login PATH, outside the sandbox  (!3))
             apply_patch F                         (outbox/F, mode 0600)
             zmx-peer-chat send --to claude --message-file F
               me = the session whose zpc.thread is $CODEX_THREAD_ID
               write P/inbox/.<msg>.part, rename it to P/inbox/<msg>
                 {proto, pair, inc=I1, text "Chat from Codex: ..."}
               prints "delivered" if Claude's wait runs, else "queued"
  hook-wait  collect under collect.lock -> mail on stderr, exit 2 -> Claude wakes with it
             (mail for another incarnation, protocol or pair -> quarantine, reported)

Claude's wait across a Happy mode switch
  claude (local, claude.exe)    SessionStart        -> hook-wait runs
                                mail arrives        -> exit 2, wake; UserPromptSubmit and Stop
                                                       start the next wait
  switch in the Happy app       old claude exits    -> its wait ends (its owner is gone)
  claude (remote, SDK claude)   SessionStart:resume -> hook-wait runs again; nobody asks
```

### Known risks

1. **Sends to Codex read the Codex TUI's screen.** TASK-51's probes found no daemon call that tells which thread a TUI shows, so before every `codex queue` the router reads the Codex session's screen with `zmx history` and requires the footer to end with `· zpc-<inc>`. A Codex release that changes the footer, or a dialog over it, makes every send to Codex refuse with exit 1 and `nothing was queued`; it never starts a turn on a thread the TUI does not show. After a Codex upgrade, try one send on a live pair.
2. **Registration uses an undocumented Codex API.** The register helper reaches the daemon through `codex app-server proxy` and calls `thread/loaded/list`, `thread/read` and `thread/name/set`, internal JSON-RPC methods of codex-cli; its thread pick also relies on how codex-cli 0.163.0 sets `createdAt` and `updatedAt`. The client fails closed: an unexpected handshake, frame or answer is code 3 (`codex daemon: …`) and sets no label, and a thread it cannot single out is code 4 or 5. Only a failure during the snapshot, before the helper returns, reaches the launcher as an exit code; once the detached bind runs, failures go to `register.log` in the mail root. Run `zmx-peer-chat daemon check` after every Codex upgrade: it exits 1 when the installed codex-cli is not the tested one and 3 when the daemon does not answer as expected. A new version needs a box run of the register demonstrations before the launcher relies on it.
3. **The pair works only after provisioning, and the Codex side needs most of it.** Installing the plugin gives Claude Code the hooks, the skill and `zmx-peer-chat` on its Bash `PATH`, so apart from the register call, which both sides need, the Claude side is self-contained. Three things marked `[prov]` are outside the plugin's reach:
   - Both sides: the launcher must call `zmx-peer-chat register` before it creates each `claude` and `codex` session. Without it the session has no labels, and sends refuse: an unregistered Claude gets `zmx session NAME is not registered with zmx-peer-chat`, a Claude whose Codex is unregistered gets `no codex session is paired with NAME; nothing was sent`, and an unregistered Codex gets `no zmx session is bound to this Codex thread (…)`.
   - Codex: `zmx-peer-chat` must be on the login shell's `PATH`, which the daemon snapshots for Codex's commands. Without it Codex got `zmx-peer-chat: command not found` (exit 127) on the box.
   - Codex: the lines of `codex/rules/zmx-peer-chat.rules` must be in `~/.codex/rules/`. They let exactly three commands run outside Codex's sandbox: `zmx-peer-chat status`, `prepare-message` and `send --to claude --message-file`. Without them those commands run inside it, where `status` failed on the box with `zmx ls failed: error: ReadOnlyFileSystem`; any other form, such as `send --to claude --stdin`, stays inside it even with the rules.

## Versions

Every demonstration ran on 2026-10-20 with these versions, read from `--version` output or package files (never `happy --version`, which starts a session):

| Tool | Version |
|------|---------|
| codex-cli (TUI and app-server daemon) | `codex-cli 0.163.0` (the daemon client's `TESTED_CODEX_CLI`) |
| zmx | `0.8.1` |
| claude-code, local mode | `2.1.280` (transcripts: `entrypoint` `cli`) |
| happy-coder | `1.1.9` |
| Claude in Happy's remote mode | the bundled `@anthropic-ai/claude-agent-sdk-linux-x64` package `0.2.141`, which runs Claude Code `2.1.141` (transcripts: `entrypoint` `remote_mobile`) |
| Python | `3.12.3` (the plugin is stdlib only) |

`zmx-peer-chat daemon check` prints the installed codex-cli version next to the tested one and exits 1 when they differ, so the provisioning repo can smoke-test the daemon client after a Codex upgrade.

## Contract

### What the plugin ships

| Path in `plugins/zmx-peer-chat/` | For | What it is |
|-----------------------------------|-----|------------|
| `bin/zmx-peer-chat` | both | The one command: register helper, router, mailbox, wait, daemon client. Python 3, stdlib only; the code is in `skills/zmx-peer-chat/scripts/zpc/`. |
| `.claude-plugin/plugin.json` | Claude | Manifest, version `0.1.0`. Claude Code puts `bin/` on the Bash tool's `PATH`. |
| `skills/zmx-peer-chat/SKILL.md` | Claude | How Claude receives, replies and refuses. |
| `hooks/hooks.json` | Claude | `SessionStart`, `UserPromptSubmit`, `Stop` and `StopFailure` hooks that run `zmx-peer-chat hook-wait` with `asyncRewake`. |
| `.codex-plugin/plugin.json` | Codex | Manifest: `"skills": "./codex-skills/"` and `"hooks": "./codex/hooks.json"`. |
| `codex-skills/zmx-peer-chat/SKILL.md` | Codex | How Codex sends through file-backed messages and receives queued turns. |
| `codex/hooks.json` | Codex | An empty hooks file, so Codex does not load the Claude hooks (see "Codex side"). |
| `codex/rules/zmx-peer-chat.rules` | Codex | Example `prefix_rule` lines for `~/.codex/rules/`. |

The repo root carries the Claude catalog (`.claude-plugin/marketplace.json`) and a Codex catalog (`.agents/plugins/marketplace.json`) that lists only this plugin.

### Labels

The register helper sets these zmx labels on a new session in one `zmx set`, after the session exists. Nothing in the plugin runs `zmx attach`: on a live session `zmx attach --labels` overwrites its labels.

| Key | Value | Set for |
|-----|-------|---------|
| `zpc.pair` | `d` + the first 16 hex digits of the SHA-256 of the session directory's canonical full path, or the `--pair` value | both |
| `zpc.role` | `claude` or `codex` | both |
| `zpc.inc` | 8 random hex digits, new for every session (the incarnation) | both |
| `zpc.proto` | the protocol version, `1` | both |
| `zpc.thread` | the Codex thread UUID the new TUI opened | Codex |

A peer is the one other session with the same `zpc.pair` and the other `zpc.role`. Zero or several such sessions refuse; nothing picks the first.

### Protocol version

`PROTO = "1"` in `zpc/common.py`. It is bumped on any incompatible change to the labels or to the message format. A session whose own `zpc.proto` differs refuses to send; a peer whose `zpc.proto` differs is refused; a message whose `proto` differs is quarantined.

### Register helper

```text
zmx-peer-chat register --role claude|codex --session NAME [--dir DIR] [--pair ID] [--timeout SECONDS] [--foreground]
```

The launcher runs it just before it creates the session with `zmx attach NAME <tool>`, in the same directory. It returns at once and binds in a detached child that logs one line to `register.log` in the mail root; the child lets go of the caller's stdin, stdout and stderr, so a launcher may capture the helper's output. `--foreground` binds in the foreground and prints the labels. `--timeout` (default 10 seconds) bounds the wait for the session and its thread.

1. If session `NAME` already exists, it changes nothing and exits 0 (`register: session NAME exists; its labels are left as they are`): the launcher attaches to the live session as before.
2. It takes a per-directory lock (`register-<hash>.lock` in the mail root), held until the bind ends.
3. For Codex it notes the time and snapshots the daemon's loaded thread ids, with the update time of each one whose `cwd` is the directory.
4. The bind waits for the session, then (Codex only) for the one thread the new TUI opened in the directory, names that thread `zpc-<inc>` with `thread/name/set`, and sets all labels in one `zmx set`.

The Codex thread pick, in `zpc/register.py`:

| The TUI | What identifies its thread |
|---------|-----------------------------|
| starts a thread (`codex`) | a loaded id that was not in the snapshot, with `createdAt` at or after the snapshot time |
| resumes one (`codex resume --last`, which the launcher runs in a directory with an interactive rollout) | `updatedAt` at or after the snapshot time and later than in the snapshot; resuming moves `updatedAt` to the resume time, whether or not the daemon still had the thread loaded |

A thread seen running a turn, at the snapshot or at any of the bind's polls 0.3 seconds apart, is never taken: a turn that ends moves `updatedAt` too. Being newly loaded is not enough: during a resume the starting TUI loaded an older thread of the same directory that it does not show, and that thread kept its old times (see "Register" under the demonstrations). An exiting TUI moves neither time. The spike saw `createdAt` read the time of the first `thread/read` for a thread without a rollout; the rule uses `createdAt` only for ids that were not loaded at the snapshot, and the sender's footer check (below) refuses any send to a thread the TUI does not show, so a wrong pick cannot start a turn.

### Exit codes

Every command uses the same codes; a refusal prints `zmx-peer-chat: <reason>` on stderr.

| Code | Meaning |
|------|---------|
| 0 | Done (`queued`, `delivered`, labels set, or nothing to do) |
| 1 | Refused, nothing sent: no peer, several peers, protocol mismatch, unbound or not-shown Codex thread, `codex queue` failed, session not registered; `waiting` also exits 1 for "no" and `daemon check` for an untested codex-cli |
| 2 | Usage: a bad argument, name or message file, or no zmx session to act for |
| 3 | The Codex daemon could not be reached or answered something unexpected (`codex daemon: …`) |
| 4 | Ambiguous: another registration runs for the directory, or several Codex threads opened in it at once; no label set |
| 5 | Not in time: the session or its Codex thread did not appear within `--timeout`; no label set |

### Commands

| Command | Who runs it | What it does |
|---------|-------------|--------------|
| `register …` | the launcher | above |
| `send --to codex --stdin` | Claude | finds the peer, checks it, queues `Chat from Claude: <text>` with `codex queue --thread <zpc.thread>`; prints `queued` |
| `prepare-message NAME` | Codex | creates `<mail root>/outbox/NAME`, empty, mode 0600, and prints its path |
| `send --to claude --message-file NAME` | Codex | consumes that file and delivers `Chat from Codex: <text>` to the mailbox; prints `delivered` while Claude's wait runs, `queued` otherwise |
| `status` | either | this session's labels, its peer and whether Claude's wait runs |
| `hook-wait` | the Claude hooks | the wait below; exit 2 hands the mail to Claude |
| `wait`, `waiting`, `collect` | diagnostics | a foreground wait, exit 0 while a wait runs, take the mail now |
| `daemon check`, `daemon skills --cwd DIR` | provisioning, tests | version and reachability check; the skill names Codex lists for `DIR` |

Every command finds its own session this way: `--session NAME` if given; else, when `CODEX_THREAD_ID` is set (Codex sets it for every command it runs), the one `codex` session whose `zpc.thread` is that id; else `$ZMX_SESSION`. Codex runs commands in its app-server daemon, whose `ZMX_SESSION` is the one it was started under, not the TUI's: on the box that named a session that no longer existed. With `CODEX_THREAD_ID` set, `ZMX_SESSION` is never consulted, and a thread no session is bound to (after `/new`) refuses.

### Sending to Codex

`send --to codex` queues only when all of these hold, and otherwise exits 1 with `nothing was sent` or `nothing was queued`:

- exactly one peer session of role `codex` in the pair is live in `zmx ls` (the daemon keeps a thread loaded after its TUI exits and would run a queued message headless);
- its `zpc.thread` label is a UUID;
- the Codex TUI shows that thread: one of the last six non-empty lines of `zmx history <peer>` ends with `· zpc-<inc>`, the footer's thread name. After `/new` the footer has no name, after `/resume` to another thread it has that thread's name, and a dialog over the footer hides it; each of these refuses.

### Mailbox

The mail root is `$ZPC_MAIL_DIR` or `/tmp/zmx-peer-chat-<uid>`, created mode 0700; every directory under it must be a directory owned by the uid with no group or other bits, or the command refuses.

```text
<root>/<pair-id>/inbox/<ns>-<pid>-<rand>.msg   one JSON message: proto, pair, from, inc (the Claude incarnation), sent, text
<root>/<pair-id>/quarantine/                   mail that was not delivered, kept and reported
<root>/<pair-id>/waiter                        heartbeat of the running wait: "<claude pid> <wait pid>", refreshed every second
<root>/<pair-id>/waiter.lock                   held by the one running wait (a second one returns at once)
<root>/<pair-id>/collect.lock                  held while a collect takes the inbox
<root>/outbox/<name>                           a message file Codex fills before a send
<root>/register.log                            one line per background registration
<root>/register-<hash>.lock                    the per-directory registration lock
```

A message is written to `.<name>.part`, opened with `O_EXCL`, and renamed to `<name>` in the inbox. A collect takes the `*.msg` files whose names do not start with a dot, oldest first, under `collect.lock`, so it never sees a message that is still being written. Mail for another incarnation of the Claude session, in another protocol version, for another pair, or unreadable moves to `quarantine/` and is reported as `zmx-peer-chat: quarantined <file>: <why>`. `waiting` is true only while the heartbeat is under 5 seconds old and both pids in it are alive, so a killed wait reads as no wait at once.

### Claude side: the wait

The plugin's hooks run `zmx-peer-chat hook-wait` with `"asyncRewake": true` and a 24-hour timeout on `SessionStart`, `UserPromptSubmit`, `Stop` and `StopFailure`. The hook returns at once when its session is not a registered Claude side or a wait already runs; otherwise it waits in the background (up to 86100 seconds) while its `claude` process lives. When mail arrives it prints a note and the messages on stderr and exits 2, which wakes Claude even when it is idle; Claude Code shows it as hook feedback. Every new `claude` process runs `SessionStart`, including the one Happy starts on each mode switch, so no person has to start a wait, and the hook runs no Bash command, so local manual mode asks nothing. The owner is the nearest ancestor whose `argv[0]` basename is `claude` (the SDK binary in remote mode) or `claude.exe` (the npm package in local mode).

### Codex side

| Need | Why | What provisioning does |
|------|-----|------------------------|
| `zmx-peer-chat` on the login shell's `PATH` | Codex runs commands in its app-server daemon with a shell snapshot taken from a login shell, not with the TUI's environment, so a `PATH` set for the TUI does not reach them | links `bin/zmx-peer-chat` of the installed plugin into a directory on the login `PATH` (the demonstration used `~/.local/bin`, which the box's `~/.profile` adds when it exists) |
| the three rules of `codex/rules/zmx-peer-chat.rules` in `~/.codex/rules/` | Codex rules decide which commands run outside the sandbox without approval; inside it, `zmx ls` fails with `ReadOnlyFileSystem` | merges the lines |
| the plugin installed with `codex plugin marketplace add` and `codex plugin add zmx-peer-chat@dddpaul-claude-skills` | Codex finds the skill as `zmx-peer-chat:zmx-peer-chat` | installs it |

Codex loads a plugin's `hooks/hooks.json` unless the manifest's `hooks` names another file. Without the empty `codex/hooks.json`, Codex counted the three Claude hooks it supports and a fresh TUI stopped at a "Hooks need review" dialog before it created its thread, so the register helper timed out. `"hooks": []` falls back to `hooks/hooks.json`. The long-running daemon kept the hooks it first loaded for plugin version `0.1.0` across `codex plugin remove` and `codex plugin add`; a fresh `codex app-server` and a reinstall through the daemon's own `plugin/install` saw the change.

### For the launcher

1. Before `zmx attach NAME <tool>` creates a session, run `zmx-peer-chat register --role <tool> --session NAME --dir <dir>` (only for `claude` and `codex`), from any directory.
2. A non-zero exit means no label will be set; the launcher may start the session anyway, and its sends then refuse.
3. A registration that fails in the background (codes 3, 4 and 5) is logged to `register.log` in the mail root and leaves the session unlabelled.
4. Start one session per directory at a time; a second registration in the same directory while one binds exits 4. No other Codex TUI may start or resume a thread in that directory during the bind, which lasts up to `--timeout` (usually under two seconds); one that only runs a turn there is ignored.

## Box demonstrations

Every command ran from the Mac as `ssh <box> 'bash -l'` with a script on stdin. Three changes made after the review were tested on the Mac only, not on the box: the delivery's partial file is named `.<name>.part`, the detached register child lets go of the caller's output, and a thread seen running a turn is never bound. Throwaway sessions were named `zpc-*`; the scratch directory was `~/zpc-scratch`, and the session directories were `~/zpc-scratch/pair`, `~/zpc-scratch/fresh` and `~/zpc-scratch/fresh2`. Sessions were started through the box's own launcher with `script` supplying the terminal, as in the spike: `timeout 12 script -qfc "agent zpc-scratch/pair codex -n zpc-codex" /dev/null`. `Z` below is the scratch copy's `bin/zmx-peer-chat`.

### Temporary installs

The working tree was copied to the box with `tar` over ssh, never pushed for this.

```sh
# Claude: a scratch marketplace holding the plugin, enabled for the pair directory only
claude plugin marketplace add ~/zpc-scratch/mkt
cd ~/zpc-scratch/pair && claude plugin install zmx-peer-chat@zpc-scratch --scope project
# Codex: the repo's own catalog layout (.agents/plugins/marketplace.json + plugins/zmx-peer-chat)
codex plugin marketplace add ~/zpc-scratch/codex-mkt
codex plugin add zmx-peer-chat@dddpaul-claude-skills
mkdir ~/.codex/rules && cp <scratch copy>/codex/rules/zmx-peer-chat.rules ~/.codex/rules/
mkdir ~/.local/bin && ln -s ~/.codex/plugins/cache/dddpaul-claude-skills/zmx-peer-chat/0.1.0/bin/zmx-peer-chat ~/.local/bin/
```

```text
Added marketplace `dddpaul-claude-skills` from <home>/zpc-scratch/codex-mkt.
Added plugin `zmx-peer-chat` from marketplace `dddpaul-claude-skills`.
Installed plugin root: <home>/.codex/plugins/cache/dddpaul-claude-skills/zmx-peer-chat/0.1.0
```

`codex plugin marketplace add` and `codex plugin add` wrote `[marketplaces.dddpaul-claude-skills]` (`source_type = "local"`) and `[plugins."zmx-peer-chat@dddpaul-claude-skills"] enabled = true` to `~/.codex/config.toml`; a copy of the file taken before the install was compared after the removal (see "Cleanup").

### Codex install and skill discovery (AC #7)

```text
$ codex plugin list   # the dddpaul-claude-skills block
Marketplace `dddpaul-claude-skills`
<home>/zpc-scratch/codex-mkt/.agents/plugins/marketplace.json

PLUGIN                               STATUS              VERSION  SOURCE
zmx-peer-chat@dddpaul-claude-skills  installed, enabled  0.1.0    <home>/zpc-scratch/codex-mkt/plugins/zmx-peer-chat

$ Z daemon skills --cwd ~/zpc-scratch/pair | grep zmx-peer-chat
zmx-peer-chat:zmx-peer-chat
exit 0
$ Z daemon check
codex-cli 0.163.0 (tested with codex-cli 0.163.0); daemon ok, 4 loaded thread(s); protocol 1
exit 0
```

`daemon skills` sends `skills/list` (`{"cwds": [...], "forceReload": true}`) through the plugin's own daemon client. The full list also held the box's other skills; only the plugin's is shown. In the TUI, Codex read the skill on the first peer message (`Read SKILL.md (zmx-peer-chat:zmx-peer-chat skill)`).

### Register (AC #1)

A fresh start in a directory without Codex history, with the code as it stood before the review fixes (the thread pick by creation and update times was in place):

```text
$ Z register --role codex --session zpc-codex3 --dir zpc-scratch/fresh2
register: labelling zpc-codex3 in the background (log: register.log)
exit 0
$ agent zpc-scratch/fresh2 codex -n zpc-codex3
label after 1.6 s
$ zmx get zpc-codex3
zpc.inc=9dacd89b zpc.pair=<pair-id> zpc.proto=1 zpc.role=codex zpc.thread=<thread-3>
$ zmx get zpc-codex3 zpc.thread
<thread-3>
```

`zmx ls` showed `cmd=codex`, and the TUI footer read `GPT-6.1-Sol medium · ~/zpc-scratch/fresh2 · zpc-9dacd89b`. "label after" is the time from the register command to the first `zmx get … zpc.thread` that succeeded, polled every half second.

A resume, in the directory where earlier turns had left an interactive rollout, so the launcher ran `codex resume --last` and the daemon still had the thread loaded:

```text
$ Z register --role codex --session zpc-codex --dir zpc-scratch/pair
register: labelling zpc-codex in the background (log: register.log)
exit 0
$ agent zpc-scratch/pair codex -n zpc-codex
label after 1.6 s
$ zmx get zpc-codex
zpc.inc=9ef063ae zpc.pair=<pair-id> zpc.proto=1 zpc.role=codex zpc.thread=<thread-1>
```

`zmx ls` showed `cmd=codex resume --last`, and the footer read `… · ~/zpc-scratch/pair · zpc-9ef063ae`: the resumed thread was renamed from its previous incarnation's name.

Three failures on the way shaped the helper:

- The first launch after the plugin install stopped at Codex's "Hooks need review" dialog (`3 hooks are new or changed`): no thread, and the background bind logged `zpc-codex: no new Codex thread in <home>/zpc-scratch/pair in time; no label set` (code 5). Fixed by the empty `codex/hooks.json`.
- The first resume saw no new loaded id and timed out (code 5); `thread/read` showed that the resume had moved the thread's `updatedAt` to the resume time, while killing the TUI had not moved it. The helper took that as the resume signal.
- A later resume bound the wrong thread: while `codex resume --last` resumed `<thread-1>`, the starting TUI loaded `<thread-2>` (a turnless thread from an earlier `/new` in the same directory, not loaded at the snapshot), and the helper took it as new within 1.1 seconds. The footer showed `<thread-1>`'s name, so every send would have refused. `<thread-2>` had kept its creation and update times from the `/new`, so the helper now requires a started thread to be created after the snapshot (`test_an_older_thread_loaded_again_is_no_candidate`).

### Send to Codex, and the dead session (AC #2)

```text
$ Z send --to codex --stdin --session zpc-claude <<'MSG'
Box test C1 of the zmx-peer-chat plugin. Please answer me through the zmx-peer-chat skill with exactly this text: PONG-C1, no reply needed.
MSG
queued
exit 0
```

The idle Codex TUI showed `› Chat from Claude: Box test C1 …` as a new turn and answered through the skill (next section). After `zmx kill zpc-codex`, with the thread still loaded in the daemon:

```text
thread …e27e name=zpc-23e41a92 status=idle turns=5
$ zmx kill zpc-codex
killed session zpc-codex
$ Z send --to codex --stdin --session zpc-claude <<'MSG' ...
zmx-peer-chat: no codex session is paired with zpc-claude; nothing was sent
exit 1
thread …e27e name=zpc-23e41a92 status=idle turns=5
```

The `thread …` lines come from `thread/read` with `includeTurns` before the kill and five seconds after the refused send: no turn was added.

### Codex replies to Claude

With the rules and the `PATH` link in place, the Codex TUI ran, without any approval:

```text
• Ran zmx-peer-chat prepare-message zpc-codex-c1-7b29.txt
  └ /tmp/zmx-peer-chat-<uid>/outbox/zpc-codex-c1-7b29.txt
• Edited /tmp/zmx-peer-chat-<uid>/outbox/zpc-codex-c1-7b29.txt (+1 -0)
    1 +PONG-C1, no reply needed.
• Ran zmx-peer-chat send --to claude --message-file zpc-codex-c1-7b29.txt
  └ delivered
```

before which its `zmx-peer-chat status` had found its own session through `CODEX_THREAD_ID` (`peer: zpc-claude (claude)`, `waiting: yes`). Claude woke with the message as hook feedback and ended the exchange (`No action needed — Codex's message requires no reply.`); a new wait was running right after. Before the fixes this run failed three ways: `zmx-peer-chat: command not found` (the daemon's `PATH`), `zmx ls failed: error: ReadOnlyFileSystem` (`status` had no rule and ran in the sandbox), and `zmx session <the daemon's ZMX_SESSION> is not running`.

### `/new` and `/resume` (AC #3)

```text
thread …e27e name=zpc-23e41a92 status=idle turns=4
$ (in the Codex pane) /new
  GPT-6.1-Sol medium · ~/zpc-scratch/pair
$ Z send --to codex --stdin --session zpc-claude <<'MSG' ...
zmx-peer-chat: the Codex TUI in zpc-codex does not show thread zpc-23e41a92 (moved by /new or /resume, or a dialog covers the footer); nothing was queued
exit 1
thread …e27e name=zpc-23e41a92 status=idle turns=4
```

Then `/resume` in the pane listed one entry, `zpc-23e41a92`; resuming it brought the name back to the footer, and the next send queued on the shown thread:

```text
  GPT-6.1-Sol medium · ~/zpc-scratch/pair · zpc-23e41a92
$ Z send --to codex --stdin --session zpc-claude <<'MSG' ...
queued
exit 0
thread …e27e name=zpc-23e41a92 status=idle turns=5
```

`/new` and `/resume` were typed into the throwaway Codex pane with `zmx send` to drive the test; no message went that way. Resuming another directory's thread was not tried: the picker's "All" view also lists the user's own threads.

### Send to Claude: delivered and queued (AC #4)

From a throwaway shell session labelled as the Codex side (`zpc-fakecodex`, `zmx set zpc-fakecodex zpc.pair=<pair-id> zpc.role=codex zpc.inc=feedface zpc.proto=1`):

```text
$ echo "Local-mode test L2 …" | Z send --to claude --stdin --session zpc-fakecodex
delivered
```

With the wait killed first (`kill <hook-wait pid>`):

```text
waiting: no
$ echo "Box test Q2, sent right after the wait was killed. …" | Z send --to claude --stdin --session zpc-fakecodex
queued
exit 0
<one .msg file in the inbox>
```

A test prompt typed into the throwaway Claude pane then ran the hooks, whose new wait took the queued message at once: Claude answered the prompt (`OK`), then the mail (`PONG-Q2`), and the next send printed `delivered` and woke it (`PONG-D1`). Before the heartbeat carried the wait's own pid, the same kill left `waiting: yes` for up to ten seconds and a send in that window printed `delivered` for mail no wait would take.

### Local manual mode (AC #5)

The throwaway Claude ran under Happy in local mode with `⏸ manual mode on` in its status line. Nobody asked for a wait and no approval prompt appeared; the wait ran as a hook, not as a Bash command:

```text
$ Z waiting --session zpc-claude
waiting: yes
pid … /bin/sh -c "${CLAUDE_PLUGIN_ROOT}/bin/zmx-peer-chat" hook-wait
  ^ … /usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe --resume <session-id> …
```

### Happy mode switches (AC #6)

The user switched the throwaway session to remote mode from the Happy app. The wait was running again under the new process, the SDK claude, with nobody asking:

```text
$ Z waiting --session zpc-claude
waiting: yes
pid …
  ^ … /bin/sh -c "${CLAUDE_PLUGIN_ROOT}/bin/zmx-peer-chat" hook-wait
  ^ … /usr/lib/node_modules/happy-coder/node_modules/@anthropic-ai/claude-agent-sdk-linux-x64/claude --output-format stream-json --verbose --input…
  ^ … node … happy-coder/dist/index.mjs claude …
```

A message sent then (`R1`) woke it about a second and a half later; the transcript recorded `version= 2.1.141 entrypoint= remote_mobile` and the reminder `Stop hook blocking error from command "SessionStart:resume": zmx-peer-chat: peer mail from Codex. …`, and Claude ran the reply command from the note. The switch back to local was Ctrl-T typed into the throwaway pane (`Press space (or Ctrl-T) to switch to local mode`). Fifteen seconds later:

```text
waiting: yes
pid … started … claude=… /usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe --resume <session-id> …
```

and a message sent then (`L2`) woke the local process (`PONG-L2`), after which a wait was running again (`UserPromptSubmit` starts one as the wake arrives, `Stop` at the end of the turn).

### Cleanup (AC #11)

```text
$ zmx kill zpc-claude
killed session zpc-claude
$ zmx kill zpc-fakecodex
killed session zpc-fakecodex
$ zmx kill zpc-codex
killed session zpc-codex
$ zmx kill zpc-codex2
killed session zpc-codex2
$ zmx kill zpc-codex3
killed session zpc-codex3
$ cd ~/zpc-scratch/pair && claude plugin uninstall zmx-peer-chat@zpc-scratch --scope project
✔ Successfully uninstalled plugin: zmx-peer-chat (scope: project)
$ claude plugin marketplace remove zpc-scratch
✔ Successfully removed marketplace: zpc-scratch
$ codex plugin remove zmx-peer-chat@dddpaul-claude-skills
Removed plugin `zmx-peer-chat` from marketplace `dddpaul-claude-skills`.
$ codex plugin marketplace remove dddpaul-claude-skills
Removed marketplace `dddpaul-claude-skills`.
$ rm ~/.codex/rules/zmx-peer-chat.rules && rmdir ~/.codex/rules
$ rm ~/.local/bin/zmx-peer-chat && rmdir ~/.local/bin
$ rm -r ~/.claude/plugins/cache/zpc-scratch   # the uninstall left it, marked .orphaned_at
$ rmdir ~/.codex/plugins/cache/dddpaul-claude-skills   # empty after codex plugin remove
$ rm -r ~/zpc-scratch /tmp/zmx-peer-chat-<uid>   # scratch copies and the mailbox
```

The listings after it:

```text
$ zmx ls | grep -c zpc-
0
$ claude plugin marketplace list | grep -c zpc-scratch
0
$ claude plugin list | grep -c "zmx-peer-chat@zpc-scratch"
0
$ ls ~/.claude/plugins/cache | grep -c zpc-scratch
0
$ codex plugin list | grep -c -e dddpaul-claude-skills -e zmx-peer-chat
0
$ ls ~/.codex/plugins/cache | grep -c dddpaul-claude-skills
0
$ diff <copy taken before the install> ~/.codex/config.toml
no difference
$ ls -d ~/.codex/rules ~/.local/bin
ls: cannot access '<home>/.codex/rules': No such file or directory
ls: cannot access '<home>/.local/bin': No such file or directory
$ bash -lc "command -v zmx-peer-chat"
exit 1
```

`zmx ls` listed only the user's own session. The transcripts of the throwaway Claude and Codex sessions were left in place.
