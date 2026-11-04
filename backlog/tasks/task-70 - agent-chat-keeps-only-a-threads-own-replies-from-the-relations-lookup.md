---
id: TASK-70
title: agent-chat keeps only a thread's own replies from the relations lookup
status: In Progress
assignee: []
created_date: '2026-11-04T13:37:00Z'
updated_date: '2026-11-04T13:43:00Z'
labels:
  - feature:agent-chat-threads
dependencies: []
priority: medium
ordinal: 70000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

The live check after TASK-68 and TASK-69 merged ran agent-chat 0.4.0 against continuwuity 26.9.1. The server's thread
relations lookup returns more than the thread asked for. A rich reply R carries `m.in_reply_to` to a message G and no
`rel_type`. When R has its own thread, the lookup of G's thread lists R's thread replies too. Observed, with G holding
thread replies C1 and C2 and R holding thread reply C3 (whose `m.relates_to.event_id` is R, not G):

```text
GET /_matrix/client/v1/rooms/{room}/relations/{G}/m.thread?dir=b&limit=3  -> [C2, C1, C3]
GET /_matrix/client/v1/rooms/{room}/relations/{G}/m.thread?dir=b&limit=1  -> [C2]
GET /_matrix/client/v1/rooms/{room}/relations/{R}/m.thread?dir=b          -> [C3]
```

The root's own replies came first and the nested thread's replies after them. agent-chat only reads with dir=b;
dir=f returned an empty chunk and stays unused.

This happens in agent-chat's documented flow. The user answers an agent with a plain Reply in Element, and the agent
replies with `send --thread <that reply>`, which opens a thread on the rich reply.

What goes wrong today:

- **Receiving.** `matrix.Client.thread()` returns the whole chunk and `threads.observe()` treats every event in it as
  G's thread. The sender of C3 then counts among G's agents, so the user's unaddressed message in G's thread wakes it.
  It also counts as having posted in G, so it gets no earlier context. And C3 can appear under "Earlier in this thread".
- **Sending.** `matrix.Client.thread_latest()` asks for one event and uses it for `m.in_reply_to`. It is right today
  only because the server happens to list the root's own replies first, and nothing promises that order.

## Locked decisions

- **Test.** One function in matrix.py decides whether an event belongs to a root's thread: its
  `content["m.relates_to"]` is a dict with `rel_type == "m.thread"` and `event_id` equal to the root. Both lookups use
  it.
- **Receiving.** `Client.thread()` returns only the events that belong, still newest first. It still asks the server
  for THREAD_WINDOW (50) events, so after filtering the window may hold fewer; that is accepted.
- **Sending.** `Client.thread_latest()` asks for THREAD_WINDOW events instead of 1, keeps the event-type suffix and
  dir=b, and returns the ID of the first event that belongs. It returns None when none belongs, and send then uses the
  root for `m.in_reply_to`, as it does today for an empty thread.
- **Nothing else changes.** The wake rule, the note format, the lookup budget, the refusals and the output lines stay
  as they are. No doc change: the docs already say "the thread's events", which is what this makes true.
- **Fake homeserver.** It gets a switch that mimics the server: `nested_relations`, default None. With "after", the
  relations route answers a root with the root's own thread events followed by the thread events of every rich reply
  to the root (an event whose `m.relates_to` has `m.in_reply_to.event_id == root` and no `rel_type`). With "first",
  the nested events come first, which proves send does not depend on the order. dir and limit apply to the combined
  list as they do now.
- **Version.** agent-chat 0.4.1 in both plugin.json files and in the version pin in test_agent_chat_codex.py.

## Housekeeping in the same task

- Append this record to TASK-68's implementation notes with `backlog task edit 68 --append-notes`:

```text
Live check after merge (agent-chat 0.4.0, continuwuity 26.9.1, one host, posts without mentions): send --thread on a top-level message opened a thread on it; send --thread on that thread's child, given with its $, posted into the same thread with m.in_reply_to on the latest reply; a rich reply (m.in_reply_to only) to the top-level message was accepted as a thread root by send --thread. The user confirmed all three in Element. Found: the relations lookup of the top-level message (dir=b) also listed the reply in the rich reply's thread, after the root's own replies; dir=f returned nothing. TASK-70 keeps only the events whose thread root is the one asked for.
```

- Commit the working-tree change to this feature's design file under the repo's design directory (`git status
  --short` lists it as modified; it updates one open question with the live-check answer) as it is. It is design
  history; do not edit it further.

## Scope cuts

- No workaround for dir=f.
- No recursion, and no reading past 50 events to make up for filtered ones.
- No change to `thread_root()`'s refusals.
- No zmx-peer-chat change.

## Paths

Scripts live in `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/` (matrix.py, threads.py, cli.py). Tests and
the fake homeserver (ac_fakes.py) live in `plugins/agent-chat/skills/agent-chat/tests/`, and the transport tests are in
test_agent_chat_transport.py.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 matrix.py has one function that tells whether an event belongs to a root's thread (m.relates_to is a dict with rel_type m.thread and event_id equal to the root), and Client.thread() and Client.thread_latest() both use it
- [x] #2 The fake homeserver has a nested_relations switch (None, after, first) that adds the thread events of rich replies to the root to the relations answer, after or before the root's own
- [x] #3 A test with nested_relations=after shows Client.thread() for the root returns only the root's own thread events, newest first
- [x] #4 A test with nested_relations=first shows send --thread <root> sets m.in_reply_to to the root's own latest reply, and a test where no event in the window belongs shows m.in_reply_to falls back to the root
- [x] #5 Client.thread_latest() asks the relations endpoint with limit 50 (THREAD_WINDOW), dir=b and the m.room.message suffix
- [x] #6 agent-chat version is 0.4.1 in plugins/agent-chat/.claude-plugin/plugin.json, plugins/agent-chat/.codex-plugin/plugin.json and the version pin in test_agent_chat_codex.py
- [x] #7 TASK-68's implementation notes end with the live-check record given in the description
- [x] #8 uv run ruff check . is clean and uv run pytest plugins/agent-chat passes
- [x] #9 A test with nested_relations=after shows the user's unaddressed message in the root's thread does not wake an agent that posted only in the rich reply's thread while the root thread's own agent wakes, and an agent the root mentions that has not posted gets earlier context with no nested reply in it
- [ ] #10 The design file's working-tree change is committed as it is (git status --short shows nothing modified under the design directory)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: add matrix.in_thread(event, root); Client.thread() filters the chunk with it; thread_latest() asks THREAD_WINDOW with dir=b and returns the first event that belongs. Fake homeserver gains nested_relations (after/first). Tests in test_agent_chat_transport.py. Version 0.4.1. TASK-68 note; commit the design file as is.

Commit: `d6fc255` - task-70: record the live-check answer in the agent-chat threads design

Commit: `5da3e82` - task-70: agent-chat keeps only a thread's own replies from the relations lookup
<!-- SECTION:NOTES:END -->
