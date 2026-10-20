# zmx peer chat: transport spike

Spike for TASK-49: which delivery paths work for a Claude Code and Codex pair that both run on a remote Linux box, each in its own zmx session, with nothing forwarded to the Mac. All experiments ran on 2026-10-20 in throwaway `spike-*` zmx sessions in a scratch directory on the box. Placeholders: `<box>` is the ssh alias, `<home>` the box user's home, `<host>` its host name, `<uid>` its uid, `<thread-uuid>` the throwaway Codex thread id.

## Versions

| Tool | Command | Output on the box |
|------|---------|-------------------|
| codex-cli | `codex --version` | `codex-cli 0.163.0` |
| zmx | `zmx version` | `zmx		0.8.1` (then `ghostty_vt	ghostty-1.3.2-dev-5UdBC4FtYAV-PdFOt-gceWieTHLri0H4ztHtd6Tr4dGj`, `socket_dir	/run/user/<uid>/zmx`, `log_dir		<home>/.local/state/zmx/logs`) |
| claude-code | `claude --version` | `2.1.280 (Claude Code)` |
| happy-coder | `happy --version` | `happy version: 1.1.9` (followed by `Error: Request failed with status code 401`, which does not affect the version) |

All four match the versions the task expected.

## Setup

Every command ran from the Mac as `ssh <box> '...'`. The scratch directory was `~/spike-zmx-peer-chat`. Sessions were started through the box's own launcher, the way agterm starts them, with `script` supplying the terminal that `zmx attach` needs; `timeout` then ends the client and the session keeps running:

```sh
timeout 8 script -qfc "agent spike-zmx-peer-chat codex -n spike-codex" /dev/null
timeout 10 script -qfc "agent spike-zmx-peer-chat claude -n spike-claude" /dev/null
zmx set spike-codex pair=spike-zmx-peer-chat inc=<8 hex digits>
```

### zmx behaviour seen on the way

| What | Command | Observed |
|------|---------|----------|
| Create a detached session | `zmx run spike-probe -d bash -c 'echo probe-started; exec bash'` | `session "spike-probe" created` / `command sent!`. `run` starts a login shell and types the command into it with `; echo ZMX_TASK_COMPLETED:<id>:$?` appended, so the command is not the session process. |
| Session listing | `zmx ls` | `name=spike-probe	pid=…	clients=0	created=…	cwd=file://<host><home>/spike-zmx-peer-chat` |
| Several labels at once | `zmx attach --labels "pair=spike inc=abc" spike-probe3 bash` | both set (`inc=abc pair=spike`) |
| Repeated flag | `zmx attach --labels pair=spike --labels inc=abc spike-probe2 bash` | only the last one is kept (`inc=abc`) |
| Comma-separated | `zmx attach --labels pair=spike,inc=abc …` | `error: key-value kvs can only contain [a-z, A-Z, 0-9, -_.] characters: value=[spike,inc=abc]` |
| Labels on any session | `zmx set spike-probe pair=spike inc=xyz` | `inc=xyz pair=spike` |
| Relabel by attaching | `zmx attach --labels inc=changed spike-probe` on a live session | labels become `inc=changed pair=spike`: an attach overwrites the labels of an existing session, so a launcher must read them (`zmx get`) before it attaches |
| Screen with escapes | `zmx history <name> --vt` | colours as SGR sequences and, at the end, the cursor position as CUP (`ESC[24;38H`) |
| Session process exit | Ctrl-C twice into the Codex session (`zmx send spike-codex "$(printf '\003')"`) | the launcher's session runs `codex` itself, so the session ended with it; the second send got `session spike-codex is unresponsive (Unexpected)` / `daemon may be busy: try again`. A launcher-started Codex never leaves a shell behind. |

## Codex: how a launcher learns its thread id

Every Codex TUI on the box runs on a shared local app-server daemon (`codex features list`: `daemon_auto_start stable true`, `tui_app_server removed true`; the daemon is `codex app-server --listen unix://`). Before its first turn a fresh TUI writes nothing a launcher could read: no rollout under `~/.codex/sessions` and no line in `~/.codex/session_index.jsonl`. The daemon knows the thread from the start, though.

`codex app-server proxy` passes stdio to the daemon's control socket, which speaks JSON-RPC over WebSocket (a plain JSONL `initialize` gets no answer; an HTTP upgrade gets `HTTP/1.1 101 Switching Protocols`). A throwaway stdlib client (`rpc.py`, about 50 lines: the upgrade request, masked text frames out, plain frames in) sent `initialize`, `initialized`, `thread/loaded/list` and `thread/read`:

```sh
cd ~/spike-zmx-peer-chat && python3 -u rpc.py
```

```text
initialize: ok
loaded thread ids: 1
{"id": "<thread-uuid>", "name": null, "cwd": ".../spike-zmx-peer-chat", "status": {"type": "idle"}, "source": "vscode", "createdAt": 1792476089, "updatedAt": 1792476089, "path": ".../rollout-2026-10-20T08-59-24-<thread-uuid>.jsonl"}
```

