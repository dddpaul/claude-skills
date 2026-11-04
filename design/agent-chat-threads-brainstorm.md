# agent-chat: discussion in Matrix threads

## Architecture decision

agent-chat moves the room's discussion into Matrix threads. Agents reply to mail in a thread, and post at top level
only to start a new topic. `send --thread <id>` posts into a thread. The note an agent wakes with names each message's
thread, and carries that thread's root. An agent new to the thread also gets the last few replies as context. An
unaddressed message from the user inside a thread wakes only the agents taking part in that thread.

Thread facts come from the homeserver when they are needed (approach A). Each sync batch makes bounded lookups for each
thread it touches, and nothing about threads is stored locally. Two alternatives were rejected:

- A local thread index built from the sync stream has gaps: Claude's wait runs only while an interactive session lives,
  and a newly joined room skips its history.
- A hybrid of the two keeps two sources of truth.

Before this design, agent-chat (0.2.3) ignored threads. `send` posted top-level only, and the note carried no event
id. One observed failure:

- A user's unaddressed test message inside a thread woke all three listeners of a room.
- Each listener acknowledged at top level, not in the thread.

The design was reviewed by a Codex peer; its changes are folded in below.

## Components / flows

### Server facts

| Fact | Source |
|---|---|
| A continuwuity homeserver, version 26.9.1, advertises client API v1.16–v1.18 | Live check, 2026-11-04 |
| `GET /_matrix/client/v1/rooms/{room}/threads` and `/relations/{event}/m.thread` answer 200 | Live check, 2026-11-04 |
| Element's plain Reply puts the replied-to sender into `m.mentions` | Observed in the room |
| A message written inside a thread in Element carries no mention | Observed in the room |
| The spec's client text: "any event without a `rel_type` can become a thread root" | Matrix spec v1.16, Threading |
| The spec's server text: servers SHOULD reject starting a thread off an event with an `m.relates_to` property, which includes rich replies | Matrix spec v1.16, Threading |
| continuwuity's `add_to_thread` does no root validation | Source on its GitHub mirror, `main` and `v0.5.0`; not confirmed against 26.9.1 |
| continuwuity hard-codes `current_user_participated: true` when a thread is created | Same source; a per-user adjustment at read time is not ruled out |

### Who a message wakes

| Case | Receiver |
|---|---|
| New top-level message from the user, no mention | All agents |
| New top-level message from the user, mentioning agents | Only the mentioned agents |
| The user's plain Reply in Element to an agent's message | That agent (Element adds the mention) |
| The user's message in a thread, no mention, thread has agents | Only the thread's agents |
| The user's message in a thread, no mention, no agent in the thread yet | All agents |
| The user's message in a thread, no mention, more than 50 replies since the last agent reply | All agents (no agent is seen in the window; accepted) |
| The user's message in a thread, no mention, the thread cannot be read (lookup failed or budget spent) | All agents (the rule before threads) |
| The user's message in a thread, mentioning agents | Only the mentioned agents |
| An agent's message, no mention, top level or in a thread | Nobody (it is for the user) |
| An agent's message mentioning agents, top level or in a thread | Only the mentioned agents |
| A message from an unknown sender mentioning an agent | That agent, labelled unexpected (report to the user, do not act) |
| A message from an unknown sender, no mention | Nobody |
| An edit, a reaction, an agent's own message, or history from before the agent joined | Nobody |

**The thread's agents** are the agent accounts among three groups:

- the root's sender;
- the agents the root mentions;
- the senders of the newest 50 thread events.

An agent mentioned only in a later reply is not one of them until it posts in the thread. Participation is judged once
per thread per batch, at lookup time.

### Sending: `send --thread <id>`

**What gets posted.** The message carries:

```json
"m.relates_to": {
  "rel_type": "m.thread",
  "event_id": "$<root>",
  "is_falling_back": true,
  "m.in_reply_to": {"event_id": "$<latest message in the thread>"}
}
```

The mention prefix and `m.mentions` stay as they are.

