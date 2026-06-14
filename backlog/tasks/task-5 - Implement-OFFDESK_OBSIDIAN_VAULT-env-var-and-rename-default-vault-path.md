---
id: TASK-5
title: Implement OFFDESK_OBSIDIAN_VAULT env var and rename default vault path
status: Done
assignee: []
created_date: '2026-06-14 07:43'
updated_date: '2026-06-14 07:54'
labels:
  - 'feature:offdesk'
dependencies:
  - TASK-3
priority: medium
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Land addendum #1 from the offdesk design (device-neutral default vault path + configurable via env var). Initial v0.1.0 shipped with hardcoded laptop vault root because TASK-3's AC text froze the old path; this task pulls SKILL.md, setup.md, marketplace.json, and the plugin manifest into line with the canonical design intent.

## Why a follow-up, not part of v0.1.0

The implementer of TASK-3 spotted the AC-vs-addendum mismatch, made the conservative call to honor the AC literal, and flagged a follow-up. Review verdict on the offdesk feature was Partial because of this single drift. Closing this task moves the feature from Partial → Aligned and the plugin from 0.1.0 → 0.2.0.

## SKILL.md changes

Target: plugins/obsidian/skills/offdesk/SKILL.md

Add a new section near the top of the body (before the Push section) titled "Vault path" or "Environment", documenting the env var contract:

```text
Default vault root on the laptop: ~/Obsidian/offdesk/
Override: set OFFDESK_OBSIDIAN_VAULT in your shell profile (~/.zshrc or ~/.bashrc) to point at any directory. The skill reads it at every invocation; restart the shell after editing.
```

In the Push procedure, replace the hardcoded vault path with the env var expansion. Step 3 of the procedure should read like this (or equivalent prose around the same shell snippet):

```bash
VAULT_ROOT="${OFFDESK_OBSIDIAN_VAULT:-$HOME/Obsidian/offdesk}"
VAULT_ROOT="${VAULT_ROOT%/}"   # strip trailing slash for consistency
mkdir -p "$VAULT_ROOT/<slug>/"
```

In step 7 (Write to vault), update the destination path to:

```text
$VAULT_ROOT/<slug>/<filename>.md
```

In the Pull procedure, the grep target uses the same env var expansion:

```bash
VAULT_ROOT="${OFFDESK_OBSIDIAN_VAULT:-$HOME/Obsidian/offdesk}"
VAULT_ROOT="${VAULT_ROOT%/}"
grep -nrE '^>\s*\[!ai\]' "$VAULT_ROOT/<slug>/"
```

The call site that invokes scripts/merge-frontmatter.py (currently passing a hardcoded path as the dst arg) must use \$VAULT_ROOT/<slug>/<filename>.md instead.

Cleanup section path mentions: any reference to ~/Obsidian/android in the body must be removed. The cleanup procedure itself is path-agnostic (it operates on the source md, not the vault copy) so no shell snippet change is needed — only prose tidying.

## references/setup.md changes

Target: plugins/obsidian/skills/offdesk/references/setup.md

Replace the laptop vault root from ~/Obsidian/android to ~/Obsidian/offdesk throughout. Specifically:

- macOS section, Syncthing WebUI Add Folder step: path becomes the new default

  ```text
  ~/Obsidian/offdesk
  ```

- .stignore location:

  ```text
  ~/Obsidian/offdesk/.stignore
  ```

- Add a short note (one or two sentences) right after the macOS Syncthing folder add step, telling users with a non-default Obsidian layout to override via the OFFDESK_OBSIDIAN_VAULT env var in their shell profile.

- Syncthing folder label and folder ID: note that both can stay as 'offdesk-android' (legacy) OR be renamed to 'offdesk' at the user's discretion. The skill doesn't care.

Android-side path stays at:

```text
/storage/emulated/0/Obsidian/android/
```

That path is the Syncthing folder mapping on the Android device, set independently of the laptop env var. Do NOT change it; document this independence explicitly so a user doesn't try to align it with the laptop path.

## marketplace.json changes

Target: .claude-plugin/marketplace.json (obsidian plugin entry only — do NOT touch architect or presentation entries)

Update the description text. Currently:

```text
Obsidian vault tooling — offdesk push/pull for off-desk markdown review on phone/tablet via Syncthing.
```

