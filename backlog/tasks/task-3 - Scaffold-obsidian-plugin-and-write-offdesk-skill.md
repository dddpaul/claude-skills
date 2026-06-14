---
id: TASK-3
title: Scaffold obsidian plugin and write offdesk skill
status: Done
assignee: []
created_date: '2026-06-14 06:11'
updated_date: '2026-06-14 07:14'
labels:
  - 'feature:offdesk'
dependencies: []
priority: medium
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create a new obsidian plugin domain inside the existing dddpaul-claude-skills marketplace and ship the offdesk skill — a user-level Claude skill that copies markdown from any project into a Syncthing-synced Obsidian vault on phone/tablet, then pulls annotated `>[!ai]` callouts back to source.

Implementation home: this repo, NOT a separate project. The marketplace already lists architect and presentation; obsidian is the third plugin. Layout mirrors them exactly.

## Marketplace entry

Add to the .claude-plugin/marketplace.json plugins array (do NOT touch existing entries):

```json
{
  "name": "obsidian",
  "source": "./plugins/obsidian",
  "description": "Obsidian vault tooling — offdesk push/pull for off-desk markdown review on phone/tablet via Syncthing."
}
```

## Plugin manifest

Write the following at:

```text
plugins/obsidian/.claude-plugin/plugin.json
```

Contents:

```json
{
  "name": "obsidian",
  "description": "Obsidian vault tooling",
  "version": "0.1.0",
  "author": { "name": "Pavel Derendyaev" },
  "homepage": "https://github.com/dddpaul/claude-skills",
  "repository": "https://github.com/dddpaul/claude-skills",
  "license": "Apache-2.0"
}
```

## Skill file

Write the SKILL.md at:

```text
plugins/obsidian/skills/offdesk/SKILL.md
```