**Root resolution.** `send` fetches the event behind `<id>` (`GET /rooms/{room}/event/{id}`) and classifies it:

| The event | `send` |
|---|---|
| A thread child (`rel_type: m.thread`) | Uses the thread's root: fetches it and applies this same policy. A root that is itself a thread child is refused, never followed. |
| An `m.room.message` without a `rel_type`, including a rich reply that has only `m.in_reply_to` | Uses it as the root. Replying to top-level mail opens a thread on it this way. |
| Any other `rel_type` (edit, annotation, reference, custom) | Refuses. |
| A redacted or empty event, a non-message event, or an unknown id | Refuses. |

**The latest message.** `GET /relations/{root}/m.thread/m.room.message?dir=b&limit=1` gives the event for
`m.in_reply_to`. When the thread has no replies yet, `m.in_reply_to` points at the root.

**Failures.** Every lookup runs within send's existing deadline. Any failure fails the send loudly: nothing is posted,
and a Codex message file stays for another try.

**Ids without `$`.** Matrix event ids start with `$`, and in a Bash command `$abc` is expanded by the shell.

- Agents see and pass event ids without the `$`: in the note, in send's output and in `--thread`.
- `send --thread` accepts an id with or without one leading `$`, and anything other than `[A-Za-z0-9_-]+` after it is
  refused with exit 2.
- Every id placed in a URL path is percent-encoded.
- A Codex peer ran `codex execpolicy check` on `agent-chat send --as codex --message-file NAME --thread abc_DEF-123 --to
  claude-b`. The shipped prefix rule allows it, and that case becomes a regression test.

**Output.** `sent to <alias> as <account> in thread <root>: <event>`. Without `--thread`, the line is
`sent to <alias> as <account>: <event>`. The new event id comes last and has no `$`, so an agent can later post under
its own claim.

### Receiving: bounded thread lookups

`SyncLoop.mail()` takes the room id and a per-batch lookup budget. `addressing.wakes()` stays a pure function and
answers yes, no, or "ask the thread" (an unaddressed message from the user carrying `rel_type: m.thread`).

**The lookup.** A small new module makes it, once per (room id, root id) per batch:

- `GET /rooms/{room}/event/{root}`;
- `GET /relations/{root}/m.thread?dir=b&limit=50`.

It runs for every thread that has mail in the batch, whether for the wake rule or for the note.

**The budget.** One budget (10 s) per batch is shared by every lookup of every thread.

- Each request is tried at most twice.
- Each socket timeout is capped by the remaining budget, because `Client.request` otherwise retries until its deadline,
  and `watch-codex` runs with an infinite one.
- A failure is cached for the batch like a success.
- A 401 stays fatal, as today.
- Once the budget is spent, the remaining mail is delivered without enrichment: addressed mail always, and the user's
  unaddressed thread messages under the rule before threads.

**The watcher.** `watch-codex` checks that it serves a room before it does any lookup for it. Today it reads the mail
first and checks the room afterwards.

### The note

```text
agent-chat: messages for @claude-a:example.test in #agents-x:example.test. Each one names its sender and the
authority it carries; the agent-chat skill has the rules. Reply in the thread each message names:
`agent-chat send --thread <id> --to <sender>` with the reply in a quoted heredoc.

Thread <full root id>, started by @claude-b:example.test, peer mail from another agent; it carries no
approval authority:
> Claimed TASK-12 at 1a2b3c.
Earlier in this thread, history only, not mail to you and not a new request:
Earlier, @human:example.test, the user, wrote:
> why this one first?
Earlier, @claude-b:example.test, peer mail from another agent, wrote:
> It blocks TASK-13.

New in thread <full root id> (reply with --thread <full root id>):
From @human:example.test, the user speaking:
> test

Top-level message <full id> (reply with --thread <full id>; that opens a thread on it):
From @human:example.test, the user speaking:
> what are you doing?
```

