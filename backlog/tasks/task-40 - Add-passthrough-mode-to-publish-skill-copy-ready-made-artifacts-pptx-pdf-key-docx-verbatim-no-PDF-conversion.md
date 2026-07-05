---
id: TASK-40
title: >-
  Add passthrough mode to publish skill: copy ready-made artifacts
  (pptx/pdf/key/docx) verbatim, no PDF conversion
status: To Do
assignee: []
created_date: '2026-07-05 15:40'
updated_date: '2026-07-05 18:05'
labels: []
dependencies: []
priority: medium
ordinal: 40000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

The `publish` skill currently accepts **only** markdown: step 2 of the push procedure hard-fails on any non-`.md` extension, and every push shells out to the `pdf` skill (`md-to-pdf.py`) to render MD → PDF before dropping the result on a transport provider. That means an already-final artifact — a `.pptx` deck, a `.pdf`, a Keynote `.key`, a `.docx` — cannot be published at all: there is nothing to render, only to copy. In practice a user who says "put this deck on gdrive" gets a hard-fail, and the assistant falls back to ad-hoc `rclone`/`cp` instead of the skill, defeating the point of having a transport skill.

Add a **passthrough mode**: when the source is a ready-made artifact, copy it verbatim into the same per-project provider folder the skill already computes, preserving the original extension — no PDF conversion. Markdown behavior is unchanged.

Transport is out of scope: the requesting user publishes to Google Drive via the **Google Drive for desktop local mount** (`~/Library/CloudStorage/GoogleDrive-*/My Drive`), which the skill already targets. Do NOT add rclone / headless upload — the existing mount-based transport and `providers.py` resolver are reused as-is.

## Scope

In scope:
- Rework the `publish` push procedure (`SKILL.md`) to branch on source extension instead of hard-failing:
  - `.md` → existing render branch (shell out to `pdf`/`md-to-pdf.py`, target `<slug>.pdf`). Unchanged.
  - ready-made artifact (at minimum `.pdf`, `.pptx`, `.key`, `.docx`; define the definitive allowlist in the skill) → **passthrough**: copy the file verbatim (`cp`) into `<provider-root>/Reading/<project-basename>/<basename.ext>`, preserving the original filename/extension. No conversion.
- Reuse the existing provider resolution unchanged (trigger → provider, env-var/glob root resolution via `providers.py`, per-project `Reading/<project>` subfolder, mount-only transport). Slug-collision handling applies to the passthrough basename the same way it applies to the markdown slug.
- Update the skill `description` (SKILL.md frontmatter), `plugins/publish/.claude-plugin/plugin.json` `description` + `version` (minor bump, e.g. 1.3.1 → 1.4.0), and the root `README.md` `### publish` section to state that markdown is rendered to PDF while ready-made artifacts are copied as-is.
- Update the "Out of scope" section of SKILL.md: remove/soften "No non-`.md` input" and keep the rclone/headless-upload exclusion intact.
- Update reference docs and marketing copy for parity where they assert markdown-only: `references/providers.md` (including the `<slug>.pdf` layout line), the root `README.md` `### publish` section (currently "Publish a markdown file … as a PDF" and "v1.3 ships three providers"), and any provider ref that repeats the `.md`-only contract.
- Add or extend a test asserting the passthrough contract (see AC) so the doc/behavior contract is regression-guarded.

Out of scope:
- **No rclone / headless upload.** The user has the Google Drive for desktop local mount; transport stays mount-based. Do not touch the transport mechanism or `providers.py` resolver logic.
- **No new provider.** icloud / google-drive / onedrive set is unchanged.
- **No annotation pull-back, no EPUB, no multi-file batching** — still out of scope, unchanged.
- **No change to the `pdf` skill** beyond what the markdown branch already calls; passthrough must not invoke it.

## Files

- `plugins/publish/skills/publish/SKILL.md` (exists) — push procedure steps 2/3/6/7, frontmatter `description`, "Out of scope" section.
- `plugins/publish/.claude-plugin/plugin.json` (exists) — `description` + `version` bump.
- `README.md` (exists) — root `### publish` section: currently asserts "Publish a markdown file … as a PDF" and "v1.3 ships three providers"; update the contract for passthrough and bump the version string to match plugin.json.
- `plugins/publish/skills/publish/references/providers.md` (exists) — markdown-only assertions to soften for passthrough (including the `<slug>.pdf` layout line).
- `plugins/publish/skills/publish/references/google-drive.md` (exists) — read-only context: confirms mount-only transport (no rclone) — do NOT add rclone here.
- `plugins/publish/skills/pdf/scripts/md-to-pdf.py` (exists) — read-only context: the renderer the markdown branch keeps calling; passthrough must NOT call it.
- `plugins/publish/skills/publish/tests/test_providers.py` (exists) — existing resolver test; extend here or add a sibling test file for the passthrough contract.

## Source

Source: /Users/paul/Private/Alfa/Projects/channels@1c2d983ebddf
Source context (read-only): this handoff originates from an interactive channels session where the user published `presentations/doc-2/output/channels-definition-arch.pptx` to Google Drive. The publish skill could not be used because it hard-fails on non-`.md`; the file was copied manually into the mount-equivalent `Reading/channels/` folder. This task closes that gap. No source file needs to be read to implement the task — the destination `publish` skill is self-contained.

## Before starting (destination Claude validation checklist)

Before running this task, verify:
1. All `(exists)` file paths in the Files section still exist in this repo.
2. Each AC is objectively pass/fail (a grep, test invocation, or visible behavior — not "works correctly").
3. All dependencies in the task's frontmatter are status=Done.
4. Out-of-scope items are not accidentally pulled in by ambiguous AC (especially: do NOT add rclone; do NOT alter the pdf renderer or providers.py resolver).

If anything is unclear or any check fails: STOP and ask the user. Do NOT start work blindly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 publish SKILL.md step 2 no longer hard-fails on non-.md input: the procedure branches on source extension, with an explicit passthrough branch for ready-made artifacts; the 'No non-.md input' line is removed/softened in Out of scope
- [ ] #2 For a .md source, behavior is unchanged: the skill still renders via the pdf skill (md-to-pdf.py) to <provider-root>/Reading/<project>/<slug>.pdf
- [ ] #3 For a ready-made artifact (.pdf/.pptx/.key/.docx per the skill allowlist), the skill copies the file verbatim (cp, no conversion) into <provider-root>/Reading/<project>/<basename.ext>, preserving the original extension, and does NOT invoke md-to-pdf.py
- [ ] #4 SKILL.md frontmatter description, plugins/publish/.claude-plugin/plugin.json description, AND the root README.md ### publish section all state markdown is rendered while ready-made artifacts are copied as-is; plugin.json version is bumped (minor, e.g. 1.4.0) and the README.md 'v1.3 ships' version string is updated to match
- [ ] #5 Transport is untouched: no rclone/headless-upload added anywhere, providers.py resolver logic and the icloud/google-drive/onedrive set are unchanged (git diff shows no logic change to providers.py); grep for 'rclone' in plugins/publish finds no new occurrence
- [ ] #6 The passthrough contract is regression-guarded by a doc-assertion test (e.g. an assertion that publish/SKILL.md contains the non-.md passthrough allowlist and no longer hard-fails on non-.md) rather than by adding logic to providers.py; uv run pytest passes and uv run ruff check . is clean
<!-- AC:END -->
