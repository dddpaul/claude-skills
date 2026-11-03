---
id: TASK-65
title: Retest the exact Codex thread pick of zmx-peer-chat register on the box
status: In Progress
assignee: []
created_date: '2026-11-03T17:36:00Z'
updated_date: '2026-11-03T18:27:00Z'
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
- [x] #1 With the user's explicit OK, a zpc-rt- session started as codex ends labelled with its new thread, and the register.log line and the label time are recorded
- [x] #2 A zpc-rt- session started as codex resume --last while the thread is unloaded, and one while it is still loaded, each end labelled with the resumed thread in under FALLBACK_SECONDS
- [x] #3 design/zmx-peer-chat.md records each command, its output and zmx ls before and after, and zmx ls after shows no zpc-rt- session
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: interactive over ssh (Ralph's container cannot reach the box). Copy the 0.1.6 tree to ~/zpc-retest/copy on the box; with the user's OK (given in this session): zpc-rt-codex6 = codex resume --last in ~/zpc-retest/fresh while <thread-r> is unloaded, zpc-rt-codex7 = the same right after codex6 is killed (still loaded), zpc-rt-codex5 = codex in a new ~/zpc-retest/fresh2. No turns. Record label times, register.log, thread/read and footers, zmx ls before/after, in design/zmx-peer-chat.md; then clean up.

Ran from the Mac over ssh (only the Mac reaches the box), with the user's explicit OK in this session, zmx-peer-chat 0.1.6 scratch copy, codex-cli 0.166.0. zmx ls before (21:19:03) and after (21:19:35): only the user's two sessions; grep -c zpc-rt- after: 0. AC #1: zpc-rt-codex5 (codex, new ~/zpc-retest/fresh2) labelled with its new thread after 1.61 s; register.log 21:19:22 labelled. AC #2: zpc-rt-codex6 (codex resume --last, thread unloaded) after 1.62 s and zpc-rt-codex7 (the same a second after codex6 was killed, thread still loaded) after 1.61 s, both with the resumed thread; register.log 21:19:04 and 21:19:07. All under FALLBACK_SECONDS (20). AC #3: design/zmx-peer-chat.md 'The exact pick (TASK-64)' and 'Sessions before and after'. Sessions killed; ~/zpc-retest and our two locks removed; other directories' mail-root entries left alone; transcripts kept. No code changed; no version bump (docs only).

Commit: `c1df0b4` - task-65: record the exact thread pick binding all three cases on the box

Review round 1 (CHANGES REQUESTED, 4): the contract table's manifest version and 'For the launcher' item 4's bind times now match 0.1.6's exact pick (about 1.6 s for codex and codex resume --last; just over FALLBACK_SECONDS only on a fallback); the README's bind times likewise, so zmx-peer-chat goes to 0.1.7 (README only). The record now shows the probe at 21:18:50 before the zmx ls, says the still-loaded case was not probed between kill and start, credits only the still-loaded resume's gain to the exact pick, gives 1.61 to 1.62 s and 'about two hours', and shows the cleanup's pair-dir loop. Notes say 'other directories'.
<!-- SECTION:NOTES:END -->
