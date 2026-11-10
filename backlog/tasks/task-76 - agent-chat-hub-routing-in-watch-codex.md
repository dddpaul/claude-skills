---
id: TASK-76
title: agent-chat hub routing in watch-codex
status: Done
assignee: []
created_date: '2026-11-10T14:06:00Z'
updated_date: '2026-11-10T15:52:00Z'
labels:
  - feature:agent-chat-hub
dependencies:
  - TASK-75
priority: medium
ordinal: 76000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Task 3 of 4 of the agent-chat hub feature: hub routing in watch-codex, in all-rooms and single-thread mode, using the wake predicate task 2 added to `addressing.py`.

The agent-chat code lives in `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/` and its tests in `plugins/agent-chat/skills/agent-chat/tests/`. The block below is the contract shared by all four hub tasks; this task implements only its own part, and its acceptance criteria are this task's section of the sketch. Every task must leave every 0.4.4 behaviour unchanged while no `hub` key is configured.

**Direction:** approach A, one shared hub room named by the `hub` key. Projects are addressed at the start of a message
(`beta, gamma: …`), and agents' messages carry their sender project in a content field and a visible prefix.

**Locked decisions (with rationale):**

- **The optional key `hub = "agents-hub"` names the hub `#<hub>:<server_name>`.** Without the key, agent-chat
  behaves exactly as 0.4.4. A `hub` that is not a string or does not start with `room_prefix` is a config error.
  While the hub is on, `send` and the wait refuse the project whose room is the hub (`hub` for `agents-hub`).
  *Rationale:* the owner names the room in the config. Joining needs the prefix, and one room must never be both the
  hub and a project room.
- **Group conversations:** a message may address several projects, and the answers stay in one hub thread.
  *Rationale:* the owner needs group questions with the answers in one place.
- **The address is the run of comma-separated project tokens at the start of the body, followed by `:`.** A token
  is `[A-Za-z0-9._-]+`, exact and case-sensitive. `beta: …`, `beta, gamma: …` and `beta: @claude-a …` are addresses;
  `beta @claude-a: …`, `Summary: …` (unless `Summary` is a project), a name without `:` and a mention-only message are
  not. The listener tests only whether its own project is among the tokens: no alias lookups on the wake path.
  *Rationale:* Element sends plain text and pills, and a pill's body text is a display name that cannot be parsed
  reliably.
- **Accounts narrow the address and come only from `m.mentions` and the literal `@`-run right after the colon,**
  parsed with the existing mention rules. *Rationale:* `m.mentions` is exact, wherever the pill sits.
- **An agent's hub message carries `"agent_chat.hub": {"v": 1, "from": "<project>", "to": [<projects>]}`** and the
  visible prefix `<from> → <to, comma-separated>: `, or `<from>: ` when `to` is empty. For an agent the field is
  authoritative and the text is for people; a missing or invalid field wakes nobody and makes no participant. The field
  never supplies authority. *Rationale:* accounts are per host, so only the field names the sender's project.
- **A session is the pair (account, project).** Own-message suppression, thread participants, the note's "(this
  account)" label and the skipped thread context, Codex routing and dedup, and status all compare pairs. *Rationale:*
  otherwise beta on host A cannot reach alpha on host A, because both are `@claude-a`.
- **One wake predicate for the listener (me, P), shared by Claude's wait and watch-codex:**
  1. A non-message, a body that is not a string, an edit, and a sender that is neither the human nor a configured
     agent: nothing.
  2. An agent message: nothing when the field is invalid, when it is the own pair (sender `me`, `from` P) or when
     `to` is empty. Otherwise it wakes when P is in `to` and either there are no mentions or `me` is among them, in a
     thread too.
  3. A human message with an address: it wakes when P is named and either there are no mentions or `me` is among
     them, even when its thread cannot be read.
  4. A human message without an address: at top level, nothing. In a thread, it wakes (me, P) when the root's address
     selects it or (me, P) is a participant pair; when that message has mentions, only if `me` is among them. A root's
     address is the human root's parsed address, or an agent root's `to` and mentions. Participants are the (sender,
     `from`) pairs with a valid field among the root and the thread's newest 50 events. If the lookup fails, it wakes
     nothing and logs the event.

  *Rationale:* an explicit address must never depend on optional thread context. Inheritance is the user's
  convenience, and agents never inherit, so they cannot wake each other in a loop.
- **Every agent send to the hub is explicit:** `send --hub --project a,b [--to <account>] [--thread <id>]`. `--hub
  --thread <id>` without `--project` posts for the user (`to` empty). `send` never derives an address from a thread.
  *Rationale:* a thread's audience is a union of per-project selectors, which one field and one `m.mentions` cannot
  express.
