---
name: publish
description: Publish a file from the active project to a configured transport provider (v1.4 ships icloud + google-drive + onedrive): markdown is rendered to PDF, while ready-made artifacts (.pdf/.pptx/.key/.docx) are copied verbatim (passthrough, no conversion). Push-only — no read-back. Triggers (EN) "send to books", "read on ipad", "review on books", "send to icloud", "send to gdrive", "send to google drive", "read on gdrive", "read on drive", "send to onedrive", "send to one drive", "read on onedrive"; triggers (RU) "положи это в books", "положи это в книги", "почитаю на айпаде", "положи в icloud", "положи в gdrive", "положи в гугл драйв", "отправь на драйв", "положи в onedrive", "положи в ванндрайв", "отправь на onedrive".
---

# publish

Umbrella push skill. A markdown source is rendered to a PDF via the sibling
[[pdf]] skill; a ready-made artifact (`.pdf`, `.pptx`, `.key`, `.docx`) is
copied verbatim (passthrough — no conversion). Either way the result is
dropped under a per-project subfolder on a configured transport provider.
v1.4 ships three providers: `icloud`, `google-drive`, and `onedrive`.

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
2. **Resolve the source path and select the mode** from the source
   extension (case-insensitive):
   - `.md` → **render mode**: the markdown is rendered to PDF via the
     [[pdf]] skill (step 7 render branch).
   - `.pdf`, `.pptx`, `.key`, `.docx` (the ready-made-artifact allowlist)
     → **passthrough mode**: the file is copied verbatim, no conversion
     (step 7 passthrough branch).
   - Any other extension → **hard-fail**, naming the `.md` render path and
     the passthrough allowlist.
3. **Compute the target basename.** In render mode it is `<slug>.pdf` where
   `slug = Path(source).stem`; in passthrough mode it is `Path(source).name`
   — the original filename and extension, preserved verbatim. On collision
   in the target subfolder, append `-<sha1(absolute_source_path)[:6]>` to the
   stem (before the extension) so the same source always maps to the same
   target name.
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
   providers; the target basename depends on the mode (step 3):

   ```text
   <provider-root>/Reading/<project-basename>/<slug>.pdf       # render mode (.md)
   <provider-root>/Reading/<project-basename>/<original-name>  # passthrough (.pdf/.pptx/.key/.docx)
   ```

   ```bash
   mkdir -p "<provider-root>/Reading/<project-basename>"
   ```

7. **Produce the target file** — branch on the mode from step 2:
   - **Render mode (`.md`):** shell out to the [[pdf]] skill with the
     source and the final target path:

     ```bash
     uv run plugins/publish/skills/pdf/scripts/md-to-pdf.py \
         "<source.md>" \
         "<provider-root>/Reading/<project-basename>/<slug>.pdf"
     ```
   - **Passthrough mode (ready-made artifact):** copy the file verbatim —
     do **not** invoke `md-to-pdf.py` or any other converter:

     ```bash
     cp "<source.ext>" \
        "<provider-root>/Reading/<project-basename>/<original-name>"
     ```

8. **Report the final path** so the user can open it on the target device
   (e.g. on iPad: tap-to-open in Files.app → Open in Books; on Google
   Drive: opens via Drive on any signed-in device).

## Providers

See [[providers]] for the table of supported providers, their env vars, and
default roots. v1.4 ships `icloud`, `google-drive`, and `onedrive`;
provider-specific transport notes live in dedicated reference files
([[icloud]], [[google-drive]], [[onedrive]]).

## Out of scope (v1.4)

- **No pull triggers, no annotation extraction.** Pen marks stay with the
  human.
- **No EPUB output.** Apple Books pen annotations don't work on EPUB.
- **No arbitrary input.** Passthrough accepts only the ready-made-artifact
  allowlist (`.pdf`, `.pptx`, `.key`, `.docx`); markdown is rendered to PDF.
  Any other extension still hard-fails.
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
