---
name: publish
description: Publish a markdown file from the active project as a PDF to a configured transport provider (v1 ships icloud only). Push-only — no read-back. Triggers (EN) "send to books", "read on ipad", "review on books", "send to icloud"; triggers (RU) "положи это в books", "положи это в книги", "почитаю на айпаде", "положи в icloud".
---

# publish

Umbrella push skill. Converts a markdown file in the active project to a PDF
via the sibling [[pdf]] skill, then drops it under a per-project subfolder on
a configured transport provider. v1 ships only the `icloud` provider.

The skill is **push-only**: any annotations the human makes (Apple Pencil on
iPad, etc.) stay with the human, not with Claude. There is no pull-back.

## Triggers

The trigger phrases below name the *consumer experience* but route to the
underlying *transport provider*. v1 routes every one of these eight phrases
to the `icloud` provider — see [[providers]].

- EN: "send to books", "read on ipad", "review on books", "send to icloud"
- RU: "положи это в books", "положи это в книги", "почитаю на айпаде", "положи в icloud"

If the user says something generic like "publish this" or "отправь это" with no
provider implied, **ask** which provider before proceeding. Do not silently
default to `icloud`.

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
   [[providers]] (e.g. `PUBLISH_ICLOUD_DIR` for `icloud`); fall back to the
   provider's default root if the env var is unset.
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
   (e.g. on iPad: tap-to-open in Files.app → Open in Books).

## Providers

See [[providers]] for the table of supported providers, their env vars, and
default roots. v1 ships only `icloud`; provider-specific transport notes
live in dedicated reference files (e.g. [[icloud]]).

## Out of scope (v1)

- **No pull triggers, no annotation extraction.** Pen marks stay with the
  human.
- **No EPUB output.** Apple Books pen annotations don't work on EPUB.
- **No non-`.md` input.** PDF, EPUB, anything-else are out of scope.
- **No multi-file batching.** One file per push.
- **No auto-cleanup** of old PDFs in the provider folder.
- **No fallback to the legacy v0.x env var.** Clean break in v1; if the
  pre-rename env var was set on your machine, set `PUBLISH_ICLOUD_DIR`
  instead.
- **No non-icloud providers in v1** (e.g. OneDrive, Google Drive, AirDrop,
  email). Adding a new provider is its own backlog task.
