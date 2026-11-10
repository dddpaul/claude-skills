# agent-chat: a shared hub room for cross-project talk

## Architecture decision

agent-chat gets one shared room, the hub, where agents of different projects and the user talk. Projects are addressed
at the start of a message, `beta, gamma: …`, and the user does the same from Element in plain text. This is approach A.
Cross-project messages go only through the hub; the local SendMessage between Claude sessions is no longer used for
them (it stays for subagents inside a session).

The need: an agent of one project on one host (alpha on host B) must reach agents of other projects on another host
(beta and gamma on host A). The owner also wants group questions, with the answers in one place. Today this is not
possible. Accounts are per agent and host (`@claude-a`), and a room names a project (`#agents-<project dir>`). A
mention therefore addresses a host, and the room supplies the project. A cross-project message needs a project for the
recipient, and one for the sender so that the answer can come back. A second defect follows from the per-host account:
the wait drops messages from its own account, so beta on host A writing to alpha on host A (both `@claude-a`)
would be lost.

Rejected:

- **B. Fan-out into the target projects' rooms.** `send --project beta,gamma` would post a copy into each room, and
  the asking session would follow its threads there by a hidden tag. The answers end up in N rooms, against the owner's
  "answers in one place". The routing rests on tags that the user cannot set from Element.
- **C. Per-project accounts** (`@claude-beta-a`). Pure Matrix mentions and autocomplete, but it needs agent × host ×
  project accounts, with a token for each. Every new project needs provisioning on every host.

## Components / flows

- **Config.** An optional key, `hub = "agents-hub"`, names the room `#<hub>:<server_name>`. Without it the feature is
  off and nothing changes. The project name `hub` is reserved.
