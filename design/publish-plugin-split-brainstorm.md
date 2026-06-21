# Publish Plugin Split

## Architecture decision

Split the current `reading` plugin's single `books` skill into two cohabiting
skills under a renamed plugin `publish`:

- **`pdf`** — standalone MD → PDF conversion. Callable directly when the user
  just wants a local PDF and no upload.
- **`publish`** — umbrella skill that converts MD → PDF (by shelling out to
  the `pdf` skill's script) and atomically writes the PDF to a cloud-mount
  target. Providers are declared as config blocks in
  `references/providers.md`; per-provider deep dives live in
  `references/<provider>.md`.

Providers are named by **transport**, not by consumer device. v1 ships two:

| Provider       | Env var                    | Default root                                                  |
|----------------|----------------------------|---------------------------------------------------------------|
| `icloud`       | `PUBLISH_ICLOUD_DIR`       | `~/Library/Mobile Documents/com~apple~CloudDocs/Reading`       |
| `google-drive` | `PUBLISH_GOOGLE_DRIVE_DIR` | `~/Library/CloudStorage/GoogleDrive-*/My Drive/Reading` (glob) |

Trigger phrases stay user-intent-oriented and route to the renamed provider
ids (e.g., «почитаю на айпаде» → `icloud`; «положи в gdrive» → `google-drive`).

Plugin rename `reading` → `publish` is a hard major bump (v1.0.0). No
backward-compat fallback for `READING_ICLOUD_DIR` — clean break, user edits
`~/.zshrc` once.

## Components / flows

- `plugins/publish/.claude-plugin/plugin.json` — manifest, major bump on rename.
- `plugins/publish/skills/pdf/SKILL.md` — conversion-only spec. Bilingual
  EN+RU triggers ("convert to pdf" / "сделай pdf"). Output path defaults to
  `<source-dir>/<source-stem>.pdf` when target omitted.
- `plugins/publish/skills/pdf/scripts/md-to-pdf.py` — unchanged renderer
  (weasyprint + markdown, atomic write via `.tmp` + `os.replace`). Moved from
  `books/scripts/` via `git mv` so history is preserved.
- `plugins/publish/skills/pdf/references/styles.css` — unchanged stylesheet
  (A4 portrait, IBM Plex Serif 11pt, etc.). Moved from `books/references/`.
- `plugins/publish/skills/pdf/tests/test_anchors.py` — unchanged conversion
  tests. Moved from `books/tests/`.
- `plugins/publish/skills/publish/SKILL.md` — new, written from scratch.
  Holds the shared push procedure (resolve provider → resolve source →
  compute slug → resolve target root → mkdir → invoke pdf script → report).
- `plugins/publish/skills/publish/references/providers.md` — single source
  of truth for the provider table (id, env var, default root, triggers).
- `plugins/publish/skills/publish/references/icloud.md` — iCloud-as-transport
  notes; "Apple Books on iPad is one consumer" sidebar.
- `plugins/publish/skills/publish/references/google-drive.md` — mount-only
  notes, multi-account hard-fail rationale, glob behavior.
- `plugins/publish/skills/publish/tests/` — new tests: provider resolution
  from trigger phrase, env-var precedence, GDrive glob (0 / 1 / >1 matches),
  no-provider-matched flow.
- `.claude-plugin/marketplace.json` — rename entry `reading` → `publish`;
  update `source` path; rewrite description.
- Root `README.md` — replace `### books` / `### reading` sections with
  `### pdf` / `### publish`; update install snippets and project-structure
  ASCII tree.

**Push flow (publish skill, parameterized by provider):**

1. Match user phrase against provider trigger table. If no match → ask the
   user which provider, then continue.
2. Resolve source path; hard-fail if extension is not `.md`.
3. Slug = `Path(source).stem`; on collision in target subfolder, suffix
   `-<sha1(abs_path)[:6]>` (carried over from books).
4. Project root via `git rev-parse --show-toplevel`; fall back to
   `dirname(source)`. Subfolder name = `basename(project_root)`.
5. Resolve provider root: env var → default. For `google-drive`, glob-expand
   the `*` and hard-fail on 0 or >1 matches.
6. `mkdir -p "<root>/Reading/<project>"`.
7. Shell out: `uv run ../pdf/scripts/md-to-pdf.py "<source.md>"
   "<root>/Reading/<project>/<slug>.pdf"`.
8. Print final path; user tap-to-opens on iPad / Drive.

## Scope cuts

- **No EPUB output** — Apple Books pen annotations don't work on EPUB;
  carried over from books v0.1.
- **No rclone / headless upload** — mount-only in v1. rclone is a separate
  future feature.
- **No PDF or non-`.md` input** — `publish` is "convert markdown and ship";
  shipping arbitrary files is out of scope.
- **No syntax highlighting** in code blocks — carried over from books v0.1.
- **No multi-file batching / folder push** — one file per invocation.
- **No cleanup of old PDFs** in target; user curates manually.
- **No annotation pull-back** — push-only across all providers. Pen marks
  stay with the human (icloud); GDrive has no annotation surface anyway.
- **No GDrive multi-account auto-pick** — hard-fail on glob 0 or >1 matches
  and force `PUBLISH_GOOGLE_DRIVE_DIR` to disambiguate.
- **No `READING_ICLOUD_DIR` deprecation grace** — clean break in v1.0.
- **No OneDrive in v1** — explicitly deferred; same shape as `google-drive`
  when added later.
- **No skill-to-skill invocation via the Skill tool** — `publish` shells out
  directly to the `pdf` skill's script. Fewer hops, no skill plumbing.

## Open questions

None outstanding — all four open questions from the brainstorm were
resolved before save:

1. Deprecation horizon → clean break in v1.0.
2. `pdf` skill RU triggers → ship bilingual EN+RU.
3. Subfolder layout → symmetric `<root>/Reading/<project>/` on both
   providers.
4. No-provider-matched UX → ask the user which provider, then proceed.

OneDrive and rclone-headless are deliberately deferred to future iterations,
not unresolved questions.

## Hand-off

Next: `ralph-task feature=publish-plugin-split` to create the two backlog
tasks:

- **T1** — Refactor `reading` → `publish` plugin: extract `pdf` skill,
  scaffold `publish` skill with `icloud` provider only, preserve all
  existing books trigger phrases end-to-end, plugin.json major bump,
  marketplace.json + README updates. AC includes: every books trigger
  resolves to the `icloud` provider; `READING_ICLOUD_DIR` is no longer
  read; existing anchor tests pass under the new pdf path; new tests
  cover provider resolution and no-provider-matched ask flow.
- **T2** — Add `google-drive` provider to `publish` (depends on T1).
  AC includes: glob root with hard-fail on 0/>1 matches; EN+RU triggers
  route to `google-drive`; `PUBLISH_GOOGLE_DRIVE_DIR` overrides glob;
  tests cover all three glob cases.
