# Feature Review: agent-chat-hub

**Verdict: Aligned**

The code delivers every locked decision in the addendum's "Distilled for ralph-task" block. No scope cut is broken and
no scope creep was found. There are three small gaps: Codex `status`, a missing step in the rollout docs, and one
design caveat left out of the README. None of them blocks the rollout, and each has an easy fix.

No `.claude/ralph-review-rules.md` exists, so only the standard rubric was applied.

**Passes run:** 3 (brainstorm scope cuts) and 5 (out-of-scope creep).
**Passes skipped:** 1, 2 and 4, because there is no `design/agent-chat-hub-prd.md` (no PRD user stories or FRs, no
Non-Goals section, no Success Metrics section).

The intent-to-implementation matrix below uses Pass 1's Delivered / Partial / Missing labels, but it is checked against
the brainstorm addendum's locked decisions (LD) and acceptance sketch, not a PRD. The verdict comes from Passes 3 and 5,
and the matrix agrees with it.

Review range: `e1dd7e8..185681f` (TASK-74 to TASK-77). Tests were not re-run by the reviewer; the host result was 281
passed, ruff clean.

## Intent → Implementation Matrix

Paths: code is under `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/`, tests under
`plugins/agent-chat/skills/agent-chat/tests/`.

| ID | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| LD-1 | Optional `hub`. Without it the behaviour is 0.4.4. A non-string value, or one without the prefix, is a config error. `send` and the wait refuse the hub's own project. | Delivered | `config.py:114` checks the type, the prefix, and that the rest is a token (one check more than the design asks). Hub-directory refusals: `cli.py:259` (send), `:397` (hook-wait), `:330` (watch-codex `--thread`); all-rooms skip at `watch.py:466`. Existing tests unchanged apart from the version pin; `ac_fakes.write_config` only gained an optional argument. |
| LD-2 | Group messages; answers stay in one hub thread | Delivered | Several `--project` targets in one field (`cli.hub_content`). Replies use `--hub --thread <root>`. |
| LD-3 | Address = comma-separated tokens followed by `:`; exact and case-sensitive; no alias lookups on the wake path | Delivered | `addressing.py:19` `_ADDRESS`, `:158` `project_address`. `beta @claude-b: x`, `Summary: x`, `@claude-b: x` and `beta x` wake nobody (`test_what_is_not_an_address_wakes_nobody`). `hub_wakes` makes no network calls. |
| LD-4 | Accounts come only from `m.mentions` and the `@`-run right after the colon | Delivered | `project_address` (mentions plus the leading run of the text after the colon); `test_an_element_pill_narrows_the_address_wherever_it_sits`. |
| LD-5 | Field `agent_chat.hub {v:1, from, to}` and prefix `<from> → <to>: ` / `<from>: `. An invalid field wakes nobody and makes no participant. The field never sets authority. | Delivered | `hub_field` (`addressing.py:136`) requires an int `v == 1` and token strings. `participants()` (`threads.py:72`) uses only valid fields. `authority()` is untouched. Send content is pinned in `test_a_hub_send_carries_the_prefix_the_field_and_the_mentions`. |
| LD-6 | A session is the pair (account, project) everywhere | Delivered (Partial for Codex status, see notes) | Own-pair check in `hub_wakes:206`; `Thread.pairs` / `hub_selects` (`threads.py:58`); note `_own` / `_took_part` (`note.py:145,157`); Codex routing per project (`watch.py:401`); `<slug>.hub` per project room. |
| LD-7 | One wake predicate, rules 1–4, shared by `listen.py` and `watch.py` | Delivered | Rules 1–3 are in `hub_wakes`. Rule 4 is `Wake.THREAD` plus `Thread.hub_selects`, with narrowing via `addressees`. The loop is `SyncLoop.hub_routes` (`listen.py:238`), used by `Listener.hub_mail` and `CodexWatcher._hub_routes`, so there is exactly one copy. |
| LD-8 | Every agent hub send is explicit; `--hub --thread` alone posts for the user with an empty `to`; no address taken from the thread | Delivered | `cmd_send` / `_check_hub_flags` (`cli.py:299`). `to = []` when there is no `--project`. Nothing reads the thread to build an address. |
| LD-9 | Targets checked with `resolve_alias`, never joined; refusals with one line, non-zero exit, nothing posted | Delivered | `check_hub_send` (`cli.py:208`); `test_targets_are_resolved_but_never_joined` and the refusal tests. |
| LD-10 | Note: `Hub: from <project> (<authority>) to …`, reply hints, Codex form | Delivered | `hub_header` (`note.py:122`) also shows the account. `CODEX_SEND` puts `--as codex --message-file <fresh-name>` first. |
| LD-11 | Locks and cursors stay per (account, project room); the hub timeline comes from the same `/sync` | Delivered | The filter has no room restriction, so the hub timeline arrives in the same sync. Cursor names are unchanged (`test_two_waits_of_one_account_each_get_their_projects_mail_once` asserts the cursor file names). |
| LD-12 | Hub isolation: resolve and join bounded at wait start, failure logged once, retried at the next wait, project mail never blocked | Delivered | `Listener._hub` (`listen.py:387`) is bounded by `HUB_SECONDS` = 10; project-room mail is computed before hub mail; leaving mid-wait drops the hub; `test_a_broken_hub_never_blocks_project_mail_and_is_logged_once`. The watcher retries at each sweep and logs once per reason (`watch.py:418,427`), which fits a long-running process. |
| LD-13 | Fail closed only for inherited routing; explicit addresses are delivered from an unreadable thread | Delivered | `hub_routes` logs through `_unread` and wakes nobody. Explicit mail keeps an unread `Thread` (`test_an_unreadable_thread_wakes_only_explicitly_addressed_mail`). |
| LD-14 | Best-effort delivery is documented | Delivered | README "Delivery is best-effort"; both SKILL.md files. |
| LD-15 | Rollout with restarts; hub-only switch deferred | Delivered (Partial, see notes) | README "Rollout order" adds a correct second restart after the key is set, because config is read at process start. A test pins the absence of "only through the hub". The step "`status` confirms coverage" is not in the rollout text. |
| T1 | `send --hub`, Codex form, execpolicy for both forms, 0.5.0 | Delivered | `test_agent_chat_hub.py`. Execpolicy cases added and the rules file is unchanged. Codex was not installed in the container, so that skip is recorded in the notes. |
| T2-a | `beta, gamma: x`, the pill form, agent own pair, invalid or `v` ≠ 1 field | Delivered | `test_agent_chat_hub_wait.py:119–190` |
| T2-b | Thread case: empty `to` wakes nobody; the user's reply wakes root addressees and posters, and no other alpha account | Delivered | `test_a_thread_reply_wakes_the_roots_addressees_and_its_posters` |
| T2-c | Two waits of one account; broken hub; note labels; status covered / unavailable / unknown with `.owner` unchanged | Delivered | `:277`, `:345`, `:494`, `:390–435` (the `.owner` file is asserted as `"<pid>\n"`). |
| T3 | watch-codex: queued once per project, `not queued`, single-thread mode with no zmx lookup, own pair | Delivered | `test_agent_chat_codex.py` hub section (asserts `zmx.log` is absent in single-thread mode). |
| T4 | README and both skills: grammar with pill example, reply commands, best-effort, provisioning, rollout, no approval, one thread per topic, hub optional | Delivered | Pinned by `test_the_docs_document_the_optional_hub` and `test_the_skills_deny_hub_approval_and_keep_one_thread_per_topic`. |
| Post | Live two-host round trip (6 steps); the later hub-only task | Not done here (outside the repo by design) | No follow-up task exists yet, which is correct: the design says it is created only after the round trip passes. |