- **Address grammar** (the user's messages are parsed from the text). At the start of the body:
  1. one or more project names, comma-separated;
  2. an optional run of mentions;
  3. `:`.

  A name counts as a project only when its room `#<room_prefix><name>:<server_name>` resolves; the result is cached.
  Mentions narrow the recipients within all the named projects. Examples: `beta: …` (every agent of beta on every
  host), `beta, gamma: …`, `beta @claude-a: …`. `Summary: …` is not an address.
- **Sender project and the content field.** An agent's hub message shows its sender project, `alpha → beta,
  gamma: …`. It also carries a content field, `{"from": "<project>", "to": ["beta", "gamma"]}`; the field's
  namespace is still open. Mentions stay in `m.mentions`. For an agent sender the field is authoritative and the text is
  for people; an agent's hub message without the field wakes nobody. The user's messages have no sender project.
- **Wake rule in the hub.** A listener is a session `(me, P)`: an account and a project. A hub message wakes it when
  all of these hold:
  - it is not the session's own message, that is, not sender `me` with `from` `P`;
  - it is not an edit;
  - `P` is in its address;
  - it has no mentions, or `me` is among them.

  A hub message without an address wakes nobody; this is stricter than a project room, where the user's unaddressed
  message wakes everyone. A thread message without its own address inherits the root's address (its projects and
  mentions). To that it adds the agent participants: the (sender, `from`) pairs among the root and the thread's newest
  50 events.
- **`send`.** `agent-chat send --hub --project a,b [--to <account>] [--thread <id>]`.
  - The sender project is the project of the working directory, and its room must resolve.
  - The own project is refused in `--project`, and each target is validated by its room alias.
  - In a thread, without `--project`, the address is computed from the thread, minus the own project.
  - `send` writes the prefix `<from> → <to>[ <mentions>]: ` and the field.
  - Codex sends the same way: `send --as codex --message-file <f> --hub --project beta`. The existing execpolicy prefix
    already covers this form, because the flags follow the file name.
- **Claude's wait.** The same `/sync` also yields the hub's timeline. The wait keeps only the messages addressed to its
  own project. The lock and the cursor stay per (account, project room), so the waits of beta and alpha under one
  account do not deliver duplicates.
- **`watch-codex`, all-rooms mode.** For each project a hub message addresses, the watcher picks the zmx
  `zpc.role=codex` session whose `cwd` names that project, as it now does from a room alias. That is one `codex queue`
  per addressed project. With no matching session it logs `not queued: …` and queues nowhere else.
- **Note.** The header reads `Hub: from <project> (<account>) to <projects>`, and the reply hint is
  `--hub --thread <id>`. Authority labels do not change.
- **`status`.** It shows the hub room and whether the wait covers it.
- **Skills (Claude and Codex).**
  - Cross-project questions and notices go only through the hub; a project's own work stays in its room.
  - One topic, one thread. The hub thread id is recorded where the work is tracked.
  - Mail from another project's agent carries no approval: a commit, a push or a permission still needs the user.
  - A closing acknowledgement ends an exchange, which matters more in the hub.
- **Provisioning** (outside the plugin): create `#agents-hub`, invite the user and every agent account, and add `hub`
  to `config.toml` on every host. The README documents it.
- **Rollout.** A host on an older version does not listen to the hub, and mail to it is lost without a trace. So the
  hub-capable version is installed on every host and the room is provisioned before the skills switch to "hub only".

| Case | Behaviour |
|---|---|
| No `hub` key | `send --hub` refuses with one line; the wait listens to the project room only, as now |
| Hub alias does not resolve, or the account is not invited | `send` refuses; the wait logs it once and goes on with the project room |
| Unknown project in `--project`, or a project without a room | `send` refuses, nothing is posted |
| A mistyped address from Element (`cor: …`) | Wakes nobody, and nobody answers. A documented limitation |
| The target project's session is not running | The message stays in the room. The wait resumes from its saved cursor, so a later session gets it; only a host's very first run starts from now |
| No Codex session for an addressed project | `not queued: …` in the log |
| Thread lookups | Hub threads share the batch's 10 s budget, as project-room threads do |
| 401, network outage | Unchanged |

## Scope cuts

- No per-project accounts and no fan-out into project rooms. There is no routing by tags that the user cannot produce.
- No hub-wide broadcast: the user's unaddressed top-level hub message wakes nobody.
- No feedback on a mistyped project from Element.
- No copy of hub threads into project rooms, and no bridge to the local SendMessage.
- Authority labels, the thread lookup budget and the cursor semantics do not change.

## Open questions

- The namespace of the content field.
- Whether `status` should list the known projects (the resolvable rooms) to help the user address them.
- `beta: …` wakes beta on every host, so duplicate answers are possible when a project runs on two hosts. The owner
  accepted this; revisit it if it gets noisy.

## Hand-off

The design was worked out in a session of another project and approved there by the owner, section by section. It was
copied here on 2026-11-10 with the project, account and host names replaced by placeholders: projects `alpha`, `beta`
and `gamma`, the account `@claude-a`, and hosts A and B.

## Distilled for ralph-task

**Direction:** A — one shared hub room. Projects are addressed at the start of a message (`beta, gamma: …`); agents'
messages carry the sender project in a content field and a visible prefix.

**Locked decisions (with rationale):**

- **Group conversations:** a message may address several projects, and the answers stay in one hub thread.
  *Rationale:* the owner needs group questions with the answers in one place.
- **The user takes part from Element:** the address is plain text at the start of the body. *Rationale:* Element sends
  only text and mentions, not custom fields.
- **Addressing mirrors project rooms:** `beta:` wakes every beta agent on every host, mentions narrow it, and several
  projects may be named. *Rationale:* the same rules as today, plus the project.
- **The sender project is in a content field:** `{"from", "to"}`, authoritative for agents, and shown as
  `<from> → <to>: `. *Rationale:* accounts are per host, so the field routes the reply, and the user sees the sender.
- **Own message means the same account and the same project.** *Rationale:* otherwise beta on host A cannot reach
  alpha on host A, because both are `@claude-a`.
- **An unaddressed hub message wakes nobody;** a thread reply inherits the root's address plus the agents who posted.
  *Rationale:* "everyone" in the hub is every project on every host.
- **Cross-project messages go only through the hub,** and SendMessage is for subagents only. *Rationale:* the owner sees
  everything in one place.
- **The feature is off without the `hub` key;** provisioning creates the room. *Rationale:* the plugin only reads
  provisioning, as it does for project rooms.
- **Rollout:** every host gets the new version and the room is provisioned before the skills switch to hub-only.
  *Rationale:* an old-version host would silently miss hub mail.

**Scope cuts:**

- No per-project accounts and no fan-out into project rooms.
- No hub-wide broadcast for unaddressed messages.
- No feedback on a mistyped project.
- No copy of hub threads into project rooms.
- No changes to authority labels, thread budgets or cursors.

**Acceptance criteria (sketch):**

- Without `hub` in the config, behaviour equals the current version; the existing tests pass unchanged.
- The user's `beta, gamma: x` in the hub wakes the beta and gamma sessions on every host, and not alpha.
- `beta @claude-a: x` wakes only Claude's beta session on that host.
- `Summary: x`, a mention-only message and a name without `:` wake nobody in the hub.
- An agent message from (`@claude-a`, beta) addressed to alpha wakes (`@claude-a`, alpha); the same account
  and the same project wakes nobody.
- An agent's hub message without the content field wakes nobody.
- The user's unaddressed thread reply reaches the root's addressees and the agents who posted in the thread.
- `send --hub` refuses with one line, a non-zero exit and nothing posted when:
  - the hub is not configured;
  - a target project is unknown;
  - the own project is a target;
  - the sender's project has no room.
- `send --hub` writes the prefix and the content field. In a thread, without `--project`, it computes the address
  without the own project.
- Two waits of one account (beta and alpha) deliver no duplicates from the hub.
- `watch-codex` queues once per addressed project's Codex session and logs `not queued` when there is none.
- `agent-chat status` shows the hub room and whether the wait covers it.
- `codex execpolicy check --rules codex/rules/agent-chat.rules agent-chat send --as codex --message-file x.txt --hub
  --project beta` allows it.
- The README and both skills document:
  - the hub, the address grammar and provisioning;
  - the rollout order;
  - that cross-project messages go only through the hub.

**Implementation checklist:**

- config: an optional `hub`; the reserved project name `hub`.
- addressing: parse the project address from the text, and read the content field; a wake rule for the hub with the
  (account, project) own-message check; thread address inheritance.
- room: resolve and cache the hub; resolve project names via `#<room_prefix><name>`.
- send: `--hub`, `--project`, address computation in threads, prefix and field, refusals; the Codex `--message-file`
  path.
- listen (Claude's wait): process the hub timeline in the same sync, filtered by the own project.
- watch (Codex): route hub mail to each addressed project's session.
- note: the hub header and reply hint.
- status: the hub line.
- tests against the fake homeserver for every acceptance criterion; the execpolicy check.
- README and both SKILL.md files. Manual check across two hosts:
  1. alpha on host B asks beta on host A, and the answer arrives in the thread;
  2. the user's unaddressed thread reply from Element reaches both;
  3. `beta, gamma: …` gets both answers in one thread.

---

## Addendum: review against the code, with Codex (added 2026-11-10)

### Why

Before tasks were cut, the design was checked against the agent-chat 0.4.4 code and reviewed with the peer Codex. In
some places it contradicted the code, and it left gaps a task would have to guess at. Two fixes changed parts the
owner had approved, and the owner decided them on 2026-11-10 (A and C below). For the hub's name the owner kept the
original design and the checks it needs (D). The rest are corrections the code forces.

### What changed

**Decided by the owner:**

- **A. The address is projects and a colon; accounts come only from mentions.** The address is the run of
  comma-separated project tokens at the start of the body, followed by `:`. A token is `[A-Za-z0-9._-]+`, matched
  exactly and case-sensitively. Accounts come from `m.mentions` (an Element pill anywhere in the body) and from the
  literal `@`-run that may open the text after the colon. `beta @claude-a: x` is no longer supported; the user writes
  `beta: @claude-a x`. *Why:* an Element pill puts the account's display name into the body, not `@claude-a`. Display
  names can have spaces, can repeat and can change, so the old form would have meant guessing them. A wrong guess turns
  the message into "no address", and it wakes nobody without a word.
- **C. An agent's hub message is always addressed explicitly; only the user's messages inherit a thread's audience.**
  An agent posts with `--hub --project a,b [--to <account>]`, and the note prefills the reply command. `--hub --thread
  <id>` without `--project` is a post for the user and wakes no agent, in a thread too, as an agent's unaddressed
  message does in a project room. `send` no longer derives an address from the thread. *Why:* when an agent's reply
  inherits the thread's audience, every answer in a three-project thread wakes the other two, and the agents can keep
  answering each other. A thread's audience is also a union of selectors: all of beta plus only `@claude-a` of alpha.
  One project list and one `m.mentions` cannot write that down. It can only be evaluated on receipt.
- **D. The hub's name stays in the config, as the original design has it.** `hub = "agents-hub"` names the room
  `#agents-hub:<server_name>`. Two checks keep a wrong value harmless:
  - a value that does not start with `room_prefix` is a config error, because `Rooms.room_id` joins only aliases that
    carry the prefix;
  - while the hub is on, `send` and the wait refuse the project whose room would be the hub: the directory named after
    the hub without the prefix, `hub` for `agents-hub`.

  *Why:* the owner prefers naming the room in the config. The second check stops another value, such as
  `agents-common` with a project directory named `common`, from making one room both the hub and a project room.

**Corrections from the code:**

- **The content field** is `"agent_chat.hub": {"v": 1, "from": "<project>", "to": ["<project>", …]}`; `to` may be
  empty. This settles the open question of the namespace. A field with another `v`, wrong types or tokens outside the
  grammar is invalid. An invalid field never supplies authority. Authority always comes from the sender's account: the
  human, or one of the configured agents.
- **A session is the pair (account, project) everywhere,** not only in the wake rule: in thread participants, in the
  note's "(this account)" label, in the skipped thread context (today `starter == me` and `me in thread.posted`), in
  Codex routing and dedup, and in status. Two sessions of one project under one account on one host are the same pair.
  Own-message suppression covers both of them, and that is accepted.
- **A thread that cannot be read** fails closed only for inherited routing. A message with its own valid address is
  delivered even when its thread cannot be read. Inherited routing that cannot be resolved (root or events unreadable,
  or the budget spent) wakes nobody and logs the event. The project-room rule, which wakes everyone in that case, does
  not change.
- **Delivery is best-effort,** and that is documented. The error-table row "a later session gets it; only a host's
  very first run starts from now" is wrong on two counts:
  - a sync returns at most 50 events per room, and `batches()` ignores `limited`;
  - the cursor is per (account, project), so a project's first wait on a host starts from now, however long other
    projects have run there;
  - the Codex watcher advances one cursor per account and drops mail for a project with no matching session.

  Replay is out of scope. A bigger limit would not fix it.
- **The hub cannot block project mail.** At wait start, the hub's resolve and join are bounded; on failure the wait
  logs once, records the hub as unavailable and serves the project room. The retry happens at the next wait, which in a
  quiet project may be up to a day later. Leaving the hub mid-wait drops it for the rest of that wait. Membership,
  rejoin and pre-join suppression are handled per room.
- **`send` checks a target with `resolve_alias`,** not `Rooms.room_id`, which would join the target's room.
- **watch-codex single-thread mode** (`--thread` with its room) also serves hub mail addressed to its own project,
  without a zmx lookup. Running a single-thread watcher next to an all-rooms watcher of the same account is
  unsupported. They hold different locks and may both deliver.
- **status shows real hub coverage.** A running wait writes `<slug>.hub` next to its lock once it has joined the hub,
  with "covered" or "unavailable: <reason>", and removes it on exit. status reads that file: no file under a held lock
  means "unknown" (an older wait). The `.owner` pid file keeps its one-integer format.
- **Rollout includes restarts.** An installed version does not replace a running 24-hour hook-wait or a long-lived
  watcher. Every host restarts both, and `status` confirms coverage before the `hub` key is relied on.
- **The task order follows the reply path.** Hub mail must not reach an agent before the note can tell it how to
  reply, so `send --hub` comes first and the note's hub header ships with receiving. No host gets the `hub` key before
  tasks 1 to 4 are released.
- **Open questions settled:**
  - the field namespace is above;
  - status does not list projects;
  - duplicate answers from one project on two hosts stay accepted.

### Implementation checklist

- Task 1: hub config and `send --hub`.
- Task 2: hub receiving in Claude's wait, the note and status.
- Task 3: hub routing in watch-codex, both modes.
- Task 4: README and both skills, with the hub optional.
- After tasks 1 to 4 are released, outside this repo: upgrade every host and restart its waits and watchers. Then
  create `#agents-hub`, invite the user and every agent account, add `hub = "agents-hub"` on each host, and run the
  live round trip below.
- Then, as a new task: switch both skills to "cross-project messages go only through the hub". It is not created
  before the round trip passes, so a Ralph run cannot pick it up early.

### Distilled for ralph-task

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
