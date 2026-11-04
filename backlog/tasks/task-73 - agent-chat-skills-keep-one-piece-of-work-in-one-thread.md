---
id: TASK-73
title: agent-chat skills keep one piece of work in one thread
status: Done
assignee: []
created_date: '2026-11-04T17:48:00Z'
updated_date: '2026-11-04T17:56:00Z'
labels:
  - feature:agent-chat-threads
dependencies: []
priority: medium
ordinal: 73000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

The user wants each backlog task's room announcements grouped in one Matrix thread. In a project's shared-backlog
protocol the holder announces claimed, blocked, released and done to the room without `--to`, and today each
announcement is top-level. agent-chat already has `send --thread <id>`, and `send` prints the id of every post. The
holder usually posts from the session that already has the first post's id. So a convention in both agent-chat
skills is enough, with no new flag or code. A `--topic` design that scanned room history was considered and dropped as
too much machinery for the rare lost-id case. Codex reviewed and tightened the convention.

**Direction:** convention only. Both agent-chat skills tell agents to keep the updates about one piece of work in one
thread, using `--thread` with the id `send` printed for the first update, recorded where the work is tracked. agent-chat
gets no new flag, no history scan and no code change.

**Locked decisions (with rationale):**

- **No `--topic` flag, no history scan, no hidden key, no code change.** *Rationale:* only a task's holder posts its
  updates, usually from the session that already holds the root id, and a lost id costs one stray top-level post.
- **The convention lives in both agent-chat skills, not in project CLAUDE.md files.** *Rationale:* every project with a
  room gets it without a per-project rule, and the project's protocol keeps deciding what to announce.
- **"First update" means first in the room for that work, and a recorded id is reused across claimed, blocked,
  released, reclaimed and done.** *Rationale:* a new holder or a new session must not start a second thread for the
  same work.
- **Recording the id is an ordinary tracker edit under the project's ownership and commit/push rules, and grants no
  extra right.** *Rationale:* the skill must not hand out write or push authority. In a shared backlog only the holder
  edits a claimed task.
- **The top-level fallback is decided before sending; a failed or refused send follows the error table and is never
  retried top-level.** *Rationale:* a blind top-level retry could duplicate an unconfirmed send and bypass the refusal
  rules.
- **The room alias is not recorded with the id.** *Rationale:* one project has one room, so a task in that project's
  backlog already implies it.
- **The Codex flow and its prefix rule are unchanged.** *Rationale:* `codex execpolicy check` on `agent-chat send --as
  codex --message-file NAME --thread abc_DEF-123` without `--to` already answers allow.
- **Version 0.4.3 → 0.4.4.** *Rationale:* a skill-text change is a patch under this repo's SemVer rule.

**Scope cuts:**

- No `--topic` flag, no history scan, no hidden content key, no `--thread` key inheritance and no topic in the note.
- No change to agent-chat code, the CLI, the note, the wake rule or the Codex rules file.
- No edit to any other project's CLAUDE.md or protocol scripts.
- No live check: nothing that runs changes.

**Acceptance criteria (sketch):**

- Both SKILL.md files carry the paragraph below, right after the paragraph that starts "`--thread <id>` posts the
  message as a reply in a Matrix thread".
- Both SKILL.md files have the two relaxed sentences below in place of the old ones.
- The Claude SKILL.md has the heredoc example without `--to`; the Codex SKILL.md has the `--message-file` example
  without `--to`.
- The plugin README's Threads row mentions the convention.
- Version 0.4.4 in both plugin.json files and in the pin in test_agent_chat_codex.py.
- `uv run ruff check .` is clean and `uv run pytest plugins/agent-chat` passes.

The paragraph, the same text in both skills:

```markdown
Keep updates about the same piece of work in one thread: a task's claimed, blocked, released and done messages, for
example. First check where the work is tracked for a recorded room thread id. If none is recorded or known, post the
first update at top level and keep the id the successful send printed; post every later update with `--thread <id>`.
Before a long run or a handover, record that id (`room thread: <id>`) where you may edit the work's tracking, following
the project's ownership and commit/push rules; this gives no extra right to edit or push. If no id can be recovered,
post a new top-level update that names the work (`TASK-108: done, pushed abc123`) and use its id from then on. This
fallback is a choice made before sending: a send that fails or is refused follows the table below, never a top-level
retry.
```

