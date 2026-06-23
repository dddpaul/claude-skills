---
id: TASK-36
title: Add onedrive provider to publish skill (v1.3.0)
status: Done
assignee: []
created_date: '2026-06-23 07:33'
updated_date: '2026-06-23 07:44'
labels:
  - 'feature:publish-plugin-split'
dependencies: []
priority: high
ordinal: 36000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Publish skill currently ships two providers (`icloud`, `google-drive` per v1.2.0). User needs to publish docs to OneDrive. Modern macOS OneDrive client syncs into `~/Library/CloudStorage/OneDrive-*` (Personal mounts as `OneDrive-Personal`, Work/School as `OneDrive-<Org>`) — same glob pattern as Google Drive's existing default_root_glob, so the provider shape transfers directly.

This task also serves as the first non-trivial dogfood of the new Python ralph_orchestrator.py that landed in TASK-35 (post-upgrade default).

## Scope

In scope:
- Add a third `onedrive` Provider in `plugins/publish/skills/publish/scripts/providers.py` mirroring `GOOGLE_DRIVE`'s shape (env_var + default_root_glob + triggers tuple).
- Wire the new provider into the `PROVIDERS` dict.
- Extend `test_providers.py` with parallel tests: trigger-phrase resolution for every new EN+RU phrase, env-var override, default_root_glob expansion (mirror the google-drive glob tests structure).
- Update SKILL.md: bump 'v1.1 ships ...' / 'v1.2 ships ...' wording to 'v1.3 ships icloud + google-drive + onedrive'; extend the EN/RU trigger lists in the description and in the body's `onedrive triggers:` section.
- Update `plugins/publish/.claude-plugin/plugin.json` description and version 1.2.0 → 1.3.0.

Out of scope:
- Changes to the `pdf` skill (rendering layer unchanged).
- Changes to how providers are resolved or how transport metadata is written; provider model is generic and transparently supports a third entry.
- Per-organization Work/School OneDrive discrimination (the glob handles both Personal and Work mounts; users with multiple mounts set PUBLISH_ONEDRIVE_DIR explicitly).

## Provider definition (locked from brainstorm)

```python
ONEDRIVE = Provider(
    name="onedrive",
    env_var="PUBLISH_ONEDRIVE_DIR",
    default_root_glob="~/Library/CloudStorage/OneDrive-*",
    triggers=(
        "send to onedrive",
        "send to one drive",
        "read on onedrive",
        "положи в onedrive",
        "положи в ванндрайв",
        "отправь на onedrive",
    ),
)
```

## Files

- `plugins/publish/skills/publish/scripts/providers.py` (exists) — add ONEDRIVE constant + PROVIDERS dict entry
- `plugins/publish/skills/publish/tests/test_providers.py` (exists) — add resolution/env-var/glob tests parallel to google-drive
- `plugins/publish/skills/publish/SKILL.md` (exists) — update description, triggers section, version mention
- `plugins/publish/.claude-plugin/plugin.json` (exists) — bump version 1.2.0 → 1.3.0 and refresh description

## SemVer

Minor bump (1.2.0 → 1.3.0): new provider is additive, no breaking changes for existing icloud/google-drive users.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 providers.py exports ONEDRIVE = Provider(...) matching the locked definition; PROVIDERS dict contains exactly three entries: icloud, google-drive, onedrive
- [x] #2 test_providers.py: every onedrive trigger phrase resolves to 'onedrive' via resolve_provider(); PUBLISH_ONEDRIVE_DIR env-var override beats the glob default; default_root_glob expands against the filesystem (mirror the existing google-drive glob test pattern)
- [x] #3 SKILL.md description frontmatter and triggers section include all 6 onedrive phrases; version mention updated to 'v1.3 ships icloud + google-drive + onedrive'
- [x] #4 plugins/publish/.claude-plugin/plugin.json version bumped 1.2.0 → 1.3.0; description string mentions onedrive alongside icloud and google-drive
- [x] #5 uv run pytest exits 0 (existing 79 tests + new onedrive tests all pass); uv run ruff check . exits 0
- [x] #6 task-reviewer agent on git diff master..HEAD returns APPROVED before merge
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: 1) Add ONEDRIVE Provider constant in providers.py with the locked definition (env_var, default_root_glob ~/Library/CloudStorage/OneDrive-*, 6 triggers). 2) Register in PROVIDERS dict. 3) Mirror google-drive tests in test_providers.py: trigger resolution (param), env-var override, glob expansion (one match / zero matches / multi-account). 4) SKILL.md: bump v1.1/v1.2 mentions to v1.3 ships icloud + google-drive + onedrive; extend triggers section and frontmatter description with 6 new phrases; remove 'No OneDrive' from out-of-scope. 5) plugin.json: 1.2.0 -> 1.3.0; description mentions all three providers. 6) ruff + pytest. 7) task-reviewer.

Commit: `b56aba3` - task-36: add onedrive provider to publish skill (v1.3.0)

Implemented ONEDRIVE provider matching the locked definition; 18 new tests parallel google-drive structure; 97/97 tests pass; ruff clean; task-reviewer APPROVED. Follow-up recommended (out of scope here): update references/providers.md and add references/onedrive.md for full doc parity.
<!-- SECTION:NOTES:END -->
