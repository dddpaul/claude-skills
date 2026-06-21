---
id: TASK-32
title: >-
  Refactor reading plugin into publish plugin with pdf and publish(icloud)
  skills
status: Done
assignee: []
created_date: '2026-06-21 07:03'
updated_date: '2026-06-21 07:18'
labels:
  - 'feature:publish-plugin-split'
dependencies: []
priority: medium
ordinal: 32000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Direction: Rename the plugin `reading` to `publish` and split the single books skill into two sibling skills — pdf (conversion-only, callable directly) and publish (umbrella with provider config; ships only the icloud provider in v1). Every existing books trigger phrase continues to work end-to-end and routes to the icloud provider.

Locked decisions with rationale:

- Plugin rename reading → publish is a hard major bump (v1.0.0). The umbrella skill is named publish, the plugin should match. Install snippet becomes /plugin install publish@dddpaul-claude-skills.
- pdf is a standalone callable skill (not just a script). Users can render to PDF without uploading.
- publish shells out directly to the pdf skill's script instead of skill-to-skill plumbing. One script remains the source of truth; fewer hops.
- Providers are named by transport (`icloud`), not by consumer device. Reframes iCloud-as-transport with Apple Books on iPad as one consumer. Makes adding future consumers easier without rename.
- Subfolder layout: <provider-root>/Reading/<project-basename>/<slug>.pdf. Symmetric across providers.
- Env var rename READING_ICLOUD_DIR → PUBLISH_ICLOUD_DIR with NO fallback. Clean break in v1.0; single-user plugin, minimal upgrade cost.

Scope cuts (carry forward):

- No EPUB output, no rclone/headless upload, no non-.md input, no syntax highlighting, no multi-file batching, no cleanup, no annotation pull-back, no OneDrive in v1, no READING_ICLOUD_DIR deprecation grace.

Implementation checklist:

1. Plugin rename (preserves history):

   ```bash
   git mv plugins/reading plugins/publish
   ```

2. Books → pdf skill rename (preserves history on scripts/, references/, tests/):

   ```bash
   git mv plugins/publish/skills/books plugins/publish/skills/pdf
   ```

3. Rewrite the pdf skill SKILL.md to be conversion-only:

   ```text
   plugins/publish/skills/pdf/SKILL.md
   ```

   - Frontmatter description includes bilingual triggers — EN: "convert to pdf", "render as pdf", "md to pdf"; RU: "сделай pdf", "сконвертируй в pdf", "из markdown в pdf".
   - Interface contract:

     ```bash
     uv run plugins/publish/skills/pdf/scripts/md-to-pdf.py <source.md> [<target.pdf>]
     ```

     Hard-fail on non-.md extension. If target.pdf omitted, write <source-dir>/<source-stem>.pdf next to source. Atomic write via .tmp + os.replace (already implemented).
   - Document dependencies:

     ```bash
     uv add weasyprint markdown
     brew install cairo pango gdk-pixbuf
     brew install --cask font-ibm-plex
     ```

   - Strip iCloud / push procedure prose from the old books SKILL.md — that content moves to the publish skill.

4. Create the new publish skill:

   ```text
   plugins/publish/skills/publish/SKILL.md
   plugins/publish/skills/publish/references/providers.md
   plugins/publish/skills/publish/references/icloud.md
   plugins/publish/skills/publish/tests/
   ```

   - SKILL.md frontmatter declares the eight icloud triggers — EN: "send to books", "read on ipad", "review on books", "send to icloud"; RU: "положи это в books", "положи это в книги", "почитаю на айпаде", "положи в icloud".
   - SKILL.md body documents the shared push procedure:
     1. Identify provider from matched trigger phrase. If no specific provider matched (e.g., just "publish this" / "отправь это"), ask which provider, then proceed.
     2. Resolve source path. Hard-fail if extension is not .md.
     3. Compute slug = Path(source).stem. On collision in target subfolder, suffix -<sha1(absolute_source_path)[:6]>.
     4. Resolve project root via `git rev-parse --show-toplevel`. Fall back to dirname(source) if not a git repo. Subfolder name = basename(project_root).
     5. Resolve provider root from env var or default (providers.md).
     6. mkdir -p the per-project subfolder under <root>/Reading/<project-basename>.
     7. Shell out to the pdf skill script:

        ```bash
        uv run plugins/publish/skills/pdf/scripts/md-to-pdf.py "<source.md>" "<root>/Reading/<project>/<slug>.pdf"
        ```

     8. Print the final iCloud path to the user.
   - providers.md table (v1 lists only icloud):

     | Provider | Env var | Default root |
     |---|---|---|
     | icloud | PUBLISH_ICLOUD_DIR | ~/Library/Mobile Documents/com~apple~CloudDocs/Reading |

   - icloud.md covers iCloud-as-transport notes with an "Apple Books on iPad is one consumer" sidebar; pen marks stay with the human; no annotation pull-back.