Frontmatter: name=offdesk and a description field that includes all of these trigger phrases (so Claude's skill matcher fires on any of them):

- Push triggers (EN): "send to offdesk", "send to phone for review", "review later", "check later"
- Push triggers (RU): "положи это в offdesk", "положи это в оффдеск", "посмотрю позже", "проверю позже"
- Pull triggers (EN): "review my offdesk notes", "check offdesk feedback"
- Pull triggers (RU): "посмотри оффдеск фидбэк", "проверь оффдеск"

Body sections in this order: Push, Pull, Cleanup, Slug collision, Annotation convention, Setup.

### Push section content

1. Resolve project root via `git rev-parse --show-toplevel` (fallback to `pwd`).
2. Project slug = basename of project root.
3. Create the vault subdir:
   ```bash
   mkdir -p ~/Obsidian/android/<slug>/
   ```
4. Read the source md; parse any existing frontmatter.
5. **Merge** these keys into the existing frontmatter — do NOT prepend a second `---` block, that would break YAML:
   - offdesk-source: relative path from project root
   - offdesk-project-root: absolute project root
   - offdesk-copied-at: ISO 8601 UTC timestamp
6. Keep all existing frontmatter keys untouched (e.g., confluence-* from upmark, jekyll/hugo fields).
7. Write to:
   ```text
   ~/Obsidian/android/<slug>/<filename>.md
   ```
   Syncthing propagates automatically.

### Pull section content

1. Project slug from cwd / `git rev-parse --show-toplevel`.
2. Grep over the per-project vault subdir:
   ```bash
   grep -nrE '^>\s*\[!ai\]' ~/Obsidian/android/<slug>/
   ```
3. For each hit, parse the file's frontmatter to extract offdesk-source and offdesk-project-root for source-back mapping.
4. Report findings as `<source-file>:<line>` + callout content.
5. If the user wants Claude to apply changes (e.g., per `>[!fix]`), **confirm before modifying the source file**.

### Cleanup section content

If the source is also pushed elsewhere (e.g., back to Confluence via upmark push), strip offdesk-* keys from the frontmatter and any `>[!ai]` callouts from the body before that push. Vault copies stay annotated as history.

### Slug collision section content

Two projects with identical basenames will collide in the vault root. Resolution: suffix the slug with a short hash of the project root path (e.g., myproj-a1b2c3) when collision is detected.

### Annotation convention section content

- `>[!ai] question for Claude` — Obsidian block-level callout. Claude addresses these.
- `>[!todo] reminder for the user` — Claude ignores. (`grep -nrE '^>\s*\[!todo\]'` is for the user.)
- Multi-line callouts: each subsequent line also starts with `>`. Obsidian Android auto-inserts `>` on Enter inside an existing callout.
- Both `>[!ai]` and `> [!ai]` (no-space and with-space) render correctly; the grep regex `^>\s*\[!ai\]` handles both.

### Setup section content

One-time per-user manual setup (Syncthing + Obsidian Android + templates + toolbar) is documented in a sibling references file. Link from this section to:

```text
references/setup.md
```

## Setup reference content

Write the setup reference at:

```text
plugins/obsidian/skills/offdesk/references/setup.md
```

Required content sections:

### macOS setup

```bash
brew install syncthing
brew services start syncthing
```

Open Syncthing WebUI at http://127.0.0.1:8384 — Add Folder, path is the laptop vault root, label "offdesk-android", folder ID offdesk-android. Vault root on laptop:

```text
~/Obsidian/android
```

### Android setup

- Install Syncthing on Android from F-Droid (cleanest channel).
- Pair devices: scan the QR from the laptop WebUI on Android, accept the connection request on the laptop side, accept the shared folder on Android.
- Install Obsidian on Android from the Play Store. Open the synced folder as a vault. Android path:

```text
/storage/emulated/0/Obsidian/android/
```

### Obsidian Android — Templates + toolbar

Enable the built-in **Templates** plugin. Create two template files in the vault:

```text
_templates/ai-callout.md
```

Content: `>[!ai] ` (one trailing space; cursor lands after `] `).

```text
_templates/todo-callout.md
```

Content: `>[!todo] `.

Bind both to the bottom toolbar: Settings → Mobile → Manage toolbar options.

### .stignore

Place at the vault root path:

```text
~/Obsidian/android/.stignore
```

Contents:

```text
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/workspace.json.tmp
.DS_Store
*.swp
*.sync-conflict-*
```

## Frontmatter merge — implementation note

The push procedure (step 5) needs to merge three keys into existing YAML frontmatter without breaking it. Prefer an inline shell+python one-liner if it stays under ~30 lines; otherwise create a helper at:

```text
plugins/obsidian/skills/offdesk/scripts/merge-frontmatter.py
```

and invoke it from SKILL.md. Library choice (ruamel.yaml, PyYAML, the yq CLI, or hand-rolled) is the implementer's call — pick whatever has the lowest install footprint for this repo.

## Out of scope

- README updates (separate task — see the feature label).
- Automating any of the user-setup steps.
- iPad / second-device parallel vault.
- Archive/cleanup ergonomics for old vault copies.
- Re-push conflict UX beyond a simple "overwrite (loses pending review)?" confirm when vault copy has unprocessed callouts.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 .claude-plugin/marketplace.json plugins array length is 3 and contains an entry with name="obsidian", source="./plugins/obsidian", and the description string "Obsidian vault tooling — offdesk push/pull for off-desk markdown review on phone/tablet via Syncthing."
- [x] #2 plugins/obsidian/.claude-plugin/plugin.json exists, parses as valid JSON, has version="0.1.0", name="obsidian", license="Apache-2.0", author.name="Pavel Derendyaev", homepage=repository="https://github.com/dddpaul/claude-skills"
- [x] #3 SKILL.md body has a 'Push' section documenting: git rev-parse --show-toplevel project-root resolution with pwd fallback, slug=basename, mkdir -p ~/Obsidian/android/<slug>/, frontmatter merge of offdesk-source/offdesk-project-root/offdesk-copied-at keys, and an explicit statement to NOT prepend a second --- block (merge into existing)
- [x] #4 SKILL.md body has a 'Pull' section documenting: grep -nrE '^>\\s*\\[!ai\\]' over ~/Obsidian/android/<slug>/, frontmatter parse for offdesk-source/offdesk-project-root, report format <source-file>:<line>, and an explicit 'confirm before modifying source files' rule
- [x] #5 SKILL.md body has a 'Cleanup' section documenting that before pushing the source upstream (e.g., to Confluence via upmark), strip offdesk-* keys from frontmatter and >[!ai] callouts from the body
- [x] #6 SKILL.md body has a 'Slug collision' section stating that when two projects share basename, the slug is suffixed with a short hash of project_root
- [x] #7 SKILL.md body has a 'Setup' section that links to references/setup.md (markdown link target resolves)
- [x] #8 uv run ruff check . returns exit code 0
- [x] #9 plugins/obsidian/skills/offdesk/SKILL.md exists and starts with a --- frontmatter block whose name: field equals "offdesk" and whose description: field contains both English and Russian trigger phrases for push and pull (substrings 'send to offdesk', 'положи это в offdesk', 'review my offdesk notes', 'посмотри оффдеск фидбэк' all present)
- [x] #10 plugins/obsidian/skills/offdesk/references/setup.md exists and covers Syncthing macOS install (brew install syncthing), Syncthing Android via F-Droid, device pairing via QR, Obsidian Android install + open vault at /storage/emulated/0/Obsidian/android/, Templates plugin config with ai-callout.md and todo-callout.md, toolbar bindings, and a .stignore block containing all six patterns: .obsidian/workspace.json, .obsidian/workspace-mobile.json, .obsidian/workspace.json.tmp, .DS_Store, *.swp, *.sync-conflict-*
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: 1) marketplace.json — add 'obsidian' entry. 2) plugin.json at plugins/obsidian/.claude-plugin/. 3) SKILL.md at plugins/obsidian/skills/offdesk/ with merged frontmatter description (EN+RU triggers) and Push/Pull/Cleanup/Slug collision/Annotation/Setup sections. 4) references/setup.md with macOS/Android/Templates/.stignore. 5) merge-frontmatter.py helper for YAML merge. 6) ruff check passes.

Commit: `89d7a44` - task-3: scaffold obsidian plugin and offdesk skill

Implemented: marketplace.json (3rd entry obsidian); plugins/obsidian/.claude-plugin/plugin.json (v0.1.0); plugins/obsidian/skills/offdesk/SKILL.md (EN+RU push/pull triggers in frontmatter; Push/Pull/Cleanup/Slug collision/Annotation/Setup sections); references/setup.md (Syncthing macOS+Android, Obsidian Android, Templates, toolbar, .stignore); scripts/merge-frontmatter.py (stdlib YAML merge helper, idempotent). uv run ruff check . passes. task-reviewer agent: APPROVED. Implemented vault path against AC literal (~/Obsidian/android/), not the addendum's ~/Obsidian/offdesk/ — that reconciliation belongs in a follow-up.
<!-- SECTION:NOTES:END -->
