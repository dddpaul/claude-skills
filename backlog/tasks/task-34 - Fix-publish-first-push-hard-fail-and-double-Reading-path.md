---
id: TASK-34
title: Fix publish first-push hard-fail and double-Reading path
status: Done
assignee: []
created_date: '2026-06-21 10:55'
updated_date: '2026-06-21 11:12'
labels:
  - 'feature:publish-plugin-split'
dependencies: []
priority: high
ordinal: 34000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Direction: Strip the `/Reading` suffix from the icloud and google-drive default roots in the publish skill resolver so (a) the google-drive first push no longer hard-fails on a missing Reading/ directory, and (b) the on-disk path stops doubling to <root>/Reading/Reading/<project>/<slug>.pdf.

Symptoms surfaced by a live push on 2026-06-21:

- Defect 1 — First-push hard-fail (google-drive only): the default glob ends in `/My Drive/Reading`, but Reading/ doesn't exist on a fresh Google Drive for desktop install. The very skill that is meant to create the Reading folder cannot run until the folder exists. Resolver raises ProviderResolutionError; user has to manually mkdir or set PUBLISH_GOOGLE_DRIVE_DIR.
- Defect 2 — Double-Reading on disk (both providers): providers.md default roots end in `/Reading`, and the push procedure documented in publish/SKILL.md step 6 layers `<root>/Reading/<project>/<slug>.pdf` on top. Final on-disk paths: `~/Library/Mobile Documents/com~apple~CloudDocs/Reading/Reading/<project>/<slug>.pdf` and `~/.../GoogleDrive-*/My Drive/Reading/Reading/<project>/<slug>.pdf`.

Root cause: providers.md and providers.py default roots include `/Reading` AND the push-procedure layout in SKILL.md adds `/Reading/<project>/<slug>.pdf` on top. Either the defaults should NOT end in `/Reading`, or the procedure should not add it. The cleanest fix is to drop the suffix from the defaults so the procedure's layout is the single source of truth for the `Reading/` segment.

Locked decisions with rationale:

- icloud default_root becomes `~/Library/Mobile Documents/com~apple~CloudDocs` (was `.../CloudDocs/Reading`). The push procedure already adds `/Reading/<project>/<slug>.pdf`, so the final on-disk path stays `.../CloudDocs/Reading/<project>/<slug>.pdf` — matches the legacy books skill exactly.
- google-drive default_root_glob becomes `~/Library/CloudStorage/GoogleDrive-*/My Drive` (was `.../GoogleDrive-*/My Drive/Reading`). The glob now targets `My Drive`, which exists on a fresh Google Drive for desktop install. First push no longer hard-fails. Final on-disk path: `.../My Drive/Reading/<project>/<slug>.pdf` (single Reading, symmetric with icloud).
- Env-var precedence semantics unchanged: PUBLISH_ICLOUD_DIR and PUBLISH_GOOGLE_DRIVE_DIR still win verbatim when set. Only the defaults change.
- Version bump: minor (1.1.0 → 1.2.0). Default-root change is a behavior tweak, not an API break. Trigger phrases, env-var names, SKILL.md surface all unchanged.

Scope cuts:

- No automated migration of any content that may have landed at `<root>/Reading/Reading/<project>/` during v1.0–1.1. User manually `mv`s those (likely zero or one file in practice).
- No env-var aliasing or fallback. The only behavior change is the default root.
- No revisit of the push-procedure layout text (the `<root>/Reading/<project>/<slug>.pdf` line in publish/SKILL.md step 6 stays). The fix is in the defaults, not the procedure.

Implementation checklist:

1. Edit:

   ```text
   plugins/publish/skills/publish/scripts/providers.py
   ```

   - ICLOUD: `default_root=Path("~/Library/Mobile Documents/com~apple~CloudDocs").expanduser()`.
   - GOOGLE_DRIVE: `default_root_glob="~/Library/CloudStorage/GoogleDrive-*/My Drive"`.