5. Update plugin manifest:

   ```text
   plugins/publish/.claude-plugin/plugin.json
   ```

   Major version bump to 1.0.0 per the repo SemVer rule (rename = breaking). Description: covers both pdf and publish skills.

6. Update marketplace manifest:

   ```text
   .claude-plugin/marketplace.json
   ```

   Rename entry reading → publish. Update source to ./plugins/publish. Rewrite description.

7. Tests:
   - Existing anchor tests continue to pass at the new path under pdf/tests/.
   - New tests for the publish skill (under publish/tests/):
     - Each of the eight icloud trigger phrases resolves to the icloud provider (parameterized).
     - Env-var precedence: when PUBLISH_ICLOUD_DIR is set, the override path is used; when unset, the default root is used.
     - READING_ICLOUD_DIR is not read anywhere — setting it has no effect.
     - No-provider-matched flow: when a user phrase matches publish but no specific provider, resolver returns a needs-disambiguation sentinel (not silent default to icloud).

8. Update root README:

   ```text
   README.md
   ```

   Replace ### books and ### reading sections with ### pdf and ### publish. Update install snippets to /plugin install publish@dddpaul-claude-skills. Update Project Structure ASCII tree to match the new layout.

9. Pre-merge gates:

   ```bash
   uv run ruff check .
   uv run pytest
   ```

   Both must pass before the task is marked Done.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Plugin directory renamed: plugins/reading/ removed, plugins/publish/ exists with skills pdf/ and publish/
- [x] #2 plugins/publish/skills/pdf/SKILL.md is conversion-only (no iCloud/push procedure prose) and declares bilingual triggers EN (convert to pdf / render as pdf / md to pdf) and RU (сделай pdf / сконвертируй в pdf / из markdown в pdf)
- [x] #3 plugins/publish/skills/pdf/scripts/md-to-pdf.py and plugins/publish/skills/pdf/references/styles.css preserved via git mv from old books paths
- [x] #4 plugins/publish/skills/publish/SKILL.md declares all eight icloud triggers — EN (send to books / read on ipad / review on books / send to icloud) and RU (положи это в books / положи это в книги / почитаю на айпаде / положи в icloud)
- [x] #5 plugins/publish/skills/publish/references/providers.md lists only the icloud provider with env var PUBLISH_ICLOUD_DIR and default root ~/Library/Mobile Documents/com~apple~CloudDocs/Reading; references/icloud.md covers iCloud-as-transport notes
- [x] #6 grep -r READING_ICLOUD_DIR plugins/ returns no matches
- [x] #7 uv run pytest passes at plugins/publish/skills/pdf/tests/test_anchors.py
- [x] #8 New publish tests pass under uv run pytest plugins/publish/skills/publish/tests/: each icloud trigger resolves to the icloud provider, PUBLISH_ICLOUD_DIR overrides default, no-provider-matched flow returns needs-disambiguation rather than silent default
- [x] #9 .claude-plugin/marketplace.json lists publish (not reading) with source ./plugins/publish; root README.md replaces ### books and ### reading sections with ### pdf and ### publish and updates the install snippet to /plugin install publish@dddpaul-claude-skills
- [x] #10 plugins/publish/.claude-plugin/plugin.json version bumped to 1.0.0; uv run ruff check . passes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan:
1. git mv plugins/reading plugins/publish; git mv .../books .../pdf.
2. Rewrite pdf SKILL.md as conversion-only (bilingual triggers; interface; deps).
3. Create publish skill: SKILL.md (8 icloud triggers + push procedure), references/providers.md (icloud only), references/icloud.md.
4. Add provider resolver Python module to support tests for trigger->provider, env-var override, disambiguation, and READING_ICLOUD_DIR ignored.
5. plugins/publish/.claude-plugin/plugin.json -> 1.0.0; rewrite description.
6. .claude-plugin/marketplace.json: reading -> publish entry.
7. README: replace ### books and ### reading with ### pdf and ### publish; update install snippet and Project Structure tree.
8. Gates: uv run ruff check . && uv run pytest.

Commit: `9a921a4` - task-32: split reading plugin into publish plugin with pdf and publish skills

Implementation: plugin rename via git mv reading→publish; books skill renamed to pdf (conversion-only); new umbrella publish skill with eight icloud triggers; PUBLISH_ICLOUD_DIR replaces legacy env var (no fallback); plugin bumped to 1.0.0; marketplace + README updated; ruff + 58 pytest passing; task-reviewer APPROVED.
<!-- SECTION:NOTES:END -->
