---
id: TASK-71
title: >-
  agent-chat Codex note fits codex queue, alias failures stay per room, own root
  labelled
status: Done
assignee: []
created_date: '2026-11-04T14:51:00Z'
updated_date: '2026-11-04T15:23:00Z'
labels:
  - feature:agent-chat-threads
dependencies: []
priority: high
ordinal: 71000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

A review of the threads feature (TASK-68, TASK-69, TASK-70; agent-chat 0.4.1) found three defects and one doc gap.
Tests reproduced each of them.

1. **The Codex note can overflow its argument, and then the mail is lost.** watch.py `codex_queue()` passes the whole
   note as one `--message` argument. Codex 0.166's `codex queue` has no stdin or file input, only `--message`. Linux caps
   a single argument at MAX_ARG_STRLEN, 131072 bytes. `note.render()` cuts each root and earlier reply to 300
   characters, which is not 300 bytes, and puts no limit on the whole note. Measured for 50 threads in one batch, each
   with one short new message, a 400-character root and 3 earlier 400-character replies:
   - ASCII text: 108300 bytes;
   - 301 emoji per body (4 bytes each): 288653 bytes;
   - Cyrillic (2 bytes a character): over 131072 at about 30 threads.

   When the watcher catches up on such a batch, `codex queue` fails with E2BIG. `_deliver` logs "not queued", and the
   mail is lost, because the cursor was saved before delivery.
