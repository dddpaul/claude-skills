---
id: TASK-53
title: Add an Architecture section to the zmx-peer-chat design doc
status: In Progress
assignee: []
created_date: '2026-10-20 17:43'
updated_date: '2026-10-20 17:44'
labels: []
dependencies: []
ordinal: 53000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
design/zmx-peer-chat.md documents the zmx-peer-chat contract and the box demonstrations (TASK-51), but has no picture of how the pieces fit. Add a ## Architecture section, before ## Versions, with two ASCII diagrams in fenced text blocks: the components on the box (the two zmx sessions with their labels, Claude's hook-run wait, the mailbox, the Codex app-server daemon, the zmx-peer-chat command and the box launcher), and the flows (registration, Claude to Codex, Codex to Claude, Claude's wait across a Happy mode switch). Mark which pieces the provisioning repo sets up, and list the known risks the user asked to keep in view: (1) sends to Codex depend on reading the Codex TUI footer with zmx history; (2) registration depends on an undocumented Codex app-server API, gated by zmx-peer-chat daemon check; (3) the pair works only after provisioning: both sides need the launcher's register call, and the Codex side also needs zmx-peer-chat on the login PATH and the rules merged; apart from register, the Claude side is self-contained. Files: design/zmx-peer-chat.md (exists). Out of scope: code changes, SKILL.md and plugin README changes. The repo is public: no IP address, host name, user name or home path.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 design/zmx-peer-chat.md has a ## Architecture section placed before ## Versions, holding a component diagram and a flow diagram, each in a fenced text code block
- [x] #2 The diagrams mark the pieces the provisioning repo sets up (the launcher, the PATH link, the rules) and point at the known risks with markers that a legend explains
- [x] #3 The section lists the three known risks: the Codex footer read through zmx history, the undocumented app-server API with zmx-peer-chat daemon check as its gate, and the Codex side's dependence on provisioning; each says what fails and how (refuses, exit code, or error text)
- [x] #4 Every line inside both diagrams is at most 100 characters, and every row of the component diagram has the same length (checked with awk over the fenced blocks)
- [x] #5 grep -nE '([0-9]{1,3}\.){3}[0-9]{1,3}|/home/[a-z]|/Users/[a-z]' design/zmx-peer-chat.md prints nothing
- [x] #6 git diff master..HEAD --stat lists only design/zmx-peer-chat.md and the task file
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: interactive (the user asked to discuss the diagram in this session). Generate both diagrams with a scratch script so the box borders line up, add (!n) risk markers and [prov] ownership marks with a legend, insert ## Architecture after the intro and before ## Versions, list the three risks in prose, then run the width awk check and the AC grep, the task-reviewer, Done and merge.

Commit: `77a7d13` - task-53: add an Architecture section with diagrams and known risks to the zmx-peer-chat design doc
<!-- SECTION:NOTES:END -->
