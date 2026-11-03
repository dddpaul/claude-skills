---
id: TASK-58
title: Start agent-chat mentions with the short account name
status: To Do
assignee: []
created_date: '2026-11-02T18:58:00Z'
labels:
  - agent-chat
dependencies: []
priority: medium
ordinal: 58000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

`agent-chat send --to <account>` starts the message body with the addressee's full Matrix ID, for example `@codex-a:example.test: G received`. The human reads the project room in Element, which shows a message's body as sent, so every addressed message opens with a long ID instead of the account's short name. In a live deployment this is the first thing the user asked to change. The full ID in the body is not needed for addressing: `addressing.leading_mentions` already resolves a bare `@localpart` against `server_name`, and `m.mentions` carries the full IDs anyway.

## Scope

In scope:
- `message_content()` in `cli.py` writes each addressee in the body prefix as `@<localpart>` when its server is the configured `server_name`, and as the full ID otherwise. `m.mentions` keeps the full IDs unchanged.
- The same prefix for both send paths: Claude's stdin send and Codex's `send --as codex --message-file`.
- Tests updated and added; README and both SKILL.md files describe the short prefix; patch version bump in both plugin manifests.

Out of scope:
- An HTML `formatted_body` with mention pills. Possible later, as its own task.
- Any change to the addressing rules, `wakes()`, the note format or the listener.
- Editing messages already in rooms.
- Display names. They are set on the server, not by this plugin.

## Files

- `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/cli.py` (exists): `message_content()` builds the prefix from `to`, which holds full IDs from `Config.user_id`.
- `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/config.py` (exists): `server_name` and `user_id()`, read only.
- `plugins/agent-chat/skills/agent-chat/scripts/agent_chat/addressing.py` (exists): `leading_mentions()`. Read it to confirm the short form parses; no change expected.
- `plugins/agent-chat/skills/agent-chat/tests/test_agent_chat_transport.py` (exists): `test_send_reads_its_body_from_stdin_intact` asserts the full-ID prefix today.
- `plugins/agent-chat/skills/agent-chat/tests/test_agent_chat_codex.py` (exists): the message-file send test asserts the full-ID prefix today.
- `plugins/agent-chat/README.md` (exists): the Addressing row of the How it works table.
- `plugins/agent-chat/skills/agent-chat/SKILL.md` and `plugins/agent-chat/codex-skills/agent-chat/SKILL.md` (exist): the `--to` paragraph.
- `plugins/agent-chat/.claude-plugin/plugin.json` and `plugins/agent-chat/.codex-plugin/plugin.json` (exist): both at 0.2.0.

Today's code, for reference:

```python
def message_content(body: str, to: list[str]) -> dict[str, Any]:
    prefix = " ".join(to) + ": " if to else ""
    return {"msgtype": "m.text", "body": prefix + body, "m.mentions": {"user_ids": to}}
```

## Source

Source: <source repo>@0dbe933f3916

## Before starting (destination Claude validation checklist)

Before running this task, verify:
1. All `(exists)` file paths in the Files section still exist in this repo.
2. Each AC is objectively pass/fail (a grep, test invocation, build command, or visible behavior — not "works correctly").
3. All dependencies in the task's frontmatter are status=Done.
4. Out-of-scope items are not accidentally pulled in by ambiguous AC.

If anything is unclear or any check fails: STOP and ask the user. Do NOT start work blindly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A test sends with --to codex-a --to @claude-b and asserts the posted body is '@codex-a @claude-b: <text>' while m.mentions holds both full IDs, for the stdin send and for send --as codex --message-file
- [ ] #2 A test with a config account on a server other than server_name asserts that addressee keeps its full ID in the body prefix
- [ ] #3 A test strips m.mentions from a posted short-prefix message and asserts addressing.addressees() still returns the same full IDs, and that wakes() is true for each addressee and false for a third account
- [ ] #4 The README Addressing row and both SKILL.md --to paragraphs say the body prefix uses the short @name, and grep finds no remaining claim that it carries the full ID
- [ ] #5 Both plugins/agent-chat plugin.json files carry the same bumped patch version
- [ ] #6 uv run pytest plugins/agent-chat and uv run ruff check . both pass
<!-- AC:END -->
