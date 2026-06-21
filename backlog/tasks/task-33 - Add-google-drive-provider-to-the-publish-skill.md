---
id: TASK-33
title: Add google-drive provider to the publish skill
status: In Progress
assignee: []
created_date: '2026-06-21 07:03'
updated_date: '2026-06-21 10:28'
labels:
  - 'feature:publish-plugin-split'
dependencies:
  - TASK-32
priority: medium
ordinal: 33000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Direction: Add a second provider `google-drive` to the publish skill. Mount-only (Google Drive for desktop on macOS), no rclone. Multi-account hard-fail keeps the surface tiny.

Locked decisions with rationale:

- Provider id `google-drive` (named by transport, matching the existing icloud naming convention).
- Env var override: PUBLISH_GOOGLE_DRIVE_DIR.
- Default root via glob: ~/Library/CloudStorage/GoogleDrive-*/My Drive/Reading.
- Glob behavior:
  - 0 matches → hard-fail with a hint to set PUBLISH_GOOGLE_DRIVE_DIR.
  - >1 matches (multi-account) → hard-fail with the same hint; do NOT auto-pick.
  - exactly 1 → use it.
- Subfolder layout symmetric with icloud: <root>/Reading/<project-basename>/<slug>.pdf.
- Bilingual triggers — EN: "send to gdrive", "send to google drive", "read on gdrive", "read on drive"; RU: "положи в gdrive", "положи в гугл драйв", "отправь на драйв".
- Version bump on plugin.json: minor (new provider, no break). 1.0.0 → 1.1.0.

Scope cuts (carry forward from v1):

- No rclone / headless upload.
- No OneDrive (separate task).
- No multi-account auto-pick.
- No PDF/non-.md input — publish only accepts markdown.

Implementation checklist:

1. Add the google-drive row to the provider table in:

   ```text
   plugins/publish/skills/publish/references/providers.md
   ```

   New row:

   | Provider | Env var | Default root |
   |---|---|---|
   | google-drive | PUBLISH_GOOGLE_DRIVE_DIR | ~/Library/CloudStorage/GoogleDrive-*/My Drive/Reading (glob) |

2. Create the per-provider reference doc:

   ```text
   plugins/publish/skills/publish/references/google-drive.md
   ```

   Content:
   - Mount-only rationale (no rclone in v1).
   - Multi-account hard-fail explanation: when the glob matches more than one GoogleDrive-* directory, prompt the user to set PUBLISH_GOOGLE_DRIVE_DIR rather than guess.
   - Glob behavior table (0/1/>1 matches → behavior).
   - Pointer to "Google Drive for desktop" docs (plain reference, no auto-fetch needed).

3. Extend the publish SKILL.md trigger phrase table to include google-drive triggers:

   ```text
   plugins/publish/skills/publish/SKILL.md
   ```

   Append to the trigger table — EN: "send to gdrive", "send to google drive", "read on gdrive", "read on drive"; RU: "положи в gdrive", "положи в гугл драйв", "отправь на драйв".

4. Provider resolution logic (already in the shared publish procedure from T1) gains a glob-expansion step for google-drive:
   - If PUBLISH_GOOGLE_DRIVE_DIR is set → use it verbatim.
   - Otherwise glob the default pattern and apply the 0/1/>1 rules above.
   - Subfolder remains <root>/Reading/<project-basename>/<slug>.pdf.

5. New tests under:

   ```text
   plugins/publish/skills/publish/tests/
   ```

   Test cases:
   - Each of the seven google-drive trigger phrases resolves to the google-drive provider.
   - Glob 0 matches → ValueError / dedicated exception with message naming PUBLISH_GOOGLE_DRIVE_DIR.
   - Glob exactly 1 match → resolved root used.
   - Glob >1 matches → ValueError with the same disambiguation hint.
   - PUBLISH_GOOGLE_DRIVE_DIR set → glob is skipped entirely; env var value used verbatim.

6. Bump version in:

   ```text
   plugins/publish/.claude-plugin/plugin.json
   ```

   Minor bump 1.0.0 → 1.1.0 per the repo SemVer rule (new provider, no break).