## Non-Goal Violations

Pass 2 was skipped because there is no PRD.

## Scope Cut Violations

None detected.

- **No per-project accounts and no fan-out:** `send` posts to exactly one room.
- **No hub-wide broadcast:** an unaddressed top-level message from the user gets `Wake.NO`.
- **No feedback on a mistyped project:** nothing replies, and `status` does not list projects.
- **No replay and no bigger limit:** `TIMELINE_LIMIT` is still 50.
- **No copy of hub threads into project rooms, and no SendMessage bridge.**
- **Unchanged internals:** `authority()`, `BUDGET_SECONDS`, the project-room `wakes()` and the cursor semantics are
  untouched. Moving `_left` into `SyncLoop` is a refactor that does not change behaviour.
- **No hub-only skill switch:** a test asserts the phrase is absent.

## Success Metric Assessment

Pass 4 was skipped because there is no PRD.

## Drift List

No drift detected. A few small additions go beyond the design's words, but each traces to a locked decision:

- `cli.py:299` refuses `--project` without `--hub`, and a bare `--hub` with neither `--project` nor `--thread`. This
  follows LD-8 ("every agent send is explicit"). The bare-`--hub` refusal is recorded in the TASK-74 notes but missing
  from the README's refusal list.
- `config.py:114` also requires the part after the prefix to be a token, so `hub_project` is always addressable. This
  supports D.
