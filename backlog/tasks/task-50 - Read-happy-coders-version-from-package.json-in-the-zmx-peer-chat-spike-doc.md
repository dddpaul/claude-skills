---
id: TASK-50
title: Read happy-coder's version from package.json in the zmx peer-chat spike doc
status: To Do
assignee: []
created_date: '2026-10-20 08:38'
updated_date: '2026-10-20 08:45'
labels: []
dependencies: []
priority: medium
ordinal: 50000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

The version table in `design/zmx-peer-chat-spike.md` gets happy-coder's version with `happy --version`. In happy-coder 1.1.9 that command does not exit after printing the version. It goes on to authenticate, make sure the daemon runs and start a Claude session. When `HAPPY_SERVER_URL` is unset, as in a non-login `ssh <box> '...'` shell, it sends the machine's Happy credentials to happy's public default server (`https://api.cluster-fluster.com`). That is the `Error: Request failed with status code 401` the table records: the public server rejected credentials issued by another server. On the spike's box this has since been closed on the box side, but the doc still presents the command as a harmless version check, and anyone who copies it repeats the problem. The version should come from happy-coder's `package.json`, which runs nothing.

## Scope

In scope:
- Replace the happy-coder row of the version table in `design/zmx-peer-chat-spike.md` with the package.json read below and its output.
- Add a short note under the table saying why `happy --version` is not used.

Out of scope:
- Re-running the other version commands or changing any other part of the doc.
- Anything under `plugins/`.
- Any detail of the box's own fix (it lives in the provisioning repo).

The replacement command was run on the box on 2026-10-20 over a non-login ssh shell and printed `1.1.9` (exit 0):

```sh
jq -r .version "$(npm root -g)/happy-coder/package.json"
```

The table cell should show that command and `1.1.9`. The note should say: `happy --version` prints the version and then carries on into authentication and a Claude session; without `HAPPY_SERVER_URL` it contacts happy's public default server with the machine's credentials, which produced the 401 seen in the spike.

## Files

- `design/zmx-peer-chat-spike.md` (exists) - the version table, the happy-coder row and a note under the table.

## Source

Source: ~/Private/Projects/mycloud@c15c84b40276

## Before starting (destination Claude validation checklist)

Before running this task, verify:
1. All `(exists)` file paths in the Files section still exist in this repo.
2. Each AC is objectively pass/fail (a grep, test invocation, build command, or visible behavior - not "works correctly").
3. All dependencies in the task's frontmatter are status=Done.
4. Out-of-scope items are not accidentally pulled in by ambiguous AC.

If anything is unclear or any check fails: STOP and ask the user. Do NOT start work blindly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The happy-coder row of the version table in design/zmx-peer-chat-spike.md shows the command jq -r .version "$(npm root -g)/happy-coder/package.json" and the output 1.1.9
- [ ] #2 grep -n 'happy --version' design/zmx-peer-chat-spike.md matches only lines of the note under the version table, none inside the table
- [ ] #3 The note under the version table states that happy --version does not exit (it authenticates and starts a Claude session) and that without HAPPY_SERVER_URL it contacts happy's public default server with the machine's credentials, the 401 seen in the spike
- [ ] #4 grep -nE '([0-9]{1,3}\.){3}[0-9]{1,3}|/home/[a-z]|/Users/[a-z]' design/zmx-peer-chat-spike.md prints nothing
- [ ] #5 git diff --stat master..HEAD lists only design/zmx-peer-chat-spike.md and this task's file
- [ ] #6 uv run ruff check . passes and uv run pytest has no failures other than test_helper_renders_canonical_decision_tree, which already fails on master
<!-- AC:END -->
