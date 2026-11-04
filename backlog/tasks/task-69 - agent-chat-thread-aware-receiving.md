---
id: TASK-69
title: agent-chat thread-aware receiving
status: Done
assignee: []
created_date: '2026-11-04T12:06:00Z'
updated_date: '2026-11-04T12:51:00Z'
labels:
  - feature:agent-chat-threads
dependencies:
  - TASK-68
priority: medium
ordinal: 69000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
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
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 An unaddressed user message in a thread whose root or newest 50 replies include agents wakes only those agents (tested for Claude's wait and for watch-codex)
- [x] #2 An unaddressed user message in a thread with no agent seen wakes every listener, and an agent the root mentions counts as one of the thread's agents (tested)
- [x] #3 An agent seen only before the newest 50 replies is not one of the thread's agents (tested)
- [x] #4 A mention inside a thread wakes exactly the mentioned agents, and an agent's unaddressed thread message wakes nobody (tested)
- [x] #5 When a lookup fails or the batch budget is spent, addressed mail is still delivered and the user's unaddressed thread message wakes every listener; a failure is fetched once per thread per batch; a 401 during a lookup behaves as a 401 today (tested)
- [x] #6 A lookup during an outage ends within the per-batch budget and does not block the batch (tested with a fake clock or a fake server that does not answer)
- [x] #7 watch-codex makes no thread lookup for a room it does not serve (tested by counting the fake server requests)
- [x] #8 The note groups mail by thread, shows the root cut to 300 characters with an ellipsis, shows an agent new to the thread the last 3 replies before the first mail excluding this batch, says when that context was left out, and quotes every body line (tested)
- [x] #9 Reply hints in the note carry full ids without $, and the Codex note carries the Codex reply line with --thread (tested)
- [x] #10 Both SKILL.md files and plugins/agent-chat/README.md describe the thread wake rule, the note and the reply-in-thread rule, and the README How it works table has a Threads row
- [x] #11 The agent-chat version is 0.4.0 in both plugin.json files and in the version pin; uv run ruff check . is clean and uv run pytest plugins/agent-chat passes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: matrix.Client.request gains tries= (bounded mode: at most N tries, socket timeout capped by the deadline, NetworkError once the deadline is spent) and Client.thread(room, root, deadline) = GET event + GET relations m.thread dir=b limit=50. New module threads.py: Thread (root id, root event or None when unreadable, chronological window, agents) and Budget (one 10 s budget per batch, cache keyed by (room, root), failures cached, AuthError re-raised). addressing.wakes() returns Wake.NO / YES / THREAD. SyncLoop.mail(room, events, budget) looks up every thread with mail; candidates() lets watch-codex check _served before any lookup. note.render groups by thread (root cut at 300 chars + ellipsis, earlier context of 3 replies when this account has not posted in the window, left-out line, failed-lookup heading, top-level hint) with ids via note.bare(). Tests in addressing/hook/codex/transport; docs + 0.4.0 bump.

Commit: `c30d4fc` - task-69: agent-chat wakes the user's thread messages for the thread's agents and groups the note by thread

Commit: `e33780d` - task-69: watch-codex makes every lookup of a batch before its first delivery, and the budget runs on the client's clock

Implemented: matrix.Client.request gains a bounded mode (tries=, socket timeout capped by the deadline, NetworkError once it is spent), Client.now() and Client.thread() (GET event + GET v1 relations m.thread dir=b limit=50). New threads.py: Thread (root, window oldest first, agents = agent accounts among root sender, root mentions and window senders; posted = root sender + window senders) and Budget (one 10 s budget per batch on the client's clock, cache per (room, root), failures cached, AuthError re-raised). addressing.wakes() returns Wake.NO/YES/THREAD. SyncLoop.candidates() + mail(room, events, budget); every thread with mail is looked up. watch-codex _batch_mail(): _served for every room first, then the budget and all lookups, then deliveries, so neither an unserved room nor a slow codex queue spends the budget. note.render groups by thread: root cut at 300 chars + ellipsis as history, up to 3 earlier replies when this account has not posted in the thread (a root mention alone still gets the context), a left-out line when the first mail is outside the window, the failed-lookup heading, the top-level hint, ids without the dollar (bare() moved to note.py), and Claude/Codex reply lines with --thread. The fake homeserver gained lookup_fault (stall/drop/401) and lookups(room). Docs: both SKILL.md files, the plugin README (Addressing, Threads, comparison row, Codex watcher), the root README, and the zmx-peer-chat README's mirrored agent-chat cell (README only, no version bump). marketplace.json unchanged; it does not describe the wake rule. Version 0.4.0. Final: ruff clean, pytest plugins/agent-chat 169 passed 5 skipped. Flaky timing test test_a_wait_takes_over_the_lock_of_an_orphaned_wait[ps] failed once under load; it passes alone with and without the change. Review: ralph:task-reviewer CHANGES REQUESTED (score 5: the lookup budget also counted deliveries in watch-codex; plus 2 minors), all fixed in e33780d; re-review APPROVED (score 9). Open minor, accepted: a 401 during a lookup in watch-codex now loses that whole batch's mail, not just one room's; the watcher exits 1 on a 401 anyway. design/agent-chat-threads-brainstorm.md stays untracked as found.
<!-- SECTION:NOTES:END -->