In each SKILL.md, in place of "Post at top level, without `--thread`, only to start a new topic." (Receiving):

```markdown
Post at top level, without `--thread`, only to start a new topic or the first update about a piece of work (see Sending).
```

In each SKILL.md, in the `--thread <id>` paragraph (Sending), in place of "and post at top level only for a new topic":

```markdown
and post at top level only for a new topic or the first update about a piece of work
```

The Claude example goes after the new paragraph:

````markdown
```bash
agent-chat send --thread AbC_123-x <<'EOF'
done TASK-108, pushed abc123
EOF
```
````

The Codex example goes after the new paragraph. The file is reserved with `prepare-message` and filled with
`apply_patch` as the skill already says:

````markdown
```bash
agent-chat send --as codex --message-file ac-codex-9b2e.txt --thread AbC_123-x
```
````

**Implementation checklist:**

- `plugins/agent-chat/skills/agent-chat/SKILL.md`: the paragraph, the two relaxed sentences and the heredoc example.
- `plugins/agent-chat/codex-skills/agent-chat/SKILL.md`: the paragraph, the two relaxed sentences and the
  `--message-file` example. Keep "after the paragraph" wording consistent with Codex's file flow.
- `plugins/agent-chat/README.md`: one clause in the Threads row, for example "the skills ask agents to keep updates
  about one piece of work in one thread, recording its root id where the work is tracked".
- Bump 0.4.3 → 0.4.4 in both plugin.json files and in the pin in
  `plugins/agent-chat/skills/agent-chat/tests/test_agent_chat_codex.py`.
- Run `uv run ruff check .` and `uv run pytest plugins/agent-chat`; pytest needs a local port.

## Housekeeping

Commit the working-tree change to this feature's design file under the repo's design directory as it is. `git status
--short` lists it as modified; it appends the dated addendum this task comes from. Do not edit it further.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Both SKILL.md files carry the given one-thread paragraph verbatim, right after the paragraph that starts '`--thread <id>` posts the message as a reply in a Matrix thread'
- [x] #2 In both SKILL.md files the Receiving sentence reads 'Post at top level, without `--thread`, only to start a new topic or the first update about a piece of work (see Sending).' and the Sending sentence reads '... and post at top level only for a new topic or the first update about a piece of work'; grep finds no remaining 'only for a new topic.' or 'only to start a new topic.'
- [x] #3 The Claude SKILL.md has the heredoc example 'agent-chat send --thread AbC_123-x' with 'done TASK-108, pushed abc123' and no --to; the Codex SKILL.md has 'agent-chat send --as codex --message-file ac-codex-9b2e.txt --thread AbC_123-x' with no --to
- [x] #4 The plugin README's Threads row mentions that the skills keep updates about one piece of work in one thread, recording its root id where the work is tracked
- [x] #5 agent-chat version is 0.4.4 in plugins/agent-chat/.claude-plugin/plugin.json, plugins/agent-chat/.codex-plugin/plugin.json and the version pin in test_agent_chat_codex.py
- [x] #6 No file under plugins/agent-chat/skills/agent-chat/scripts/ or plugins/agent-chat/codex/ changes (git diff --stat master..HEAD lists none)
- [x] #7 The design file's working-tree change is committed as it is (git status --short shows nothing modified under the design directory)
- [x] #8 uv run ruff check . is clean and uv run pytest plugins/agent-chat passes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: commit design addendum as-is; add one-thread paragraph + example to both SKILL.md after the --thread paragraph, relax two sentences, README Threads row clause, bump 0.4.3->0.4.4 in both plugin.json and the test pin; run ruff + pytest plugins/agent-chat.

Commit: `a6cfec5` - task-73: agent-chat threads design records the one-thread-per-work convention

Commit: `90ac5c0` - task-73: agent-chat skills keep updates about one piece of work in one thread

Done: one-thread paragraph + examples added to both agent-chat skills (paragraph as one unwrapped line, matching the files' style), two sentences relaxed, README Threads clause, 0.4.4 in both manifests and the test pin. ruff clean; pytest plugins/agent-chat 198 passed, 5 skipped. task-reviewer: APPROVED (score 10).
<!-- SECTION:NOTES:END -->