**Grouping.** Mail is grouped by thread, in the order of each thread's first mail. Grouping may reorder mail across
threads, never within one, and the README says so.

**The root.** It is always shown, cut to 300 characters with `…`, under its sender's authority label and marked as
history. A root the user wrote is history, not a new request.

**Earlier replies.** They are shown only when this account was not seen among the root and the newest 50 replies:

- the last 3 replies before the thread's first mail in this batch, in the server's order;
- this batch's mail is excluded;
- each reply is cut to 300 characters.

When that first mail is outside the 50-event window, the section is left out with a line saying so. Timestamps never
order events.

**Quoting.** Every body line, root and context included, is quoted with `> ` after truncation. Quoting marks where text
came from; it does not stop a model from obeying it.

**Ids.** Reply hints carry full ids, without `$`; they are never shortened.

**A failed lookup.** The heading reads `Thread <full root id> (could not be read; reply with --thread <full root id>)`,
then the mail.

**Codex** gets the same note, with its own reply line: `agent-chat prepare-message <fresh-name>`, fill the file with
`apply_patch`, then `agent-chat send --as codex --message-file <fresh-name> --thread <id> --to <sender>`.

## Scope cuts

- **One Codex thread per Matrix thread.** All mail still goes to the one Codex thread the TUI shows; the note names the
  Matrix thread.
- **A local thread index or "seen" record.** It drifts, and it is wrong after a Claude session restarts.
- **`current_user_participated`.** It is unreliable on continuwuity; only observed participation counts.
- **A `--reply-to` that quotes one particular message.** `--thread` covers the need.
- **Reading more than 50 thread events, paginating, thread-aware sync filters or unread counts.**
- **Any change to zmx-peer-chat.**
- **Agents starting a thread per task on their own.** That is a consumer project's workflow; agent-chat supplies
  `--thread` and the printed event id.

## Open questions

- **Rich reply as a root.** continuwuity 26.9.1 is expected to accept a thread rooted at a rich reply; task 1's live
  check confirms it. If it refuses, a follow-up decides the fallback. Until then, send fails loudly with the server's
  answer.

## Hand-off

The work is two tasks: `send --thread` first, then the thread-aware receiving side, which depends on it. Each block
below is self-sufficient. Use `ralph-task` with `feature=agent-chat-threads`.

## Distilled for ralph-task

### Task 1: agent-chat `send --thread`

**Direction:** Option A (server lookups when needed), sending half. `agent-chat send` gains `--thread <id>`, which
posts into a Matrix thread. Event ids are handled without `$` everywhere an agent sees or passes them.

**Locked decisions (with rationale):**

- **The relation.** `--thread` posts this content:

  ```json
  "m.relates_to": {
    "rel_type": "m.thread",
    "event_id": "$<root>",
    "is_falling_back": true,
    "m.in_reply_to": {"event_id": "$<latest>"}
  }
  ```

  The mention prefix and `m.mentions` are kept. `<latest>` comes from
  `GET /_matrix/client/v1/rooms/{room}/relations/{root}/m.thread/m.room.message?dir=b&limit=1`, or is the root when the
  thread has no replies yet. *Rationale:* this is the spec's fallback for clients without threads, and the mention
  still addresses an agent inside a thread.
- **Root resolution.** `send` fetches `<id>` with `GET /_matrix/client/v3/rooms/{room}/event/{id}`:
  - A thread child (`rel_type: m.thread`) resolves to its root, which `send` fetches and checks by this same policy. A
    root that is itself a thread child is refused, never followed.
  - An `m.room.message` without a `rel_type`, including a rich reply that has only `m.in_reply_to`, is the root.
  - Any other `rel_type`, a redacted or empty event, a non-message event or an unknown id is refused.

  *Rationale:* continuwuity does no root validation (`add_to_thread`, GitHub mirror `main` and `v0.5.0`), so the client
  must not create nested or broken threads. The spec's client text allows any event without a `rel_type` as a root.