2. Update the default-root column for both providers in:

   ```text
   plugins/publish/skills/publish/references/providers.md
   ```

3. Update the "Default root" section in:

   ```text
   plugins/publish/skills/publish/references/icloud.md
   plugins/publish/skills/publish/references/google-drive.md
   ```

   In google-drive.md also update the "Multi-account hard-fail" code block (the glob example) to drop `/Reading`.

4. Update glob fixtures in:

   ```text
   plugins/publish/skills/publish/tests/test_providers.py
   ```

   - Glob fixtures must create `<tmp>/Library/CloudStorage/GoogleDrive-<account>/My Drive/` directories (NOT `My Drive/Reading/`).
   - Add a new test that asserts resolve_root("google-drive") succeeds when a fresh `My Drive/` exists with NO `Reading/` subdir — this is the regression test for Defect 1.
   - Adjust the existing 0-match, 1-match, >1-match tests to use the new glob target.
   - Adjust expected resolved-root strings everywhere they appear.

5. Bump version in:

   ```text
   plugins/publish/.claude-plugin/plugin.json
   ```

   1.1.0 → 1.2.0.

6. Pre-merge gates:

   ```bash
   uv run ruff check .
   uv run pytest
   ```

   Both must pass before the task is marked Done.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 providers.py ICLOUD default_root resolves to ~/Library/Mobile Documents/com~apple~CloudDocs (no trailing /Reading)
- [x] #2 providers.py GOOGLE_DRIVE default_root_glob equals ~/Library/CloudStorage/GoogleDrive-*/My Drive (no trailing /Reading)
- [x] #3 New regression test: with PUBLISH_GOOGLE_DRIVE_DIR unset and a fresh My Drive/ that contains NO Reading/ subdir, resolve_root('google-drive') returns the My Drive path and does NOT raise ProviderResolutionError
- [x] #4 Existing google-drive glob tests (0-match, 1-match, multi-account >1-match) updated so fixtures create My Drive/ directories instead of My Drive/Reading/ and still pass
- [x] #5 providers.md default-root table shows ~/Library/Mobile Documents/com~apple~CloudDocs for icloud and ~/Library/CloudStorage/GoogleDrive-*/My Drive (glob) for google-drive (no trailing /Reading on either)
- [x] #6 icloud.md Default root section reads ~/Library/Mobile Documents/com~apple~CloudDocs; google-drive.md Default root and Multi-account hard-fail code blocks show ~/Library/CloudStorage/GoogleDrive-*/My Drive
- [x] #7 plugins/publish/.claude-plugin/plugin.json version bumped from 1.1.0 to 1.2.0
- [x] #8 uv run ruff check . and uv run pytest both pass
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: (1) Strip /Reading from icloud default_root and google-drive default_root_glob in providers.py. (2) Update providers.md table, icloud.md and google-drive.md Default-root sections (and the Multi-account glob example in google-drive.md). (3) Update test_providers.py: change _make_gdrive_account to create My Drive/ (no Reading/), adjust expected icloud default-root assertions in test_default_root_when_publish_icloud_dir_unset and test_legacy_env_var_is_ignored, add a regression test for Defect 1 (My Drive exists, no Reading/ subdir, resolve_root returns My Drive). (4) Bump publish plugin version 1.1.0 -> 1.2.0. (5) Run ruff and pytest gates.

Commit: `18f91bb` - task-34: drop trailing /Reading from publish provider defaults (v1.2.0)

Implemented: stripped /Reading from icloud default_root and google-drive default_root_glob in providers.py; mirrored in providers.md, icloud.md, google-drive.md; updated test fixtures + added test_google_drive_glob_resolves_when_my_drive_has_no_reading_subdir regression for Defect 1; bumped plugin version 1.1.0 -> 1.2.0. ruff clean; full pytest 79 passed. task-reviewer APPROVED.
<!-- SECTION:NOTES:END -->