`createdAt` is not the thread's start time: the TUI started at 05:59:24Z (the rollout name, in box time UTC+3, and the time recorded just before the launch), while `createdAt` and `updatedAt` both read 06:01:29Z, the moment of this first `thread/read`. For a thread with no rollout yet the daemon apparently reports "now", so it cannot tell a new thread from an older one in the same directory, and a thread whose TUI has exited stays loaded (below). The launcher therefore lists the loaded thread ids before it starts Codex, starts it, lists them again until a new id appears, and takes the new id whose `cwd` is the session directory. `thread/name/set` then gives the thread a deterministic name (`python3 -u rpc.py thread/name/set '{"threadId":"<thread-uuid>","name":"spike-codex-<inc>"}'` returned `{"id": 2, "result": {}}`): the TUI footer showed the name at once and `session_index.jsonl` gained the line. The name is not usable by `codex queue` before the first turn, though (next section), so the launcher should store the UUID, for example as a zmx label, and use the name only for people. After the first turn the same id is also in the rollout's `session_meta` (`payload.id`, with `payload.cwd`).

## Codex: `codex queue`

`codex queue` adds the message to the daemon's queue (`~/.codex/queue_1.sqlite`, table `queued_items(id, thread_id, payload_json, queue_order, created_at_ms, updated_at_ms)`); the daemon starts it as a turn as soon as the thread is idle. It never types into the terminal.

### Idle TUI

```sh
codex queue --thread <thread-uuid> --message "Peer-chat spike test 1 (idle). Reply with the single word PONG-IDLE and nothing else."
```

Exit 0: `Queued message <message-id> for thread <thread-uuid>.` `queued_items` was already empty again. The idle TUI showed the message as a new user turn and answered within two seconds:

```text
› Peer-chat spike test 1 (idle). Reply with the single word PONG-IDLE and nothing else.
• PONG-IDLE
  Worked for 2s • 9:02 AM
```

The same command with the thread's name instead of the UUID, before that first turn, failed: `Error: No active session found matching 'spike-codex-<inc>'.` Once the thread had a turn on disk the name worked (test 2b below).

### Busy TUI

Test 2a queued a turn that runs `sleep 20`; five seconds in, test 2b was queued by name:

```sh
codex queue --thread <thread-uuid> --message "Spike test 2a: run the shell command sleep 20, then reply with the single word DONE-A."
codex queue --thread spike-codex-<inc> --message "Spike test 2b (sent while busy). Reply with the single word PONG-BUSY."
```

Both exited 0 with `Queued message … for thread <thread-uuid>.` While 2a ran, `queued_items` held one row (`{"UserInput":{"content":[{"type":"text","text":"Spike test 2b (sent while busy)…`) and the TUI showed only `• Working (7s • esc to interrupt) · 2 background terminals running` with an empty composer: no queued-message indicator. The running turn was not interrupted; 2b ran as the next turn as soon as 2a ended, and the queue drained:

```text
• DONE-A
  Worked for 28s • 9:03 AM
› Spike test 2b (sent while busy). Reply with the single word PONG-BUSY.
• PONG-BUSY
```

### An id that matches no session

```sh
U=$(python3 -c "import uuid; print(uuid.uuid4())")
codex queue --thread "$U" --message "should not arrive"
codex queue --thread no-such-spike-session --message "should not arrive"
```

| `--thread` | Exit | Output |
|------------|------|--------|
| a random UUID | 1 | `Error: failed to queue session message: thread/queue/add failed: failed to read thread: invalid thread-store request: no rollout found for thread id <random-uuid> (code -32603)` |
| `no-such-spike-session` | 1 | `Error: No active session found matching 'no-such-spike-session'.` |

Nothing was queued and the TUI did not change.

### After the TUI has exited

After the Codex TUI and its zmx session had ended (Ctrl-C twice), `thread/loaded/list` still listed the thread as `idle`, and `codex queue --thread <thread-uuid> --message "Spike test 4 (TUI gone). Reply with the single word PONG-GONE."` exited 0 with `Queued message …`. The daemon ran the turn without any UI: the rollout ends with the user message and the answer `PONG-GONE`. A queued message can therefore start a turn, shell commands included, that nobody watches. A sender must check that the Codex session is alive before it queues.

## Codex: `zmx send` fallback (AC #4)

Skipped. `codex queue` delivers to a running TUI both when it is idle and when it is busy, so the screen-reading and typing fallback (`zmx history --vt` checks of the composer, a marker typed with `zmx send` and removed before any submit) is not needed for Claude-to-Codex. The observations that came up anyway are in the zmx table above (the CUP cursor position at the end of `--vt` output, and that typing works with `zmx send`).

## Claude: mailbox wake under Happy