Change to (drop the 'phone/tablet' specificity, which addendum #1 calls out as misleading):

```text
Obsidian vault tooling — offdesk push/pull for off-desk markdown review via Syncthing.
```

## plugin.json version bump

Target: plugins/obsidian/.claude-plugin/plugin.json

Change the version field from \"0.1.0\" to \"0.2.0\". Minor bump per the project's SemVer rules in CLAUDE.md: this broadens the configuration surface (adds env var support, renames default folder) — not breaking because there are no existing users.

## Out of scope

- D-2 from the review: merge-frontmatter.py minor cleanup (YAML-escape in merge_keys + dead code removal of the `missing` check). Separate task if desired.
- README.md Installation block changes — none needed since the install command is identical.
- Migration tooling for existing users — there are no existing users at v0.1.0.
- Renaming the Syncthing folder ID (offdesk-android → offdesk). User's choice, documented but not forced.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 plugins/obsidian/skills/offdesk/SKILL.md has a section near the top of the body (before the Push section) documenting the OFFDESK_OBSIDIAN_VAULT env var contract: default value ~/Obsidian/offdesk/ and override-via-shell-profile instructions
- [x] #2 plugins/obsidian/skills/offdesk/SKILL.md Push procedure documents the literal shell pattern VAULT_ROOT="${OFFDESK_OBSIDIAN_VAULT:-$HOME/Obsidian/offdesk}" with trailing-slash normalization before mkdir -p "$VAULT_ROOT/<slug>/"
- [x] #3 plugins/obsidian/skills/offdesk/SKILL.md Pull procedure uses $VAULT_ROOT/<slug>/ (resolved from OFFDESK_OBSIDIAN_VAULT or default) as the grep target rather than a hardcoded path
- [x] #4 plugins/obsidian/skills/offdesk/SKILL.md call site that invokes scripts/merge-frontmatter.py uses $VAULT_ROOT/<slug>/<filename>.md as the destination path, not a hardcoded ~/Obsidian/android path
- [x] #5 grep -F '~/Obsidian/android' plugins/obsidian/skills/offdesk/SKILL.md returns no matches (all references to the old laptop default removed)
- [x] #6 plugins/obsidian/skills/offdesk/references/setup.md uses ~/Obsidian/offdesk as the laptop vault root in the Syncthing Add Folder step and in the .stignore location; the only remaining 'Obsidian/android' string in the file is the Android-side path /storage/emulated/0/Obsidian/android/
- [x] #7 plugins/obsidian/skills/offdesk/references/setup.md contains a sentence explaining that users with a non-default Obsidian layout can override the laptop vault path via the OFFDESK_OBSIDIAN_VAULT env var in their shell profile
- [x] #8 .claude-plugin/marketplace.json obsidian plugin entry description equals 'Obsidian vault tooling — offdesk push/pull for off-desk markdown review via Syncthing.' (the phrase 'phone/tablet' is removed)
- [x] #9 plugins/obsidian/.claude-plugin/plugin.json version field equals "0.2.0"
- [x] #10 uv run ruff check . returns exit code 0
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: 1) Add 'Vault path' section to SKILL.md before Push documenting OFFDESK_OBSIDIAN_VAULT. 2) Update Push step 3 with VAULT_ROOT expansion + trailing-slash strip. 3) Update Push step 7 + add explicit merge-frontmatter.py call site with $VAULT_ROOT. 4) Update Pull step 2 grep to $VAULT_ROOT. 5) Replace remaining ~/Obsidian/android paths in Cleanup + Slug-collision sections. 6) setup.md: swap laptop default to ~/Obsidian/offdesk in WebUI step + .stignore + add env var override note + document Android-path independence. 7) marketplace.json: drop 'phone/tablet'. 8) plugin.json version 0.1.0 → 0.2.0. 9) Run ruff check.

Commit: `987a52a` - task-5: support OFFDESK_OBSIDIAN_VAULT env var; default vault renamed to ~/Obsidian/offdesk

Implementation: Added 'Vault path' section to SKILL.md documenting the OFFDESK_OBSIDIAN_VAULT contract (default ~/Obsidian/offdesk, override via shell profile). Threaded VAULT_ROOT through Push step 3 (mkdir), Push step 7 (write target), the new explicit merge-frontmatter.py call site, Pull step 2 (grep), and the Cleanup / Slug-collision section path mentions. setup.md: laptop vault root swapped to ~/Obsidian/offdesk in the Syncthing Add Folder step and .stignore location, added the env-var override sentence, and documented that the Android-side path /storage/emulated/0/Obsidian/android/ is set independently of the laptop env var and should not be renamed to match. marketplace.json obsidian entry description drops 'on phone/tablet'. obsidian plugin.json version 0.1.0 -> 0.2.0 (minor bump per CLAUDE.md SemVer: broadened config surface, no breaking change since no v0.1.0 users). uv run ruff check . passes. task-reviewer agent verdict: APPROVED. Three 'phone/tablet' mentions remain in SKILL.md (frontmatter description, intro, Push step 7 narrative) by design — AC #8 narrows the rewording to marketplace.json; these are candidates for a follow-up task per the reviewer's non-blocking observation.
<!-- SECTION:NOTES:END -->
