---
id: TASK-67
title: >-
  Explain in both READMEs when to use agent-chat or zmx-peer-chat and how they
  depend on each other
status: Done
assignee: []
created_date: '2026-11-04T06:43:00Z'
updated_date: '2026-11-04T07:04:00Z'
labels:
  - agent-chat
  - zmx-peer-chat
dependencies: []
priority: low
ordinal: 67000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

agent-chat and zmx-peer-chat both let Claude and Codex talk, and both READMEs describe only their own plugin. A reader who wants Claude to reach Codex has to work out which one applies, and what one plugin borrows from the other. agent-chat's skill descriptions already fence off the box-local pair ("Not for a peer in the same box's zmx pair (that is zmx-peer-chat)"). zmx-peer-chat's descriptions say "Box only" but do not name agent-chat for the cross-host case.

## Scope

In scope:
- **README sections.** Add one section, "agent-chat or zmx-peer-chat?", to both `plugins/agent-chat/README.md` and `plugins/zmx-peer-chat/README.md`, with the same content in each. It contains a short table, then one paragraph each on the dependency and the shared footer rule.

  The table:

  | | zmx-peer-chat | agent-chat |
  |---|---|---|
  | Who talks | Exactly one Claude and one Codex in the same project directory on one box, each in its own zmx session | Agents on any host, and the user |
  | Transport | Local only: `codex queue` to Codex, a file mailbox to Claude | The project's room on a private Matrix homeserver |
  | Identity and addressing | zmx labels set by `register` (`zpc.pair`, `zpc.role`, `zpc.inc`, `zpc.thread`); the one peer of the pair | One Matrix account per agent and host; `@name` mentions; an unaddressed message from the user wakes every listener |
  | History | None; mail is consumed | The room keeps it; the user reads and answers in Element |
  | Codex API | The app-server daemon (internal), only to bind the thread at registration | `codex queue` only |

  - **The dependency runs one way.** In all-rooms mode, agent-chat's `watch-codex` finds the Codex thread through zmx-peer-chat's labels: the `zpc.role=codex` session whose `cwd` is the room's directory, then its `zpc.thread` and `zpc.inc`. A Codex session that register did not bind gets neither peer mail nor room mail. `watch-codex --thread <uuid>` needs no zmx-peer-chat. zmx-peer-chat knows nothing about agent-chat.
  - **The footer rule is shared.** Both refuse to queue unless the TUI footer shows `· zpc-<inc>` in the last six non-empty lines. agent-chat keeps its own copy because the plugins ship separately, so a Codex footer change needs both copies updated.
- **Skill fences.** zmx-peer-chat's Claude `SKILL.md` and Codex `SKILL.md` descriptions gain one fence naming agent-chat, for example: "Not for agents on other hosts or the user's project room (that is agent-chat)". The fence narrows nothing the skill did before.
- **Versions.** A patch bump of both plugins, in both `plugin.json` files of each. If a test pins agent-chat's manifest version, update it too.

Out of scope:
- Any code change.
- The root `README.md`, beyond a link to the new section if its plugin entries already describe either plugin.
- The design docs.

## Files

- `plugins/agent-chat/README.md`, `plugins/zmx-peer-chat/README.md` (exist)
- `plugins/zmx-peer-chat/skills/zmx-peer-chat/SKILL.md`, `plugins/zmx-peer-chat/codex-skills/zmx-peer-chat/SKILL.md` (exist): the `description`
- `plugins/agent-chat/.claude-plugin/plugin.json`, `plugins/agent-chat/.codex-plugin/plugin.json` (exist): version 0.2.2
- `plugins/zmx-peer-chat/.claude-plugin/plugin.json`, `plugins/zmx-peer-chat/.codex-plugin/plugin.json` (exist): version 0.1.7
- `plugins/agent-chat/skills/agent-chat/tests/test_agent_chat_codex.py` (exists): pins agent-chat's manifest version
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 plugins/agent-chat/README.md and plugins/zmx-peer-chat/README.md each have a section headed 'agent-chat or zmx-peer-chat?' with the same comparison table
- [x] #2 Both sections state that watch-codex in all-rooms mode reads zmx-peer-chat's zpc.* labels, that --thread mode does not, and that zmx-peer-chat does not depend on agent-chat
- [x] #3 Both sections state that the footer rule is copied into agent-chat and must change in both plugins together
- [x] #4 The description in both zmx-peer-chat SKILL.md files (Claude and Codex) names agent-chat for agents on other hosts and the user's project room
- [x] #5 uv run ruff check . passes and uv run pytest passes, except the known test_decision_tree_helper failure (un-vendored node_modules)
- [x] #6 The version in both agent-chat plugin.json files and both zmx-peer-chat plugin.json files is one patch above the version current at merge
- [x] #7 The test that pins agent-chat's manifest version (test_agent_chat_codex.py) matches the bumped version
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: insert one identical 'agent-chat or zmx-peer-chat?' section into both READMEs after the intro, add the agent-chat fence to both zmx-peer-chat SKILL.md descriptions, patch-bump agent-chat 0.2.2->0.2.3 and zmx-peer-chat 0.1.8->0.1.9 (TASK-66 had already moved it past the body's 0.1.7), update the test pin, link the section from the root README entries. Codex API cell also names 'daemon check', which talks to the daemon too (zpc/cli.py cmd_daemon).

Commit: `6f7fb97` - task-67: compare agent-chat and zmx-peer-chat in both READMEs and fence zmx-peer-chat's skills off agent-chat

Commit: `a259181` - task-67: limit the shared footer rule to registered sessions and name every daemon use

Done. task-reviewer: first pass CHANGES REQUESTED (footer rule overstated for --thread mode; Codex API cell missed daemon skills; hard-wrapped paragraphs), all fixed in a259181; re-review APPROVED. ruff clean; pytest 575 passed, 1 known failure (test_decision_tree_helper). Root README entries link to the new section.
<!-- SECTION:NOTES:END -->
