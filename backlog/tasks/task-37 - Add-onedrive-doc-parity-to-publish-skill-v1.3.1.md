---
id: TASK-37
title: Add onedrive doc parity to publish skill (v1.3.1)
status: In Progress
assignee: []
created_date: '2026-06-23 08:34'
updated_date: '2026-06-23 08:39'
labels:
  - 'feature:publish-plugin-split'
dependencies: []
priority: medium
ordinal: 37000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

The 2nd cumulative review for publish-plugin-split (design/publish-plugin-split-review-2026-06-23.md, verdict: Partial) flagged three doc-parity drifts after TASK-36 shipped onedrive code/tests/SKILL.md/plugin.json:

1. references/providers.md is stale — still only icloud + google-drive rows, no onedrive entry, no PUBLISH_ONEDRIVE_DIR
2. references/onedrive.md does not exist (per-provider deep-dive pattern broken — icloud.md and google-drive.md exist)
3. Root README.md "### publish" section still says "v1.1 ships two providers" and omits all 6 onedrive triggers

SKILL.md "Providers" paragraph also has a [[icloud]], [[google-drive]] wikilink list with no [[onedrive]] — patch that too.

Move feature verdict from Partial to Aligned. Pure doc patch, no code changes.

## Scope

In scope:
- providers.md: add onedrive row; refresh trigger-mapping section
- Create references/onedrive.md mirroring google-drive.md (mount-only, multi-account hard-fail, default-root, push-only, slug collision, macOS Personal-vs-Work/School naming note)
- README.md "### publish" section: bump to v1.3, three providers, list onedrive triggers + PUBLISH_ONEDRIVE_DIR
- SKILL.md Providers wikilink list: add [[onedrive]]
- plugin.json version 1.3.0 → 1.3.1 (patch — doc-only)

Out of scope:
- providers.py / test_providers.py — code is already correct
- Any rename, deprecation, or behavior change

## Files

- plugins/publish/skills/publish/references/providers.md (exists, stale)
- plugins/publish/skills/publish/references/onedrive.md (to-create)
- README.md (exists, ### publish section stale at line ~114)
- plugins/publish/skills/publish/SKILL.md (exists — Providers paragraph wikilink list only)
- plugins/publish/.claude-plugin/plugin.json (exists, version bump)

## SemVer

Patch bump (1.3.0 → 1.3.1) — docs only, no behavior or API change.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 providers.md provider table includes an onedrive row with env_var PUBLISH_ONEDRIVE_DIR and default_root_glob ~/Library/CloudStorage/OneDrive-*
- [x] #2 providers.md trigger-mapping section lists all 6 onedrive trigger phrases (EN: send to onedrive / send to one drive / read on onedrive; RU: положи в onedrive / положи в ванндрайв / отправь на onedrive)
- [x] #3 plugins/publish/skills/publish/references/onedrive.md exists and mirrors google-drive.md structure: mount-only rationale, multi-account hard-fail with PUBLISH_ONEDRIVE_DIR hint, default-root section, push-only stance, slug collision note, macOS Personal vs Work/School naming note
- [x] #4 README.md '### publish' section reads 'v1.3 ships three providers' (or equivalent), mentions PUBLISH_ONEDRIVE_DIR, and includes at least 3 example onedrive trigger phrases
- [x] #5 plugins/publish/skills/publish/SKILL.md Providers paragraph wikilink list contains [[icloud]], [[google-drive]], and [[onedrive]]
- [x] #6 plugins/publish/.claude-plugin/plugin.json version bumped 1.3.0 → 1.3.1
- [x] #7 uv run ruff check . exits 0 and uv run pytest exits 0
- [ ] #8 task-reviewer agent on git diff master..HEAD returns APPROVED before merge
<!-- AC:END -->
