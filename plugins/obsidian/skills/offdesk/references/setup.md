# Offdesk — manual setup

One-time per-user setup. The `offdesk` skill does not automate any of these
steps — run them once per transport, and the skill takes over from there.

Set up only the transports you use: the Syncthing sections cover the
laptop ↔ Android P2P vault, the iCloud section covers an Obsidian vault in
iCloud Drive for iPad. See [[transports]] for how each vault root is
resolved.

## Syncthing — macOS setup

Install and start Syncthing:

```bash
brew install syncthing
brew services start syncthing
```

Open the Syncthing WebUI at <http://127.0.0.1:8384>. Click **Add Folder** and
set:

- **Folder Label:** `offdesk-android` (legacy name; can stay or be renamed to
  `offdesk` — the skill doesn't care).
- **Folder ID:** `offdesk-android` (same — folder ID can stay or be renamed).
- **Folder Path:** the laptop vault root

Vault root on laptop (default):

```text
~/Obsidian/offdesk
```

If your Obsidian layout uses a different directory, override the default by
setting `OFFDESK_SYNCTHING_VAULT` in your shell profile (`~/.zshrc` or
`~/.bashrc`) and point it at whichever directory Syncthing shares — the
skill reads the env var at every push/pull. `OFFDESK_OBSIDIAN_VAULT` is the
older name of the same setting and still works: if it is already in your
profile there is nothing to change, and nothing to un-set.

## Syncthing — Android setup

- Install **Syncthing** on Android from F-Droid (the cleanest channel — the
  Play Store build is no longer maintained).
- Pair devices: scan the QR code from the laptop WebUI on Android, then
  accept the connection request on the laptop side. Accept the shared folder
  on Android.
- Install **Obsidian** on Android from the Play Store. Open the synced folder
  as a vault.

Android-side vault path:

```text
/storage/emulated/0/Obsidian/android/
```

This Android path is the Syncthing folder mapping on the device, set
independently of the laptop-side env var. Leave it as-is — do not try to
rename it to match the laptop default.

## iCloud — iPad setup

The iCloud transport needs no sync daemon and no pairing: Obsidian on iOS
can keep a vault in iCloud Drive, and macOS mounts the same vault locally.

On the iPad:

- Install **Obsidian** from the App Store.
- On the vault picker, choose **Create new vault**, give it a name (for
  example `offdesk`), and turn **Store in iCloud** on. An existing local
  vault cannot be switched to iCloud in place — create an iCloud vault and
  move the notes into it.

The vault then appears on the Mac under Obsidian's iCloud container, with
the vault name you chose as the last path component:

```text
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/<vault-name>
```

The skill finds it by expanding
`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/*` and using the
single matching directory. If you keep more than one Obsidian iCloud vault
— or none, because the vault has not synced to the Mac yet — the skill
stops and asks you to name the vault explicitly. Set it in your shell
profile:

```bash
export OFFDESK_ICLOUD_VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/offdesk"
```

The skill reads the env var at every push/pull; restart the shell after
editing the profile.

Two iCloud notes worth knowing:

- **Files can be evicted.** With `optimize-storage` enabled (check with
  `defaults read com.apple.bird optimize-storage`), macOS may drop the
  local copy of a file that has not been used. Reading such a file
  materializes it transparently, so the skill's grep still works — it may
  simply pause while downloading.
- **Legacy `.icloud` stubs.** An older eviction form replaces the file with
  a `.<name>.md.icloud` placeholder, and a grep over the folder finds
  nothing. The skill checks for these only when a pull returns zero
  annotations; `brctl download "<path>"` fetches them.

## Obsidian — Templates plugin + toolbar

Do this in the vault you review in — the Syncthing vault on Android, the
iCloud vault on iPad, or both. Enable the built-in **Templates** plugin
(Settings → Core plugins → Templates).

Create two template files in the vault:

```text
_templates/ai-callout.md
```

Content: `>[!ai] ` (one trailing space; the cursor lands after `] ` when the
template is inserted).

```text
_templates/todo-callout.md
```

Content: `>[!todo] ` (one trailing space).

Bind both to the bottom toolbar so they're one tap away while reading:

- Settings → **Mobile** → **Manage toolbar options**.
- Add an entry for each template, mapped to the "Insert template" command
  with the corresponding template file.

## .stignore

Syncthing only — the iCloud vault needs no ignore file. Place a `.stignore`
file at the Syncthing vault root on the laptop:

```text
~/Obsidian/offdesk/.stignore
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

These patterns keep Obsidian's per-device workspace state, macOS metadata,
editor swap files, and Syncthing's own conflict markers from bouncing
back-and-forth across the sync link.
