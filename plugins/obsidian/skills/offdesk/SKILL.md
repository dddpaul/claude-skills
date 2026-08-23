---
name: offdesk
description: Copy markdown from any project into an Obsidian vault on a phone or tablet — carried by Syncthing (default) or iCloud — then pull annotated `>[!ai]` callouts back to source. Push triggers (EN) "send to offdesk", "send to phone for review", "review later", "check later"; push triggers (RU) "положи это в offdesk", "положи это в оффдеск", "посмотрю позже", "проверю позже". iCloud push triggers (EN) "send to offdesk icloud", "offdesk icloud", "offdesk on icloud"; iCloud push triggers (RU) "положи в offdesk icloud", "положи в оффдеск айклауд", "оффдеск айклауд". Pull triggers (EN) "review my offdesk notes", "check offdesk feedback"; pull triggers (RU) "посмотри оффдеск фидбэк", "проверь оффдеск"; add "icloud"/"айклауд" or "syncthing"/"синктинг" to a pull phrase to scan one vault instead of both.
---

# Offdesk

User-level skill that copies markdown from any project into an Obsidian
vault on a phone or tablet for off-desk reading, then pulls annotated
`>[!ai]` callouts back to the source project.

Two transports carry the vault: **Syncthing** (P2P, the default) and
**iCloud** (an Obsidian vault in iCloud Drive, for iPad). They differ only
in which directory the vault root is; layout, frontmatter, annotation
convention, and pull semantics are identical across both.

The skill performs file copy, frontmatter merge, and grep directly — no
compiled CLI tool. Routing and root-resolution rules are pinned in
[scripts/transports.py](scripts/transports.py) so they stay testable;
[references/transports.md](references/transports.md) is the prose version.
Manual user-setup steps (Syncthing, Obsidian on Android/iOS, templates,
toolbar) are documented in [references/setup.md](references/setup.md).

## Transports

