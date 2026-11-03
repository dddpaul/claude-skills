---
id: TASK-65
title: Retest the exact Codex thread pick of zmx-peer-chat register on the box
status: To Do
assignee: []
created_date: '2026-11-03T17:36:00Z'
labels:
  - zmx-peer-chat
dependencies:
  - TASK-64
priority: medium
ordinal: 65000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

TASK-64 makes `register` pick the Codex thread from the daemon's `thread/started` notification (`codex`), the TUI's own `thread/list` query (`codex resume --last`) and the id (`codex resume <id>`), with the TASK-63 pick as the fallback. Its unit tests use fakes; this task checks the real daemon and TUI on the box with codex-cli 0.166.0, as TASK-61 and TASK-63 did. It runs interactively: Ralph's container cannot reach the box.

## Scope

In scope:
- Copy the working tree to a scratch directory on the box (`tar` over ssh, as in TASK-61 and TASK-63) and run its `bin/zmx-peer-chat`.
- With the user's explicit OK, throwaway Codex sessions (prefix `zpc-rt-`) in a scratch directory, started the way the launcher starts them: `codex` in a directory without history, and `codex resume --last` once with the thread unloaded and once with it still loaded. No Codex turn is needed.
- Record each command and output in `design/zmx-peer-chat.md` (the retest section), with `zmx ls` before and after, using its placeholders (`<box>`, `<home>`, `<uid>`, `<pair-id>`, `<thread-r>`).

Out of scope:
- Code changes, unless the retest finds a defect; then record it and stop for the user.
- The box launcher and the installed plugin version: the source repo owns them.
- Starting Codex sessions on the box without the user's explicit OK. Never type into, queue to, register or kill the user's own zmx sessions.

## Files

- `design/zmx-peer-chat.md` (exists): "Retest with codex-cli 0.166.0"

Public repo: no IP address, host name, user name, home path, token or conversation text in the doc.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 With the user's explicit OK, a zpc-rt- session started as codex ends labelled with its new thread, and the register.log line and the label time are recorded
- [ ] #2 A zpc-rt- session started as codex resume --last while the thread is unloaded, and one while it is still loaded, each end labelled with the resumed thread in under FALLBACK_SECONDS
- [ ] #3 design/zmx-peer-chat.md records each command, its output and zmx ls before and after, and zmx ls after shows no zpc-rt- session
<!-- AC:END -->
