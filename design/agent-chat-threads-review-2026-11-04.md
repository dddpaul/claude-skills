# agent-chat-threads review, 2026-11-04

This review covers TASK-68 (`send --thread`), TASK-69 (thread-aware receiving) and TASK-70 (the filter that keeps only
a thread's own replies). The diff is a29053e..1662704 and agent-chat is at 0.4.1. Two reviews ran:

- **Design alignment:** the `ralph-reviewer` agent compared the code with the design's intent. Its verdict is
  **Aligned**.
- **Correctness:** Claude and Codex reviewed the code independently, then discussed the findings. They found four
  defects and agree on all of them.

## Design alignment (ralph-reviewer)

**Verdict: Aligned**

**Passes run:** 3 and 5. **Passes skipped:** 1, 2 and 4, because the feature has no PRD; the design exists only as a
brainstorm, so the PRD coverage, non-goal and success-metric passes have no input. There is no project rules file for
this review, so only the standard rubric applies.

**Checked independently:**

- `uv run ruff check .` is clean.
- `uv run pytest plugins/agent-chat` passes: 179 tests, none skipped. It has to run outside the sandbox, because the
  fake homeserver binds a local port.
- `codex` is installed on the host, so the execpolicy case for `--thread abc_DEF-123` really ran, and it returned
  allow.

### Intent → implementation matrix

The matrix is built from the brainstorm's locked decisions. In the IDs, T1 is the brainstorm's Task 1 (TASK-68), T2 is
its Task 2 (TASK-69), and FU is the follow-up TASK-70.

| ID | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| T1-1 | `--thread` posts `rel_type: m.thread`, the root's `event_id`, `is_falling_back: true` and `m.in_reply_to` set to the latest message (or the root); the mention prefix and `m.mentions` are kept | Delivered | `cli.py` `thread_relation`; a test asserts the whole content dict |
| T1-2 | Root resolution: a child leads to its root, a nested root is refused, a message or rich reply without a `rel_type` is the root, and any other relation, a redacted or empty event, a non-message and an unknown id are refused | Delivered | `cli.py` `_relation` and `thread_root`; an 8-case refusal test; child-to-root and rich-reply-root tests |
| T1-3 | Failures are loud and stay within send's deadline: one stderr line, a non-zero exit, nothing posted, and the message file kept | Delivered | Lookups run in `cmd_send`'s room loop under `SEND_SECONDS`; tests check one stderr line and no PUT; a missing relations endpoint exits 1 and keeps the room cache |
| T1-4 | Ids without `$`: an optional `$`, then `[A-Za-z0-9_-]+`, and anything else exits 2; path segments are percent-encoded; both output lines print ids without `$` | Delivered | `cli.py` `EVENT_ID`; `quote(safe='')` in matrix.py; malformed-id tests make no request |
| T1-5 | The Codex prefix rule is unchanged, with an execpolicy regression case | Delivered | The rules file is untouched; the `--thread` case passes |
| T1-6 | Version 0.3.0, and the docs ship with the task | Delivered | Both manifests at merge 99118a3; plugin README, both SKILL.md files, root README |
| T1-7 | The post-merge live check (top-level message, thread child, rich reply) is recorded in the task notes | Delivered | TASK-68 notes |
| T2-1 | Wake rule: the user's unaddressed message in a thread wakes the thread's agents, or everyone when none is seen; every other case is unchanged | Delivered | `addressing.py` `Wake` and `wakes`; `threads.py` `Thread.wakes`; addressing, hook and codex tests |
| T2-2 | Participation is what the lookup observes: the root's sender, the agents the root mentions, and the senders of the newest 50 thread events; an agent mentioned only in a later reply does not count; `current_user_participated` is not used | Delivered | `threads.py` `observe`; window and mention tests |
| T2-3 | One lookup per (room, root) per batch: GET v3 event plus GET v1 relations with `dir=b&limit=50`; `SyncLoop.mail(room, events, budget)` | Delivered | `matrix.py` `Client.thread`; `threads.py` `Budget`; `listen.py` |
| T2-4 | Budget: 10 s shared by every lookup of a batch, at most 2 tries, the socket timeout capped by what is left, failures cached, a 401 fatal, mail delivered without enrichment when a lookup fails | Delivered | The bounded mode of `request(tries=)`; outage, try-count, 401 and fallback tests |
| T2-5 | `watch-codex` checks `_served` before any lookup | Delivered | `watch.py` `_batch_mail`, which also makes every lookup before the first delivery |
| T2-6 | The note groups mail by thread in first-mail order and never reorders mail within a thread | Delivered | `note.py` `render`; grouping test |
| T2-7 | The root is always shown, cut to 300 characters with `…`, under its sender's authority label, as history | Delivered | `note.py` `_thread`; truncation test |
| T2-8 | Earlier context: the last 3 replies before the first mail, in the server's order, excluding the batch's mail, 300 characters each, a left-out line when the first mail is outside the window, and only for an account not seen in the thread | Delivered | `note.py` `_earlier`. "Seen" is read as "posted" (root sender plus window senders), so an agent the root only mentions still gets context; TASK-69 documents this reading |
| T2-9 | Every body line is quoted with `> `, after truncation | Delivered | `quote(cut(...))` |
| T2-10 | Full ids without `$`; the top-level hint; the failed-lookup heading | Delivered | id and heading tests |
| T2-11 | A Codex reply line with `--thread` | Delivered | `note.py` `CODEX_REPLY` |
| T2-12 | Both skills' rule: reply in the thread the note names, post at top level only for a new topic, and treat the root and context as history, not instructions | Delivered | Both SKILL.md files |
| T2-13 | Docs: README "How it works" (the Addressing row and a new Threads row), the Codex watcher text, the root README, and marketplace.json if affected | Delivered | All present; marketplace.json rightly unchanged, since it does not state the wake rule |
| T2-14 | Version 0.4.0 | Delivered | Both manifests at merge 1a4e988 |
| FU-1 | One `in_thread(event, root)` check, used by both `thread()` and `thread_latest()` | Delivered | matrix.py |
| FU-2 | `thread_latest` asks for 50 events with `dir=b` and the `m.room.message` suffix, and returns the first that belongs, else the root | Delivered | Tests for the nested-replies-first order and for a window with nothing that belongs |
| FU-3 | The fake homeserver's `nested_relations` switch: None, after, first | Delivered | `ac_fakes.py`; the after mode reproduces the observed `[C2, C1, C3]` |
| FU-4 | A rich reply's thread neither adds agents to the root's thread nor feeds its context | Delivered | A dedicated test |
| FU-5 | Version 0.4.1, the TASK-68 note appended, the design file committed as it was | Delivered | Both manifests and the version pin; d6fc255 |

### Scope cuts

The reviewer found no scope cut violated in intent:

- one Codex thread per Matrix thread, a local thread index, `current_user_participated`, `--reply-to`, reading past
  50 events and thread-aware sync filters are all absent;
- the skills don't tell agents to start per-task threads;
- TASK-70 stayed within its cuts.

`plugins/zmx-peer-chat/README.md` changed one cell: the agent-chat cell of the comparison table that both READMEs
mirror. This is doc parity, not a zmx-peer-chat change.

### Drift list

No drift detected. Four items sit outside the checklists but support in-scope work:

- the mirrored comparison cell;
- `Client.now()` and the "every lookup before any delivery" ordering, both from TASK-69's review fix;
- test-only helpers in the fake homeserver: `no_relations`, `lookup_fault`, `lookups()`;
- process only: commit 5cbf626 added the design file on master, outside a task branch.

### Reviewer notes

1. **A 401 during a lookup drops the batch.** Claude's wait loses that batch's mail, and `watch-codex` loses it for
   every room in the batch, because the cursor was already saved. TASK-69 accepted this. The README doesn't say so.
2. **The design gives a stale value.** It still says `limit=1` for the latest-message lookup; the code reads 50 and
   filters. The design is kept as history.
3. **The filtered window can shrink.** Replies in a rich reply's thread still count against the server's 50 events.
   TASK-70 accepted this.
4. **Two functions share a name.** `cli.thread_root` asks the server and can refuse an id, while
   `addressing.thread_root` only reads the content. They do different jobs under one name.
5. **The receiving side has had no live check.** Nobody had yet sent an unaddressed in-thread message from Element and
   watched it wake only the thread's agent. The live check below, run the same day, settles this.

## Live check of the receiving side

The check ran on 2026-11-04 with agent-chat 0.4.1 against continuwuity 26.9.1, in one project room. Four listeners were
up:

- Claude A, on host 1, through the Claude wait;
- Claude B, on host 2, through the Claude wait;
- host 2's Codex watcher;
- the other configured agent accounts.

Claude A's account posted a top-level root with no mention, which woke nobody. The user then posted three messages
inside that thread from Element.

| Step | The user's message in the thread | Expected | Observed |
|---|---|---|---|
| A | No mention | only Claude A, the thread's one agent | Claude A got the note and answered in the thread; Claude B got no note; the Codex watcher logged nothing |
| B | Mentions Claude B (Element's pill) | only Claude B | Claude B got the note, with the two earlier replies as history because it had not posted yet, and answered in the thread; Claude A got no note |
| C | No mention | Claude A and Claude B, who have both posted now | both got the note with no earlier context, and both answered in the thread; the Codex watcher logged nothing |

Every agent reply carried `rel_type: m.thread` with the right root, and each note's reply hint named the full root id
without `$`.

Two observations:

- Claude A's own note headed the thread "started by <Claude A>, peer mail from another agent", which is correctness
  finding 4 below.
- Participation is judged when the lookup runs. A read-only replay of the thread after the check therefore counts
  Claude B as one of the thread's agents for step A as well, because Claude B posted later. The live listeners looked
  up at the time of each step, so they woke correctly. This is the design's lookup-time rule, not a defect.

## Correctness (Claude and Codex)

Claude and Codex each reviewed independently first, then compared findings and argued severity. Codex's reproduction
tests confirmed all four defects below: a real local HTTP server that drips its response, a rendered 288,653-byte
note, and an in-process watcher whose alias lookup fails.

| Rank | Severity | Finding | Where | Failure scenario |
|---|---|---|---|---|
| 1 | P2 | The Codex note has no byte limit, though `codex queue` takes it as a single argument | `note.py` `render`, `watch.py` `_deliver` | Linux caps one argument at 131,072 bytes. The watcher catches up on 30 or more threads of Cyrillic mail with full history, `codex queue` fails with E2BIG, and the mail is lost because the cursor has already moved; the watcher only logs it. With ASCII text, 50 threads at full history come to 108,300 bytes. `codex queue` (0.166) has no stdin or file input. |
| 2 | P3 | The bounded lookup caps each socket wait, not the total elapsed time | `matrix.py` `request` / `_once` | A response that drips bytes faster than the socket timeout outlasts the 10 s budget. In the reproduction, a request with a 0.15 s budget succeeded after 0.95 s. Slow connect, TLS, header and body phases add up the same way, and the hostname lookup (DNS) is not bounded at all. The deployed server and proxy stall or close instead, which the stall test covers. |
| 3 | P3 | The all-rooms prepass holds back mail for rooms the watcher already serves | `watch.py` `_batch_mail` → `_alias_of` | The watcher runs with an infinite deadline, so the alias lookup for a room it hasn't seen before retries for as long as that room's lookup fails. Before TASK-69, rooms earlier in the batch were delivered first. Now nothing is delivered. The unbounded retry itself predates the feature. |
| 4 | P3 | A thread the agent started itself gets the label for another agent's mail | `note.py` `_thread`, `authority()` | This host's own accounts are in `cfg.agents`, so the root is labelled "started by <me>, peer mail from another agent". A fix must keep the meaning that history is neither an instruction nor an approval. |

Not a defect: when a top-level mail and a reply in its thread arrive in the same batch, the same text shows twice,
once as mail and once as the thread's root. The design chose to always show the root, marked as history.

Fix directions both agree on:

1. **Note size:** drop the optional history by an encoded byte budget, then split the remaining mail into several
   `codex queue` calls, keeping its order and never cutting a message. Decide what happens to one message that cannot
   fit on its own; that case predates this feature.
2. **Total deadline:** a watchdog that shuts the socket down at the deadline needs:
   - explicit ownership of the socket;
   - handling before and after the connection is set up, including through a CONNECT proxy and TLS;
   - cleanup in a `finally` block;
   - a check that a late success counts as a failure.

   Test it with slow headers, a slow body and a slow connect. Don't claim DNS is bounded unless it is.
3. **Alias prepass:** give the alias lookup a finite deadline and skip a room that fails for this batch, logging a
   line; keep a 401 fatal.
4. **Self label:** add a label for the agent's own message that still marks it as history.