| Transport | Env var | Default root |
|---|---|---|
| `syncthing` (default) | `OFFDESK_SYNCTHING_VAULT` | `~/Obsidian/offdesk` |
| `icloud` | `OFFDESK_ICLOUD_VAULT` | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/*` (glob) |

Resolution per transport, first match wins:

- `syncthing`: `OFFDESK_SYNCTHING_VAULT` → `OFFDESK_OBSIDIAN_VAULT` →
  `~/Obsidian/offdesk`. `OFFDESK_OBSIDIAN_VAULT` is the pre-transport name
  of the same knob and stays fully supported — not deprecated.
- `icloud`: `OFFDESK_ICLOUD_VAULT` → expand the glob. The vault directory
  is named by the user when the vault is created in Obsidian on iOS, so
  the default cannot be a literal path. Exactly one matching directory is
  used; **0 matches → stop** with a message naming `OFFDESK_ICLOUD_VAULT`;
  **more than 1 → stop** and list every candidate. Never auto-pick — a
  guess writes notes into the wrong vault.

The env var, when set, wins verbatim (trailing slash stripped) and the
glob is not consulted.

```bash
# syncthing
VAULT_ROOT="${OFFDESK_SYNCTHING_VAULT:-${OFFDESK_OBSIDIAN_VAULT:-$HOME/Obsidian/offdesk}}"
VAULT_ROOT="${VAULT_ROOT%/}"   # strip trailing slash for consistency
```

```sh
# icloud — no shell arrays and no bare glob: the snippet must behave
# identically under sh, bash and zsh (macOS default), where array indexing
# and unmatched-glob handling all differ.
VAULT_ROOT="${OFFDESK_ICLOUD_VAULT%/}"
if [ -z "$VAULT_ROOT" ]; then
    container="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"
    # -maxdepth 1: one level of the Obsidian container, not a tree walk.
    # ! -name '.*': skip .Trash and friends, matching the resolver's glob.
    matches=$(find "$container" -mindepth 1 -maxdepth 1 -type d \
        ! -name '.*' 2>/dev/null | sort)
    count=$(printf '%s\n' "$matches" | sed '/^$/d' | wc -l | tr -d ' ')
    if [ "$count" -eq 1 ]; then
        VAULT_ROOT="$matches"
    elif [ "$count" -eq 0 ]; then
        echo "offdesk: no Obsidian iCloud vault under $container;" >&2
        echo "  set OFFDESK_ICLOUD_VAULT to the vault root" >&2
        exit 1
    else
        echo "offdesk: $count vaults matched; set OFFDESK_ICLOUD_VAULT to one of:" >&2
        printf '  %s\n' "$matches" >&2
        exit 1
    fi
fi
```

On either failure, report it to the user and stop — never continue with an
empty `VAULT_ROOT`, and never fall back to another transport.

## Push

Push targets **exactly one** transport. Trigger phrases:

- `syncthing` (default) — EN: "send to offdesk", "send to phone for
  review", "review later", "check later"; RU: "положи это в offdesk",
  "положи это в оффдеск", "посмотрю позже", "проверю позже"
- `icloud` — EN: "send to offdesk icloud", "offdesk icloud", "offdesk on
  icloud"; RU: "положи в offdesk icloud", "положи в оффдеск айклауд",
  "оффдеск айклауд"

A push phrase that names no transport routes to `syncthing`; `icloud` is
opt-in per push and always explicitly marked, by an exact trigger or by
the word "icloud"/"айклауд" in the phrase.

Procedure:

1. **Identify the transport** from the matched trigger phrase (default
   `syncthing`).
2. **Resolve project root.** Run `git rev-parse --show-toplevel`; if the
   command fails (not a git repo), fall back to `pwd`.
3. **Project slug** = `basename "$PROJECT_ROOT"`.
4. **Resolve the vault root** for the transport (see [Transports](#transports))
   and create the vault subdir on the laptop:
   ```bash
   mkdir -p "$VAULT_ROOT/<slug>/"
   ```
5. **Read the source markdown** and parse any existing YAML frontmatter (the
   leading `---` block, if present).
6. **Merge** the following keys into the existing frontmatter — do NOT prepend
   a second `---` block, that would break YAML. If the source file has no
   frontmatter, create one. If it does, add/update these keys in place:
   - `offdesk-source`: relative path from project root to the source file.
   - `offdesk-project-root`: absolute path to the project root.
   - `offdesk-copied-at`: ISO 8601 UTC timestamp (e.g., `2026-06-14T08:30:00Z`).
   - `offdesk-transport`: `syncthing` or `icloud` — which vault this copy
     was written to, so the copy stays self-describing if a vault moves.
7. **Keep all existing frontmatter keys untouched** — confluence-* keys from
   upmark, jekyll/hugo fields, anything else. Merge, do not replace.
8. **Write** the merged document to:
   ```text
   $VAULT_ROOT/<slug>/<filename>.md
   ```
   The layout is identical for both transports. Syncthing propagates to the
   phone/tablet automatically; iCloud propagates when the Mac and the iPad
   next sync.

For the YAML merge, the inline shell + python is acceptable when small;
otherwise call the helper at
[scripts/merge-frontmatter.py](scripts/merge-frontmatter.py):

```bash
scripts/merge-frontmatter.py \
    --src "<source.md>" \
    --dst "$VAULT_ROOT/<slug>/<filename>.md" \
    --offdesk-source "<rel-path>" \
    --offdesk-project-root "$PROJECT_ROOT" \
    --offdesk-transport icloud
```

`--offdesk-transport` defaults to `syncthing` when omitted.

## Pull

Pull scans **both vaults by default** — an annotation is made away from the
desk, and remembering which device it was left on is exactly the friction
this skill removes. Trigger phrases:

- both transports — EN: "review my offdesk notes", "check offdesk
  feedback"; RU: "посмотри оффдеск фидбэк", "проверь оффдеск"
- `icloud` only — EN: "check offdesk icloud", "review my offdesk icloud
  notes"; RU: "проверь оффдеск айклауд", "посмотри оффдеск айклауд фидбэк"
- `syncthing` only — EN: "check offdesk syncthing", "review my offdesk
  syncthing notes"; RU: "проверь оффдеск синктинг", "посмотри оффдеск
  синктинг фидбэк"

Procedure:

1. **Project slug** from `cwd` / `git rev-parse --show-toplevel` (same as
   push steps 2+3).
2. **Determine the scan scope** from the phrase: both transports unless it
   names one.
3. **For each transport in scope**, resolve its vault root and grep for AI
   callouts over the per-project vault subdir. A transport whose root fails
   to resolve is reported and skipped — the other transport is still
   scanned.
   ```bash
   grep -nrE '^>\s*\[!ai\]' "$VAULT_ROOT/<slug>/"
   ```
   The regex `^>\s*\[!ai\]` matches both `>[!ai]` and `> [!ai]` (no-space
   and with-space) — both forms render correctly in Obsidian. Keep the
   search pinned to `<vault-root>/<slug>/`: a `find` across a whole iCloud
   tree was measured at over two minutes.
4. **For each hit**, parse the file's YAML frontmatter to extract:
   - `offdesk-source` → the relative path back into the source project.
   - `offdesk-project-root` → the absolute project root for source-back
     mapping.
   and read the vault file's modification time
   (`stat -f '%Sm' -t '%Y-%m-%dT%H:%M' "<vault-file>"` on macOS).
5. **Merge the results and report** them grouped by source file, each line
   tagged with its transport and the file's mtime as an age:
   ```text
   [icloud, 2h ago]     design/foo.md:42 — is this still true after the split?
   [syncthing, 3d ago]  design/bar.md:17 — check the numbers here
   ```
   The mtime answers "has the vault propagated yet, or did I come back too
   early". The same source file annotated in both vaults yields **two
   independent annotation sets, not duplicates** — they were written on
   different devices. Show both; do not deduplicate.
6. **On zero annotations, check for unmaterialized iCloud files** before
   reporting "no feedback". An evicted iCloud file is normally a dataless
   file under its own name and an ordinary read materializes it, so grep
   just works (it may block while downloading). The one silent-miss case is
   a legacy `.<name>.md.icloud` stub, where the file is absent under its own
   name and grep reports nothing:
   ```sh
   find "$VAULT_ROOT/<slug>/" -name '*.icloud'
   ```
   If stubs are found, report the unmaterialized files (and that
   `brctl download "<path>"` will fetch them) instead of "no feedback".
   Skip this check entirely when annotations were found, and for the
   `syncthing` vault, which has no dataless files.
7. **Confirm before modifying the source file.** If the user wants Claude to
   apply changes (e.g., per a `>[!fix]` callout, or "apply that suggestion"),
   prompt for confirmation before editing the source. Never auto-apply.

## Cleanup

If the source markdown is also pushed elsewhere (for example, back to
Confluence via `upmark push`), strip the offdesk-only state from the
document **before** the upstream push:

- Remove all `offdesk-*` keys from the frontmatter (`offdesk-source`,
  `offdesk-project-root`, `offdesk-copied-at`, `offdesk-transport`, and any
  future `offdesk-*` additions).
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

The rule is per-vault and identical for both transports — the same project
maps to the same slug in either vault.

## Annotation convention

- `>[!ai] question for Claude` — Obsidian block-level callout. Claude
  addresses these on pull.
- `>[!todo] reminder for the user` — Claude ignores. Grep pattern
  `^>\s*\[!todo\]` is for the user, not Claude.
- **Multi-line callouts:** each subsequent line also starts with `>`.
  Obsidian on Android auto-inserts `>` on Enter inside an existing callout;
  on iOS, hold the callout line and continue.
- Both `>[!ai]` and `> [!ai]` (no-space and with-space) render correctly
  in Obsidian. The grep regex `^>\s*\[!ai\]` handles both forms.

## Not this skill

Device-named phrases — "read on ipad", "почитаю на айпаде", "send to
books", "положи это в книги" — belong to the [[publish]] skill's `icloud`
provider, which renders markdown to PDF and is push-only. offdesk phrases
are anchored on "offdesk"/"оффдеск" and never name a device, so the two
skills stay unambiguous. Use offdesk when you want the verbatim `.md` in
an Obsidian vault with annotations coming back.

## Setup

One-time per-user manual setup — Syncthing on macOS and Android, Obsidian
on Android, an Obsidian vault in iCloud Drive on iOS, the Templates plugin
with two template files, and toolbar bindings — is documented in
[references/setup.md](references/setup.md). The skill code itself does
not automate any of these steps.