- **The note gives each hub message its provenance and a ready reply command.** The header reads `Hub: from <project>
  (<authority>) to <projects>`, or names the user. The reply hint is `agent-chat send --hub --thread <id> --project
  <from> --to <sender>` for an agent's mail and `agent-chat send --hub --thread <id>` for the user's mail. The Codex
  form uses `--as codex --message-file <name>` first. *Rationale:* receiving must never invite a reply into the wrong
  room.
- **Locks and cursors stay per (account, project room),** and the wait reads the hub's timeline from the same `/sync`.
  *Rationale:* a shared hub cursor would let alpha's wait consume beta's mail. A group message delivered once to each
  addressed session is intended, not a duplicate.
- **The hub is isolated:** a bounded resolve and join at wait start, logged once per wait on failure and retried at the
  next wait. Its failure never blocks project-room mail. *Rationale:* an optional room must not break the main path.
- **Delivery is best-effort and documented:** at most 50 events per sync, a per-(account, project) cursor that starts
  at now on first use, and Codex dropping mail when no session matches. *Rationale:* replay is a separate feature.
- **Rollout:** tasks 1 to 4 are released, and every host is upgraded with its waits and watchers restarted. Only then
  is the room provisioned and the `hub` key set; the hub-only skill switch is a later task, after a live round trip.
  *Rationale:* a host on an old version, or a wait that started before the upgrade, misses hub mail silently.

**Scope cuts:**

- No per-project accounts, no fan-out into project rooms, and no routing by tags the user cannot type.
- No hub-wide broadcast: the user's unaddressed top-level hub message wakes nobody.
- No feedback on a mistyped project, and no listing of projects in status.
- No replay of mail beyond the sync limit, and no bigger limit.
- No copy of hub threads into project rooms, and no bridge to the local SendMessage.
- No change to authority labels, the thread lookup budget, the project-room wake rule or cursor semantics.
- No hub-only skill switch in tasks 1 to 4.

**Acceptance criteria (sketch):**

Task 1, hub config and `send --hub`:

- Without `hub`, every existing test passes unchanged, and `send --hub` refuses with one line, a non-zero exit and
  nothing posted. A `hub` that is not a string or does not start with `room_prefix` is a config error.
- `send --hub` refuses with one line, a non-zero exit and nothing posted in each of these cases:
  - a target is not a token or its room does not resolve;
  - a target is the own project or `hub`;
  - the sender's project room does not resolve;
  - the working directory's project room is the hub (a directory named `hub` for `hub = "agents-hub"`);
  - `--to` comes without `--project`.
- A target is checked with `resolve_alias` and its room is not joined.
- `send --hub --project beta,gamma --to claude-b` posts into the hub the prefix `alpha → beta, gamma: `, the field
  with `v` 1, `from` alpha and `to` [beta, gamma], and `m.mentions` with `@claude-b`.
- `send --hub --thread <id>` without `--project` posts the prefix `alpha: ` and a field with an empty `to`. The
  existing thread-root refusals apply in the hub.
- The Codex form `send --as codex --message-file x.txt --hub --project beta` works.
- `codex execpolicy check` against the shipped rules allows both `… --message-file x.txt --hub --project beta` and
  `… --message-file x.txt --hub --thread abc_DEF-123`.
- Version 0.5.0 in both plugin.json files and in the version pin.

Task 2, hub receiving in Claude's wait, the note and status:

- The user's `beta, gamma: x` in the hub wakes the beta and gamma sessions and not alpha. `beta: @claude-b x` wakes
  only (`@claude-b`, beta). `beta @claude-b: x`, `Summary: x`, a mention-only message and a name without `:` wake
  nobody.
- An agent message from (`@claude-a`, beta) to alpha wakes (`@claude-a`, alpha). The same message wakes nobody under
  (`@claude-a`, beta). An agent hub message without the field, or with `v` other than 1, wakes nobody.
- In an alpha, beta and gamma thread, beta's agent post with an empty `to` wakes nobody. The user's later unaddressed
  reply in that thread wakes the root's addressees plus every valid participant pair, including beta's poster, and
  no other alpha account.
- The user's unaddressed thread reply whose thread cannot be read wakes nobody and is logged. An explicitly addressed
  message in the same unreadable thread is delivered.
- Two waits of one account, for alpha and beta, each deliver only their own project's hub mail. A message addressed to
  both is delivered once to each.
- With the hub unresolvable or not joinable, the wait still delivers project-room mail, and it logs the hub failure
  once.
- The note shows the hub header and reply hints. The "(this account)" label and the skipped context compare pairs.
- `status` shows the hub as covered, unavailable or unknown from `<slug>.hub`, and the `.owner` format is unchanged.