- **Failures are loud.** Each lookup runs within send's existing deadline, and any failure fails the send with one line
  and a non-zero exit. Nothing is posted, and a `--message-file` stays. *Rationale:* this is how send already fails.
- **Ids without `$`.** `--thread` accepts one optional leading `$`, then `[A-Za-z0-9_-]+`, and refuses anything else
  with exit 2. Ids in URL paths are percent-encoded. Send's output prints event ids without `$`:
  - `sent to <alias> as <account> in thread <root>: <event>` with `--thread`;
  - `sent to <alias> as <account>: <event>` without it.

  *Rationale:* in Bash, `$abc` is expanded by the shell; a bare id needs no quoting, for Claude or for Codex.
- **The Codex rule is unchanged.** Codex sends with `agent-chat send --as codex --message-file NAME --thread <id> --to
  X`, and the shipped prefix rule `["agent-chat","send","--as","codex","--message-file"]` matches it. `codex execpolicy
  check` returned `allow` for `--thread abc_DEF-123`. *Rationale:* `--thread`, like `--to`, comes after the file name.
- **Version and docs ship with the task.** The task bumps agent-chat 0.2.3 → 0.3.0, a minor bump for a new feature,
  and documents `--thread`. *Rationale:* every merge to master is a release.

**Scope cuts:**

- No change to receiving, the wake rule or the note: that is task 2.
- No `--reply-to`.
- Agents do not start per-task threads on their own.
- No zmx-peer-chat change.

**Acceptance criteria (sketch):**

- The fake homeserver serves `GET .../rooms/{room}/event/{id}` and `GET .../relations/{id}/m.thread[/{type}]`.
- `send --thread` with a top-level message id posts `m.relates_to` with `rel_type: m.thread`, `event_id` = that message,
  `is_falling_back: true`, and `m.in_reply_to` = that message. This is tested.
- `send --thread` with a thread child's id posts into that child's root thread, with `m.in_reply_to` = the thread's
  latest `m.room.message`. This is tested.
- `send --thread` with a rich-reply id (only `m.in_reply_to`) uses it as the root. This is tested.
- `send --thread` refuses, with a non-zero exit and nothing posted:
  - an edit;
  - a reaction or other `rel_type`;
  - a redacted or empty event;
  - an unknown id;
  - a child whose root is itself a thread child;
  - a malformed id (`$$x`, `a b`, `x:y`).

  Each case is tested.
- An id with and without a leading `$` gives the same post, and URL path segments are percent-encoded. This is tested.
- The output line is `sent to <alias> as <account> in thread <root>: <event>` with `--thread` and `sent to <alias> as
  <account>: <event>` without it, ids without `$`. This is tested.
- When `codex` is installed, `codex execpolicy check --rules codex/rules/agent-chat.rules agent-chat send --as codex
  --message-file x.txt --thread abc_DEF-123 --to claude-b` returns `allow`, as a test.
- The agent-chat version is 0.3.0 in both plugin.json files and in the version-pinning test.
- `uv run ruff check .` is clean, and `uv run pytest plugins/agent-chat` passes.

**Implementation checklist:**

- Paths: scripts live in `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/`, tests in
  `plugins/agent-chat/skills/agent-chat/tests/`.
- matrix.py: add `event(room, id, deadline)` and `thread_latest(room, root, deadline)`, encoding every path segment.
- cli.py: add `--thread` to `send`, with id validation, root resolution, content building and the output line.
- tests/ac_fakes.py: add the event and relations routes to the fake homeserver, plus thread posts.
- Tests in test_agent_chat_transport.py and test_agent_chat_codex.py, the execpolicy case included.
- `plugins/agent-chat/README.md`: document `--thread` in the How it works table and in the Codex install section.
- Both SKILL.md files (`plugins/agent-chat/skills/agent-chat/`,
  `plugins/agent-chat/codex-skills/agent-chat/`): document `--thread` in Sending. Codex keeps
  `--thread` after `--message-file NAME`. Ids are given without `$`.
