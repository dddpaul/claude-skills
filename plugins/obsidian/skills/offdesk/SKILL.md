---
name: offdesk
description: Copy markdown from any project into a Syncthing-synced Obsidian vault on phone/tablet, then pull annotated `>[!ai]` callouts back to source. Push triggers (EN) "send to offdesk", "send to phone for review", "review later", "check later"; push triggers (RU) "положи это в offdesk", "положи это в оффдеск", "посмотрю позже", "проверю позже". Pull triggers (EN) "review my offdesk notes", "check offdesk feedback"; pull triggers (RU) "посмотри оффдеск фидбэк", "проверь оффдеск".
---

# Offdesk

User-level skill that copies markdown from any project into a Syncthing-synced
Obsidian vault on a phone/tablet for off-desk reading, then pulls annotated
`>[!ai]` callouts back to the source project.

The skill performs file copy, frontmatter merge, and grep directly — no
compiled CLI tool. Manual user-setup steps (Syncthing, Obsidian Android,
templates, toolbar) are documented in [references/setup.md](references/setup.md).

## Vault path

Default vault root on the laptop:

```text
~/Obsidian/offdesk/
```

Override: set `OFFDESK_OBSIDIAN_VAULT` in your shell profile (`~/.zshrc`
or `~/.bashrc`) to point at any directory. The skill reads it at every
invocation; restart the shell after editing.

Every push/pull step that touches the vault resolves the root with:

```bash
VAULT_ROOT="${OFFDESK_OBSIDIAN_VAULT:-$HOME/Obsidian/offdesk}"
VAULT_ROOT="${VAULT_ROOT%/}"   # strip trailing slash for consistency
```

## Push

Trigger phrases (any of):

- EN: "send to offdesk", "send to phone for review", "review later", "check later"
- RU: "положи это в offdesk", "положи это в оффдеск", "посмотрю позже", "проверю позже"

Procedure:

1. **Resolve project root.** Run `git rev-parse --show-toplevel`; if the
   command fails (not a git repo), fall back to `pwd`.
2. **Project slug** = `basename "$PROJECT_ROOT"`.
3. **Create the vault subdir** on the laptop:
   ```bash
   VAULT_ROOT="${OFFDESK_OBSIDIAN_VAULT:-$HOME/Obsidian/offdesk}"
   VAULT_ROOT="${VAULT_ROOT%/}"   # strip trailing slash for consistency
   mkdir -p "$VAULT_ROOT/<slug>/"
   ```
4. **Read the source markdown** and parse any existing YAML frontmatter (the
   leading `---` block, if present).
5. **Merge** the following keys into the existing frontmatter — do NOT prepend
   a second `---` block, that would break YAML. If the source file has no
   frontmatter, create one. If it does, add/update these keys in place:
   - `offdesk-source`: relative path from project root to the source file.
   - `offdesk-project-root`: absolute path to the project root.
   - `offdesk-copied-at`: ISO 8601 UTC timestamp (e.g., `2026-06-14T08:30:00Z`).
6. **Keep all existing frontmatter keys untouched** — confluence-* keys from
   upmark, jekyll/hugo fields, anything else. Merge, do not replace.
7. **Write** the merged document to:
   ```text
   $VAULT_ROOT/<slug>/<filename>.md
   ```
   Syncthing propagates to the phone/tablet automatically.

For the YAML merge, the inline shell + python is acceptable when small;
otherwise call the helper at
[scripts/merge-frontmatter.py](scripts/merge-frontmatter.py):

```bash
scripts/merge-frontmatter.py \
    --src "<source.md>" \
    --dst "$VAULT_ROOT/<slug>/<filename>.md" \
    --offdesk-source "<rel-path>" \
    --offdesk-project-root "$PROJECT_ROOT"
```

## Pull

Trigger phrases (any of):

- EN: "review my offdesk notes", "check offdesk feedback"
- RU: "посмотри оффдеск фидбэк", "проверь оффдеск"

Procedure:

1. **Project slug** from `cwd` / `git rev-parse --show-toplevel` (same as
   push step 1+2).
2. **Grep** for AI callouts over the per-project vault subdir:
   ```bash
   VAULT_ROOT="${OFFDESK_OBSIDIAN_VAULT:-$HOME/Obsidian/offdesk}"
   VAULT_ROOT="${VAULT_ROOT%/}"
   grep -nrE '^>\s*\[!ai\]' "$VAULT_ROOT/<slug>/"
   ```
   The regex `^>\s*\[!ai\]` matches both `>[!ai]` and `> [!ai]` (no-space
   and with-space) — both forms render correctly in Obsidian.
3. **For each hit**, parse the file's YAML frontmatter to extract:
   - `offdesk-source` → the relative path back into the source project.
   - `offdesk-project-root` → the absolute project root for source-back
     mapping.
4. **Report findings** to the user in the format:
   ```text
   <source-file>:<line> — <callout content>
   ```
   where `<source-file>` is the resolved path inside the originating project.
5. **Confirm before modifying the source file.** If the user wants Claude to
   apply changes (e.g., per a `>[!fix]` callout, or "apply that suggestion"),
   prompt for confirmation before editing the source. Never auto-apply.

## Cleanup

If the source markdown is also pushed elsewhere (for example, back to
Confluence via `upmark push`), strip the offdesk-only state from the
document **before** the upstream push:

- Remove all `offdesk-*` keys from the frontmatter (`offdesk-source`,
  `offdesk-project-root`, `offdesk-copied-at`, and any future `offdesk-*`
  additions).
- Remove `>[!ai]` callouts from the body. Multi-line callouts are detected
  by leading `>` on each continuation line — strip the entire block.

The vault copies under `$VAULT_ROOT/<slug>/` keep their annotations
as review history; only the upstream-bound copy is cleaned.

## Slug collision

Two projects with identical basenames (e.g., `~/work/foo` and
`~/play/foo`) would collide in `$VAULT_ROOT/foo/`. Resolution:
suffix the slug with a short hash of the project root path when a
collision is detected.

Example: `foo` and `foo-a1b2c3` (where `a1b2c3` is the first 6 hex chars
of a hash of the absolute project root). Use a stable hash (e.g.,
`sha1`) so the same project always maps to the same slug.

## Annotation convention

- `>[!ai] question for Claude` — Obsidian block-level callout. Claude
  addresses these on pull.
- `>[!todo] reminder for the user` — Claude ignores. Grep pattern
  `^>\s*\[!todo\]` is for the user, not Claude.
- **Multi-line callouts:** each subsequent line also starts with `>`.
  Obsidian Android auto-inserts `>` on Enter inside an existing callout.
- Both `>[!ai]` and `> [!ai]` (no-space and with-space) render correctly
  in Obsidian. The grep regex `^>\s*\[!ai\]` handles both forms.

## Setup

One-time per-user manual setup — Syncthing on macOS, Syncthing on
Android via F-Droid, Obsidian on Android, the Templates plugin with two
template files, and toolbar bindings — is documented in
[references/setup.md](references/setup.md). The skill code itself does
not automate any of these steps.
