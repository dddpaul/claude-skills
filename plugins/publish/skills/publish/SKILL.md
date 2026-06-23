---
name: publish
description: Publish a markdown file from the active project as a PDF to a configured transport provider (v1.3 ships icloud + google-drive + onedrive). Push-only — no read-back. Triggers (EN) "send to books", "read on ipad", "review on books", "send to icloud", "send to gdrive", "send to google drive", "read on gdrive", "read on drive", "send to onedrive", "send to one drive", "read on onedrive"; triggers (RU) "положи это в books", "положи это в книги", "почитаю на айпаде", "положи в icloud", "положи в gdrive", "положи в гугл драйв", "отправь на драйв", "положи в onedrive", "положи в ванндрайв", "отправь на onedrive".
---

# publish

Umbrella push skill. Converts a markdown file in the active project to a PDF
via the sibling [[pdf]] skill, then drops it under a per-project subfolder on
a configured transport provider. v1.3 ships three providers: `icloud`,
`google-drive`, and `onedrive`.

The skill is **push-only**: any annotations the human makes (Apple Pencil on
iPad, etc.) stay with the human, not with Claude. There is no pull-back.

## Triggers

The trigger phrases below name the *consumer experience* but route to the
underlying *transport provider*. Each trigger maps to exactly one provider —
see [[providers]] for the full mapping.

`icloud` triggers:

- EN: "send to books", "read on ipad", "review on books", "send to icloud"
- RU: "положи это в books", "положи это в книги", "почитаю на айпаде", "положи в icloud"

`google-drive` triggers:

- EN: "send to gdrive", "send to google drive", "read on gdrive", "read on drive"
- RU: "положи в gdrive", "положи в гугл драйв", "отправь на драйв"

`onedrive` triggers:

- EN: "send to onedrive", "send to one drive", "read on onedrive"
- RU: "положи в onedrive", "положи в ванндрайв", "отправь на onedrive"

If the user says something generic like "publish this" or "отправь это" with no
provider implied, **ask** which provider before proceeding. Do not silently
default to any provider.

## Push procedure

1. **Identify the provider** from the matched trigger phrase. Each trigger
   maps to exactly one provider (see [[providers]]). If no specific provider
   matched, ask the user, then proceed.
2. **Resolve the source path.** Take the absolute path of the source
   markdown file. **Hard-fail if the extension is not `.md`** — this skill
   ships markdown only.
3. **Compute the slug** = `Path(source).stem`. On collision in the target
   subfolder, append `-<sha1(absolute_source_path)[:6]>` so the same source
   always maps to the same slug.
4. **Resolve the project root** via `git rev-parse --show-toplevel`. If the
   command fails (not a git repo), fall back to `dirname(source)`. The
   `basename` of the project root becomes the per-project subfolder name.
5. **Resolve the provider root.** Read the provider's env var from
   [[providers]] (e.g. `PUBLISH_ICLOUD_DIR` for `icloud`,
   `PUBLISH_GOOGLE_DRIVE_DIR` for `google-drive`,
   `PUBLISH_ONEDRIVE_DIR` for `onedrive`). If the env var is set,
   use it verbatim. Otherwise:
   - `icloud`: fall back to the literal default root.
   - `google-drive`: expand the default-root glob; 0 or >1 matches → hard
     fail with a message naming `PUBLISH_GOOGLE_DRIVE_DIR` as the env var
     to set. Never auto-pick on multi-account. See [[google-drive]].
   - `onedrive`: expand the default-root glob
     (`~/Library/CloudStorage/OneDrive-*`); 0 or >1 matches → hard fail
     with a message naming `PUBLISH_ONEDRIVE_DIR` as the env var to set.
     Personal mounts as `OneDrive-Personal`; Work/School mounts as
     `OneDrive-<Org>`. Never auto-pick on multi-account.
6. **Ensure the per-project subfolder exists.** Layout is symmetric across
   providers:

   ```text
   <provider-root>/Reading/<project-basename>/<slug>.pdf
   ```

   ```bash
   mkdir -p "<provider-root>/Reading/<project-basename>"
   ```

7. **Shell out to the [[pdf]] skill** with the source and the final target
   path:

   ```bash
   uv run plugins/publish/skills/pdf/scripts/md-to-pdf.py \
       "<source.md>" \
       "<provider-root>/Reading/<project-basename>/<slug>.pdf"
   ```

8. **Report the final path** so the user can open it on the target device
   (e.g. on iPad: tap-to-open in Files.app → Open in Books; on Google
   Drive: opens via Drive on any signed-in device).

## Providers

See [[providers]] for the table of supported providers, their env vars, and
default roots. v1.3 ships `icloud`, `google-drive`, and `onedrive`;
provider-specific transport notes live in dedicated reference files
([[icloud]], [[google-drive]], [[onedrive]]).

## Out of scope (v1.3)

- **No pull triggers, no annotation extraction.** Pen marks stay with the
  human.
- **No EPUB output.** Apple Books pen annotations don't work on EPUB.
- **No non-`.md` input.** PDF, EPUB, anything-else are out of scope.
- **No multi-file batching.** One file per push.
- **No auto-cleanup** of old PDFs in the provider folder.
- **No fallback to the legacy v0.x env var.** Clean break in v1; if the
  pre-rename env var was set on your machine, set `PUBLISH_ICLOUD_DIR`
  instead.
- **No rclone / headless Google Drive upload** — mount-only via Google
  Drive for desktop. See [[google-drive]].
- **No multi-account auto-pick for `google-drive`** — when the glob matches
  more than one `GoogleDrive-*` directory, the skill hard-fails and asks
  for `PUBLISH_GOOGLE_DRIVE_DIR`.
- **No multi-account auto-pick for `onedrive`** — when the glob matches
  more than one `OneDrive-*` directory (e.g. Personal alongside Work),
  the skill hard-fails and asks for `PUBLISH_ONEDRIVE_DIR`.
- **No AirDrop or email providers** — separate backlog tasks.