- `cli.py:259` refuses a plain, non-hub `send` from the hub's own directory, and `cli.py:330` does the same for
  `watch-codex --thread`. Both extend D, and the README documents them.
- `watch.py:427` logs "serving the hub <alias>". This is minor operational logging.

## Reviewer Notes

1. **`status --as codex` cannot show Codex hub coverage (minor; the one Partial for LD-6 and LD-15).** `cmd_status`
   (`cli.py:446`) reads `<slug>.hub` under the account's hook-wait lock. The Codex account never runs hook-wait, and
   `CodexWatcher` writes no coverage file. So on a Codex host the line always reads
   `hub: #agents-hub:…: not covered (no wait listens)`, even while watch-codex serves the hub.
   - The README's Checks line says `status --as codex` shows "the same for the Codex account", which suggests
     otherwise.
   - The design's rule that "`status` confirms coverage before the `hub` key is relied on" can't be met for watchers.
   - The README rollout paragraph also never tells the operator to run `status` to confirm coverage.
   - The Codex SKILL avoids the problem by saying "hub mail arriving here is the sign".
   - Possible fixes: have the watcher write and remove a `watch-codex[-<slug>].hub` file and have
     `status --as codex` read it, or label the line for Codex as "see the watch-codex log". Then add "confirm with
     `status`" to the rollout steps.
2. **One design caveat is not documented.** The addendum says a single-thread watcher next to an all-rooms watcher of
   the same account is unsupported (different locks, so both may deliver hub mail). No task AC asked for it, and it
   appears in neither the README nor the skills. One sentence in the README's watcher section would cover it.
3. **Expected log noise.** In all-rooms mode, every unnarrowed hub message to a project with no local Codex session logs
   `not queued: …` on every host's watcher. That includes Claude-only projects. This matches the design ("logs
   `not queued`") but will be noisy once several projects use the hub. Worth watching after the round trip.
4. **The plain-text grammar is ambiguous in Element.** This comes from the design, not the code. An agent's reply to the
   user is shown as `beta: …`, meaning "from beta", while the user typing `beta: …` means "to beta". If the owner finds
   this confusing in Element, revisit it later, for example with a different separator for posts meant for the user.
5. **Things checked and found correct:**
   - The wait joins the hub before the first-run cursor is taken, and `since_join` drops pre-join history per room.
   - Hub thread lookups share the batch budget but run after project-room lookups, so they cannot starve project mail.
   - `AuthError` from the hub is re-raised, so 401 handling is unchanged.
   - In single-thread mode, hub mail is grouped under `room_alias(cfg, project)`, which equals the watched alias, so it
     goes to `--thread` with no zmx call.
   - The rules file `codex/rules/agent-chat.rules` is unchanged, and the README's statement that flags after the file
     name are covered by the existing rule is consistent with it.
6. **Private information: none found.** Added lines use only placeholders: `example.test`, `@claude-a/b`,
   `@codex-a/b`, `@human`, `@stranger`, projects alpha/beta/gamma/delta, `#agents-hub`, loopback
   `http://127.0.0.1:<port>`, and generic `/tmp/agent-chat-<uid>`. There are no IPs, host names, user names, home
   paths, tokens or conversation text. The design doc at the base commit also uses placeholders. The author name and
   email in `plugin.json` were already there and are not part of this diff.
7. **Versions:** 0.5.0, 0.5.1, 0.5.2, then 0.5.3 across the four tasks, consistent in both plugin manifests and the test
   pin. The marketplace description doesn't mention the hub; that's fine while the hub is optional.