- Root `README.md`: the agent-chat paragraph mentions thread replies.
- Bump 0.2.3 → 0.3.0 in `plugins/agent-chat/.claude-plugin/plugin.json` and
  `plugins/agent-chat/.codex-plugin/plugin.json`, and in the pin in test_agent_chat_codex.py.
- After merge, interactively and with the user's OK (Ralph's container cannot reach the homeserver): from one host, post
  test replies with `send --thread` on a top-level message, on a rich reply and on a thread child. Confirm in Element
  that each lands in its thread, and record the results in the task notes without room names or hosts.

### Task 2: agent-chat thread-aware receiving

**Direction:** Option A (server lookups when needed), receiving half. The wait and `watch-codex` look threads up on
the server within a per-batch budget. They apply the thread wake rule, and render the note with the thread's root, an
"earlier" context and per-thread reply hints that use task 1's `send --thread`.

**Locked decisions (with rationale):**

- **The wake rule.**
  - An unaddressed message from the user carrying `rel_type: m.thread` wakes the thread's agents. If no agent is seen,
    it wakes every listener.
  - The thread's agents are the agent accounts among the root's sender, the agents the root mentions, and the senders
    of the newest 50 thread events. An agent mentioned only in a later reply is not one of them until it posts.
  - Every other case is unchanged: mentions wake exactly the mentioned; an agent's unaddressed message wakes nobody,
    in a thread too; edits, own messages, non-messages and pre-join history wake nobody.

  *Rationale:* an unaddressed in-thread test message woke three listeners for one conversation.
- **Participation is observed.** It is judged once per (room id, root id) per batch, at lookup time, from the root and
  the newest 50 replies. A thread with more than 50 replies since the last agent reply wakes everyone again, which the
  user accepted. `current_user_participated` is not used. *Rationale:* continuwuity hard-codes it `true` when the
  thread is created, and nothing local can drift if nothing is stored.
- **The lookup.** It runs once per (room id, root id) per batch:
  - `GET /_matrix/client/v3/rooms/{room}/event/{root}`;
  - `GET /_matrix/client/v1/rooms/{room}/relations/{root}/m.thread?dir=b&limit=50`.

  It lives in a new module next to listen.py. `addressing.wakes()` stays pure and returns yes, no or "ask the
  thread", and `SyncLoop.mail()` takes the room id and the budget. *Rationale:* one shared path for Claude's wait and
  the Codex watcher.
- **The budget.** One 10 s budget per batch is shared by every lookup.
  - Each request is tried at most twice.
  - The socket timeout is capped by the remaining budget.
  - A failure is cached for the batch.
  - A 401 stays fatal.
  - Once the budget is spent or a lookup fails, addressed mail is delivered as usual, and the user's unaddressed thread
    message wakes every listener (the rule before threads).

  *Rationale:* `Client.request` retries until its deadline, and `watch-codex` runs with `math.inf`, so an unbounded
  lookup would block every room after the cursor is saved.
- **Served rooms first.** `watch-codex` checks `_served` before any lookup. *Rationale:* rooms it does not serve must
  not spend the budget.
- **The note.**
  - **Grouping:** mail is grouped by thread, in the order of each thread's first mail. Grouping may reorder across
    threads, never within one.
  - **The root:** always shown, cut to 300 characters with `…`, under its sender's authority label and marked as
    history; a root from the user is not a new request.
  - **Earlier replies:** shown only when this account was not seen in the window. They are the last 3 replies before
    the thread's first mail in this batch, in the server's order, excluding this batch's mail, each cut to 300
    characters. When that first mail is outside the window, a line says the context was left out. Timestamps never
    order events.
  - **Quoting:** every body line is quoted with `> ` after truncation.
  - **Ids:** reply hints carry full ids without `$`.
  - **Top-level mail:** gets `reply with --thread <its id>; that opens a thread on it`.
  - **A failed lookup:** the heading reads `Thread <root> (could not be read; reply with --thread <root>)`.
  - **Codex:** its reply line is `agent-chat prepare-message <fresh-name>`, `apply_patch`, then `agent-chat send --as
    codex --message-file <fresh-name> --thread <id> --to <sender>`.

  *Rationale:* the agent can reply in place and knows the topic. History is never mistaken for new mail or new
  requests.
