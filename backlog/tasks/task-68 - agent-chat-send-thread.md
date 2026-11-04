---
id: TASK-68
title: agent-chat send --thread
status: Done
assignee: []
created_date: '2026-11-04T12:05:00Z'
updated_date: '2026-11-04T12:24:00Z'
labels:
  - feature:agent-chat-threads
dependencies: []
priority: medium
ordinal: 68000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
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
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The fake homeserver serves GET .../rooms/{room}/event/{id} and GET .../rooms/{room}/relations/{id}/m.thread[/{type}]
- [x] #2 send --thread with a top-level message id posts m.relates_to with rel_type m.thread, event_id = that message, is_falling_back true and m.in_reply_to = that message (tested)
- [x] #3 send --thread with a thread child's id posts into that child's root thread, with m.in_reply_to = the thread's latest m.room.message (tested)
- [x] #4 send --thread with a rich-reply id (only m.in_reply_to, no rel_type) uses it as the root (tested)
- [x] #5 send --thread refuses with a non-zero exit and posts nothing for each of: an edit; a reaction or other rel_type; a redacted or empty event; an unknown id; a child whose root is itself a thread child; a malformed id ($$x, a b, x:y) (each case tested)
- [x] #6 An id with and without one leading $ gives the same post, and every id in a URL path is percent-encoded (tested)
- [x] #7 The output line is "sent to <alias> as <account> in thread <root>: <event>" with --thread and "sent to <alias> as <account>: <event>" without it, ids without $ (tested)
- [x] #8 When codex is installed, codex execpolicy check --rules plugins/agent-chat/codex/rules/agent-chat.rules on "agent-chat send --as codex --message-file x.txt --thread abc_DEF-123 --to claude-b" returns allow, as a test
- [x] #9 The agent-chat version is 0.3.0 in both plugin.json files and in the version pin in test_agent_chat_codex.py
- [x] #10 uv run ruff check . is clean and uv run pytest plugins/agent-chat passes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: matrix.Client gains event() (None on 404) and thread_latest() on the v1 relations endpoint, every path segment quote(safe=''). cli send gains --thread: validate ^$?[A-Za-z0-9_-]+$ (exit 2), resolve the root inside the room loop (a 403 still re-resolves the room), refuse non-message/empty/redacted/other rel_type/nested roots with one line, build m.relates_to with is_falling_back + m.in_reply_to latest-or-root, print ids without $. Fake homeserver gets the event and relations routes and a generic event append. Tests in transport + codex (execpolicy case). Docs: plugin README, both SKILL.md, root README. Bump 0.2.3 -> 0.3.0.

Commit: `47695d8` - task-68: agent-chat send --thread posts into a Matrix thread, ids without $

Commit: `bf81c5b` - task-68: a missing relations endpoint fails the send without dropping the room cache

Implemented: matrix.Client.event() (None on 404) and thread_latest() (v1 relations, dir=b limit=1; a 404 there becomes a plain AgentChatError so send does not drop its room cache). cli send --thread: id regex $?[A-Za-z0-9_-]+ (exit 2 otherwise), root resolution inside the room loop (403 still re-resolves a stale room; 404 on the event = refusal), refusals for non-message, empty, redacted, any rel_type but none/rich reply/m.thread, and a root that is itself in a thread. Output prints ids without $. Fake homeserver gained the event and relations routes, add() for any event, and a no_relations toggle. Docs: plugin README Threads row + Codex rules note, both SKILL.md (Sending + refusal row), root README. Version 0.3.0. AC #8: the execpolicy case is in the parametrized test but codex is not installed in this container, so it skipped here; the live allow is unobserved. Final: ruff clean, pytest plugins/agent-chat 140 passed 5 skipped. Review: ralph:task-reviewer APPROVED (score 7, three minors), the minors were fixed in bf81c5b, and a re-review gave APPROVED (score 10). Still open: the post-merge live check in Element (send --thread on a top-level message, a rich reply and a thread child) needs the user and a host that can reach the homeserver.
<!-- SECTION:NOTES:END -->
