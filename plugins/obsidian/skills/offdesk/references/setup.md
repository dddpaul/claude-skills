# Offdesk — manual setup

One-time per-user setup. The `offdesk` skill does not automate any of these
steps — run them once on your laptop and Android device, and the skill takes
over from there.

## macOS setup

Install and start Syncthing:

```bash
brew install syncthing
brew services start syncthing
```

Open the Syncthing WebUI at <http://127.0.0.1:8384>. Click **Add Folder** and
set:

- **Folder Label:** `offdesk-android`
- **Folder ID:** `offdesk-android`
- **Folder Path:** the laptop vault root

Vault root on laptop:

```text
~/Obsidian/android
```

## Android setup

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

## Obsidian Android — Templates plugin + toolbar

Enable the built-in **Templates** plugin (Settings → Core plugins →
Templates).

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

Place a `.stignore` file at the vault root on the laptop:

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

These patterns keep Obsidian's per-device workspace state, macOS metadata,
editor swap files, and Syncthing's own conflict markers from bouncing
back-and-forth across the sync link.