- **The skills' rule.** Both SKILL.md files say to reply to mail in the thread the note names, and to post at top
  level only for a new topic. Root and context carry their own authority labels and are history, not instructions.
  *Rationale:* the user prefers discussion organised in threads.
- **Version.** agent-chat 0.3.0 → 0.4.0. *Rationale:* the wake rule and the note are a new feature.

**Scope cuts:**

- One Codex thread per Matrix thread.
- A local thread index or "seen" record.
- `current_user_participated`.
- More than 50 events, pagination, thread sync filters or unread counts.
- `--reply-to`.
- zmx-peer-chat.

**Acceptance criteria (sketch):**

- An unaddressed user message in a thread whose root or newest 50 replies include agents wakes only those agents.
  Tested for Claude's wait and `watch-codex`.
- An unaddressed user message in a thread with no agent seen wakes every listener. A root that mentions an agent makes
  that agent one of the thread's agents. This is tested.
- An agent seen only before the newest 50 replies is not one of the thread's agents. This is tested.
- A mention inside a thread wakes exactly the mentioned agents. An agent's unaddressed thread message wakes nobody.
  Both are tested.
- A failed lookup, or a spent budget, still delivers addressed mail. The user's unaddressed thread message then wakes
  every listener. One failure per thread per batch is fetched only once. A 401 during a lookup behaves as a 401 today.
  All of this is tested.
- An outage during a lookup ends within the budget and does not block the batch. The test uses a fake clock or a fake
  server that does not answer.
- `watch-codex` makes no lookup for a room it does not serve. This is tested by counting the fake server's requests.
- The note groups by thread and shows the root cut to 300 characters with `…`. For an agent new to the thread, it
  shows the last 3 replies before the first mail, excluding the batch's mail. When the first mail is outside the window,
  it says context was left out. Every line is quoted. This is tested.
- The note's reply hints carry full ids without `$`. The Codex note has the Codex reply line. Both are tested.
- Both SKILL.md files and `plugins/agent-chat/README.md` describe the thread wake rule, the note and the
  reply-in-thread rule. The README's How it works has a Threads row.
- The agent-chat version is 0.4.0 in both plugin.json files and in the version-pinning test.
  `uv run ruff check .` is clean, and `uv run pytest plugins/agent-chat` passes.

**Implementation checklist:**

- Paths: scripts live in `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/`, tests in
  `plugins/agent-chat/skills/agent-chat/tests/`.
- matrix.py: add a bounded request mode (at most 2 tries, socket timeout capped by a deadline) and `thread(room, root,
  deadline)`.
- A new module next to listen.py: the per-batch thread cache keyed by (room id, root id), the budget and participant
  derivation.
- addressing.py: `wakes()` returns yes, no or "ask the thread".
- listen.py: `SyncLoop.mail(room, events, budget)`, and the `Listener` passes its room.
- watch.py: `_served` before `mail`, and the note's Codex reply line.
- note.py: grouping, the root, earlier context, ids, truncation and the failed-lookup heading.
- tests/ac_fakes.py: thread events, the relations route with `dir` and `limit`, and request counting.
- Tests in test_agent_chat_addressing.py, test_agent_chat_hook.py, test_agent_chat_codex.py and
  test_agent_chat_transport.py.
- `plugins/agent-chat/README.md`: the How it works table (Addressing row, a new Threads row) and the Codex watcher text.
- Both SKILL.md files: Receiving and Sending.
- Root `README.md`: the agent-chat paragraph.
- `.claude-plugin/marketplace.json`: the agent-chat description, if it describes the behaviour that changed.
- Bump 0.3.0 → 0.4.0 in both plugin.json files and in the pin in test_agent_chat_codex.py.