The Mac mailbox script was copied to the scratch directory with its one BSD call made Linux (`stat -f %m` to `stat -c %Y`) and its root moved to the scratch directory (`mail.sh`). A scratch `.claude/settings.local.json` pre-approved `Bash(~/spike-zmx-peer-chat/mail.sh wait:*)`. The throwaway Claude (under Happy, started by the launcher) was asked, by typing into its pane in local mode, to run `~/spike-zmx-peer-chat/mail.sh wait spike $PPID 1800` as a background Bash task, to answer `GOT-MAIL:` plus the output whenever it completed, and to start the wait again. Messages were dropped from outside with `echo "Chat from Codex: …" | ~/spike-zmx-peer-chat/mail.sh deliver spike`.

Two prompts came up that the plugin has to plan for:

- First run in a new directory: the trust dialog, which also lists the pre-approved rules (`This folder pre-approves 2 tool permissions in .claude/settings.local.json`); its default is `No, exit`.
- Every start of the wait in local mode (Claude's `manual mode`, three times in the spike): `Bash command … Contains simple_expansion / Do you want to proceed?`, because of `$PPID`. An allow rule cannot pre-approve a command with a shell variable, so in local manual mode each restart waits for a person. In remote mode the restarts after R1 and R2 ran within seconds and nothing reached this side; whether the Happy app asked for an approval was not recorded.

| Step | Mode | Waiter | Result |
|------|------|--------|--------|
| wait started (typed into the pane, prompt approved) | local | owner = the interactive `claude` | `waiting: yes` |
| L1 delivered | local | ends with mail | `Background command "Wait for peer mailbox message in background" completed (exit code 0)`, then `GOT-MAIL: Chat from Codex: spike local-mode message L1`, then a new wait |
| user switches to remote in the Happy app | remote | gone | Happy replaced the interactive `claude` with an SDK one (`…/claude-agent-sdk-linux-x64/claude`); the wait saw its owner exit and ended |
| R1 delivered | remote | none | stayed in the inbox, `waiting: no` |
| user asks, from the app, to restart the wait | remote | owner = the SDK `claude` | the new wait collected R1 at once; the transcript shows a `<task-notification>` and `GOT-MAIL: … R1`, then a new wait |
| R2 delivered, no message sent from the app | remote | ends with mail | `GOT-MAIL: … R2`; the next wait's shell started 6 s after R2 landed and was running when checked 30 s later |
| L2 delivered before the switch back took effect | remote | ends with mail | collected in remote mode |
| switch back with Ctrl-T (typed into the pane) | local | gone | Happy started a new interactive `claude`; Claude printed `Background command "Wait for peer mailbox message in background" was stopped` / `Background shell command didn't finish before the previous session ended` |
| L3 delivered | local | none | stayed in the inbox |
| wait restarted (typed, prompt approved) | local | owner = the new `claude` | collected L3 at once: `GOT-MAIL: … L3` |
| L4 delivered | local | ends with mail | `GOT-MAIL: … L4` |

Verdict: a background wait wakes Claude in local mode and in remote mode alike, but only a wait started in the current mode: every Happy mode switch, in either direction, replaces the `claude` process and kills the wait. Messages are kept in the inbox until the next wait starts. Nothing restarted the wait after a switch on its own: in remote mode the restart was asked for from the app, in local mode it was typed into the pane. Switching to local from the pane needs two spaces within a short window (`Press space again (or Ctrl-T) to switch to local mode`); a single typed space arms the switch, which confirms that nothing may be typed into Claude's pane in remote mode.

## Recommendation

| Direction | Transport | Conditions |
|-----------|-----------|------------|
| Claude to Codex | `codex queue --thread <UUID> --message <text>` | The launcher learns the UUID from the daemon by comparing the loaded thread ids before and after it starts Codex (the new id whose `cwd` is the session directory) and records it on the session (zmx label); the sender queues by UUID, not by name. Before queuing it checks that the Codex zmx session is alive, because the daemon runs queued messages headless once the TUI is gone. A queued message on a busy Codex waits for the current turn to end; it never steers. No typing, no screen reading. |
| Codex to Claude | the mailbox, collected by Claude's background `wait` | Claude needs a running wait in whichever Happy mode it is in, and every mode switch kills it; the spike found no trigger that restarts it, so the plugin has to provide one (open risks below). The sender reports `queued` unless `waiting` says a wait runs. The wait command must carry no shell variable (the script finds its own `claude` ancestor instead of taking `$PPID`), so one allow rule covers it and a restart in local manual mode does not wait for a person. Nothing is ever typed into Claude's pane. |

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

- Nothing restarts Claude's wait after a Happy mode switch. In the spike both restarts were asked for by a person (from the app in remote mode, typed into the pane in local mode). The plugin task has to design the trigger, for example a SessionStart hook if Happy's switch fires one, or the router noticing `waiting: no` and asking for a restart; neither was tested.
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