Task 3, hub routing in watch-codex:

- In all-rooms mode, a hub message addressed to beta and gamma is queued once to each project's `zpc.role=codex`
  session. A project with no session logs `not queued: …`.
- In single-thread mode, hub mail addressed to its project is queued to its thread, and other hub mail is ignored.
- The own pair (`@codex-a`, beta) does not wake beta's Codex.

Task 4, documentation:

- The README and both SKILL.md files document:
  - the hub, the address grammar with an Element pill example, and the reply commands;
  - best-effort delivery, provisioning and the rollout order with restarts;
  - that mail from another project's agent carries no approval;
  - one topic per hub thread, with its id recorded where the work is tracked.

  The hub stays optional; the skills do not yet say "hub only".
- `uv run ruff check .` is clean and `uv run pytest plugins/agent-chat` passes after every task.

**Implementation checklist:**

- `config.py`: the optional string `hub`, checked against `room_prefix`; the hub alias; refusal of the project whose
  room is the hub.
- `addressing.py`: the project-address parser, the field reader and validator, and the pair-aware hub predicate
  shared by `listen.py` and `watch.py`. The literal `@`-run is parsed after the colon; `m.mentions` is
  position-independent.
- `threads.py`: participant pairs from valid fields, the root's address, and fail-closed inherited routing for the hub
  only.
- `cli.py`: `--hub`, `--project` and the refusals in `send`; the prefix and the field; the Codex `--message-file`
  path; and the hub line in `status`.
- `listen.py`: the hub timeline from the same sync, per-room pre-join suppression and leave handling, the bounded
  hub setup, and the `<slug>.hub` coverage file.
- `watch.py`: per-project routing in all-rooms mode, hub mail in single-thread mode, and pair-aware dedup.
- `note.py`: the hub header, the reply hints and pair-aware labels.
- Tests against the fake homeserver for every criterion; the execpolicy regression.
- README and both SKILL.md files; version bumps per task.
- Live round trip after rollout, across two hosts:
  1. alpha on host B asks beta on host A, and the answer arrives in the thread;
  2. the same account with a different project: beta and alpha on host A reach each other;
  3. `beta, gamma: …` gets both answers in one thread;
  4. the user's unaddressed thread reply from Element reaches the thread's addressees and posters;
  5. `beta: <pill> x` from Element wakes only that account;
  6. a single-thread Codex watcher receives hub mail for its project.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 In all-rooms mode a hub message addressed to beta and gamma is queued once to each project's zpc.role=codex session, and a project with no session logs 'not queued: …'
- [x] #2 In single-thread mode hub mail addressed to its own project is queued to its thread without a zmx lookup, and other hub mail is ignored
- [x] #3 The own pair (@codex-a, beta) does not wake beta's Codex, while a message from (@codex-a, alpha) to beta does
- [x] #4 Version 0.5.2 in both agent-chat plugin.json files and in the version pin in test_agent_chat_codex.py
- [x] #5 uv run ruff check . is clean and uv run pytest plugins/agent-chat passes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: move the hub wake loop from Listener into SyncLoop.hub_routes (per-project, targets from field/address/thread pairs when no project is fixed); CodexWatcher joins the hub in each sweep (bounded, failure logged once), skips the hub as a project room, routes hub mail per project into the project room's delivery (all-rooms: find_session per project; single-thread: only its project, no zmx lookup). Tests in test_agent_chat_codex.py; bump to 0.5.2.

Commit: `e6af38a` - task-76: route hub mail in watch-codex per project, with the hub wake loop shared by the wait and the watcher

Commit: `b237ed8` - task-76: refuse watch-codex --thread in the directory whose room is the hub

Done. SyncLoop.hub_routes now holds the hub wake loop for both Listener.hub_mail (one project) and CodexWatcher (projects from the message's field/address, or for the user's unaddressed thread reply from this account's participant pairs plus the root's address). The watcher joins the hub in each sweep within HUB_SECONDS, logs a failure once per reason, forgets the hub on leave, never serves it as a project room, and merges hub mail into the project room's delivery (log names 'in the hub <alias> for <project>'). Single-thread mode serves only its own project's hub mail, with no zmx lookup. watch-codex --thread refuses the directory whose room is the hub (review's minor finding). Review: ralph:task-reviewer APPROVED (score 9) on e6af38a; the follow-up refusal commit is covered by a new test. ruff clean; pytest plugins/agent-chat 269 passed, 7 skipped. Version 0.5.2.

Review: APPROVED b237ed8 (task-reviewer, score 10): the watch-codex --thread refusal of the hub's directory is correct, minimal and pinned by a test that fails without it.
<!-- SECTION:NOTES:END -->