2. **One failing alias lookup holds up every room's mail.** `CodexWatcher._batch_mail()` calls `_served(room,
   deadline)` for every room that has candidate mail, before it delivers anything. `_served` calls `_alias_of(room,
   deadline)`, which calls `client.canonical_alias(room, deadline)` with run()'s deadline, `math.inf`. For a room whose
   alias is not cached, a network, 5xx or 429 failure is retried until `keep_going` turns false, that is, until the
   watcher shuts down. Meanwhile the mail of rooms already served in the same batch is not delivered. Before TASK-69,
   earlier rooms in the batch were delivered first; the unbounded retry itself is older.
3. **A thread the agent started itself gets another agent's label.** `note._thread()` labels the root with
   `authority(starter, cfg)`. This host's own accounts are in `cfg.agents`, so a thread the listening agent started
   reads "Thread X, started by <me>, peer mail from another agent; it carries no approval authority …".
4. **README gap.** The Threads row of the plugin README says "a 401 ends the wait as it does on a sync". It does not
   say that the batch's mail is lost, because its cursor is already saved.

## Locked decisions

### Note size

This applies to the Codex path only. Claude's hook-wait note goes to stderr and stays as it is.

- **The limit.** A constant `QUEUE_BYTES = 100_000` gives the maximum UTF-8 bytes of one `codex queue --message`
  text, below 131072 with a margin.
- **The function.** A new function, for example `note.notes(messages, cfg, me, alias, reply, limit) -> list[str]`,
  returns one or more notes. Each one is at most `limit` bytes when encoded as UTF-8, and they come in order:
  1. Render as today. If it fits, return that one note, so the output is unchanged.
  2. Otherwise, render with no earlier context in any thread: drop every "Earlier in this thread" part and every
     left-out line. The roots stay, because the root is always shown. If that fits, return that one note.
  3. Otherwise, split the messages, in their original order, into consecutive runs. Render each run, with no earlier
     context, as a full note with its own header, taking as many messages as fit. Each note groups by thread as
     `render` does, and every message of run k comes before every message of run k+1.
  4. A single message whose note does not fit on its own, even with no earlier context, has its body cut to fit.
     The cut falls on a UTF-8 character boundary, and every remaining body line is still quoted with `> `. Right after
     the quoted body comes one line of agent-chat's own, unquoted like the headers:

```text
[cut by agent-chat: <N> more bytes of this message were left out; it is event <id without $>. Ask in its thread or tell the user.]
```

- **Delivery.** `_deliver` queues each note with its own `codex queue` call, in order. A successful call logs
  `queued … (part k of n)` when n > 1. At the first failure it logs `not queued: … (parts k-n of n): <error>` and
  stops.
- **Docs.** The Codex SKILL.md and the plugin README's Codex watcher text say:
  - a long batch can arrive as several notes, each with its own header;
  - a message cut to fit ends with the cut line;
  - an agent that sees the cut line asks in the thread or tells the user, and never guesses the rest.

### Alias prepass

- **A finite deadline.** In `_batch_mail`, the `_served` call gets `min(deadline, self.client.now() + ALIAS_SECONDS)`
  with `ALIAS_SECONDS = 10.0`. That is the client's clock, the one its request deadlines use.
- **Catch network failures.** `_alias_of` catches a `NetworkError` the way it already catches a `MatrixError`. It
  logs `cannot read the alias of <room>: <error>; its mail in this batch is not delivered`, returns None and caches
  nothing.
- **What stays.** An `AuthError` is still raised. Rooms whose alias is known are delivered whatever happens to the
  others. A shutdown still ends the watcher promptly.

### Own root label

- **The label.** When the root's sender is `me`, `_thread` heads it `Thread <id>, started by <me> (this account); the
  root is history, not a new request:` instead of using the authority label.
- **Why only the root.** Earlier replies by `me` cannot appear: once `me` is in the thread's posted set, no earlier
  context is shown. Mail from `me` never wakes `me`.
- **Other accounts.** The authority label is unchanged for every other sender, including this host's other account.

### README 401 line

The Threads row says that a 401 during a thread lookup ends the wait as on a sync, and that the batch's mail is not
delivered because its cursor is already saved.

### Version

agent-chat 0.4.2 in both plugin.json files and in the version pin in test_agent_chat_codex.py.

## Housekeeping

Commit the untracked review file `design/agent-chat-threads-review-2026-11-04.md` as it is.

## Scope cuts

- **No total deadline.** The total-elapsed-time fix for lookups is a separate task.
- **The Claude note is unchanged.**
- **No change to the sync timeline limit or the cursor policy.**
- **No change to the wake rule.**

## Paths

- Scripts are in `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/` (note.py, watch.py).
- Tests and the fake homeserver are in `plugins/agent-chat/skills/agent-chat/tests/` (test_agent_chat_codex.py,
  ac_fakes.py).
- The docs are `plugins/agent-chat/README.md` and `plugins/agent-chat/codex-skills/agent-chat/SKILL.md`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A test shows a batch whose full Codex note exceeds the limit but fits without earlier context yields one note with no earlier-context parts and with every root still shown
- [x] #2 A test with Cyrillic bodies shows a batch that does not fit even without earlier context yields several notes, each with the header and at most the limit in UTF-8 bytes, every message whole and in its original order
- [x] #3 A test shows a single message too big on its own is cut on a UTF-8 character boundary with every body line still quoted, followed by the unquoted cut line naming its event id without $ and the bytes left out, and the note is within the limit
- [x] #4 A watch-codex test shows each note is queued by its own codex queue call in order, and that 50 Cyrillic threads at full history produce parts of at most 100000 bytes each
- [x] #5 A watch-codex test shows a cached served room's mail is delivered in the same batch as an uncached room whose alias lookup fails with a network error, the failure is logged, the alias lookup's deadline is at most 10 s after the client's now, and a 401 from the alias lookup still raises
- [x] #6 A test shows a thread whose root was sent by the listening account is headed 'started by <me> (this account)' and carries no 'peer mail from another agent' label
- [x] #7 The Codex SKILL.md and the plugin README say a long batch can arrive as several notes and a cut message ends with the cut line, and the README Threads row says a 401 during a lookup loses that batch's mail
- [x] #8 agent-chat version is 0.4.2 in plugins/agent-chat/.claude-plugin/plugin.json, plugins/agent-chat/.codex-plugin/plugin.json and the version pin in test_agent_chat_codex.py
- [x] #9 The untracked review file design/agent-chat-threads-review-2026-11-04.md is committed unchanged
- [x] #10 uv run ruff check . is clean and uv run pytest plugins/agent-chat passes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: note.notes() renders whole, then without earlier context, then greedy consecutive runs, cutting a lone oversized body by binary search on UTF-8 bytes; watch._deliver queues each part; _batch_mail gives each alias lookup min(deadline, now+ALIAS_SECONDS) and _alias_of catches NetworkError; _thread labels an own root '(this account)'. Tests in test_agent_chat_addressing.py (note) and test_agent_chat_codex.py (watcher, with a new alias_fault in ac_fakes).

Commit: `959a229` - task-71: agent-chat splits Codex notes to fit codex queue, bounds alias lookups per room, labels an own thread root

Done. notes() in note.py (whole → no earlier context → consecutive runs → a lone oversized body cut on a UTF-8 boundary with the unquoted cut line); watch.QUEUE_BYTES=100_000, ALIAS_SECONDS=10.0; _deliver logs (part k of n) / (parts k-n of n); _alias_of catches NetworkError; own root '(this account)' (shared by the Claude note via _thread, so the Claude SKILL.md got the same sentence). ac_fakes gains alias_fault. Review: ralph:task-reviewer APPROVED (score 9); one minor finding left as is: the split re-renders each run (quadratic), bounded by the 50-event timeline limit per room per sync.
<!-- SECTION:NOTES:END -->