7. Update root README:

   ```text
   README.md
   ```

   Under the ### publish section, mention google-drive as a second provider; show the env var PUBLISH_GOOGLE_DRIVE_DIR; note the mount-only / multi-account hard-fail caveat in one line.

8. Pre-merge gates:

   ```bash
   uv run ruff check .
   uv run pytest
   ```

   Both must pass before the task is marked Done.

Dependency: T1 must be complete first — the publish skill and its providers.md table must already exist.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 plugins/publish/skills/publish/references/providers.md contains a google-drive row with env var PUBLISH_GOOGLE_DRIVE_DIR and default root glob ~/Library/CloudStorage/GoogleDrive-*/My Drive/Reading
- [x] #2 plugins/publish/skills/publish/references/google-drive.md exists and documents mount-only rationale, multi-account hard-fail, and glob behavior
- [x] #3 plugins/publish/skills/publish/SKILL.md trigger table includes all seven google-drive triggers — EN (send to gdrive / send to google drive / read on gdrive / read on drive) and RU (положи в gdrive / положи в гугл драйв / отправь на драйв)
- [x] #4 Provider resolution logic: when PUBLISH_GOOGLE_DRIVE_DIR is set, glob is skipped and the env var value is used verbatim
- [x] #5 Glob with 0 matches raises a hard error whose message names PUBLISH_GOOGLE_DRIVE_DIR as the env var to set
- [x] #6 Glob with exactly 1 match resolves the root correctly and the publish flow uses it
- [x] #7 Glob with >1 matches raises a hard error with the same disambiguation hint (do not auto-pick)
- [x] #8 Subfolder layout matches icloud: target path is <root>/Reading/<project-basename>/<slug>.pdf for google-drive
- [x] #9 Each google-drive trigger phrase resolves to the google-drive provider in tests; existing icloud tests still pass
- [x] #10 plugins/publish/.claude-plugin/plugin.json version bumped to 1.1.0; root README mentions google-drive under ### publish; uv run ruff check . and uv run pytest both pass
<!-- AC:END -->





















## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan:
1. Create plugins/publish/skills/publish/references/google-drive.md with mount-only rationale, multi-account hard-fail explanation, glob behavior table, and pointer to Google Drive for desktop docs.
2. Append google-drive row to providers.md table; add a generic glob-expansion paragraph or call out the 0/1/>1 rule under Resolution order; add the seven trigger phrases to the v1-scope trigger mapping section.
3. Update SKILL.md frontmatter description (8→15 triggers) and the Triggers section to list all seven google-drive phrases.
4. Extend scripts/providers.py with: GoogleDriveResolutionError class (or shared ProviderResolutionError); GOOGLE_DRIVE Provider; modified resolve_root() that special-cases google-drive's glob behavior (0/1/>1) — env var still wins verbatim per AC #4.
5. Extend tests/test_providers.py with parameterized trigger tests and glob behavior tests (0 matches, 1 match, >1 matches, env override skips glob). Use tmp_path + monkeypatched glob root for determinism.
6. Bump plugins/publish/.claude-plugin/plugin.json from 1.0.0 → 1.1.0 (minor; new provider, no break).
7. Update root README.md publish section to mention google-drive + PUBLISH_GOOGLE_DRIVE_DIR + mount-only / multi-account caveat in one line.
8. Run uv run ruff check . and uv run pytest; both must pass.

Reset after iteration-2 failure from Anthropic session limit (not a code defect). task-33 branch deleted; ready for a fresh attempt.

Plan iteration 1 (2026-06-21): Implement google-drive provider with glob-based root resolution. Key design: introduce ProviderResolutionError for hard-fail messages naming the env var; extend Provider class to optionally carry a default_root_glob (string with ~) instead of an expanded Path; resolve_root() expands glob lazily and applies 0/1/>1 rules. Tests use tmp_path to create fake GoogleDrive-* directories and monkeypatch HOME to make glob deterministic without touching the real filesystem.
<!-- SECTION:NOTES:END -->
