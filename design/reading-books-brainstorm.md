# reading-books — push markdown to Apple Books on iPad for pen annotation

## Architecture decision

Ship a new Claude Code plugin **`reading`** in this repo containing a single skill **`books`**. The skill is **push-only**: it converts a markdown file from the active project into a PDF, writes it into an iCloud Drive subfolder, and trusts iCloud + Apple Books to surface it on the iPad. There is no read-back path — Apple Pencil annotations live with the human, not with Claude.

Happy Engineering is positioned as the **remote trigger channel**, not a reading surface. Push triggers issued from Happy on mobile/CLI/macOS proxy through to Claude Code running on macOS, where the skill executes (weasyprint + iCloud both live on macOS). No Happy plugin code is needed.

## Components / flows

### Repo layout

```text
plugins/
└── reading/
    ├── .claude-plugin/
    │   └── plugin.json
    └── skills/
        └── books/
            ├── SKILL.md
            ├── references/
            │   └── styles.css
            └── scripts/
                └── md-to-pdf.py
```

A 4th entry is added to `.claude-plugin/marketplace.json`:

```json
{
  "name": "reading",
  "source": "./plugins/reading",
  "description": "Push markdown from any project to Apple Books on iPad as PDF for off-desk reading with Apple Pencil annotations. Push-only via iCloud Drive."
}
```

`plugins/reading/.claude-plugin/plugin.json`:

```json
{
  "name": "reading",
  "version": "0.1.0",
  "description": "MD → PDF → iCloud Drive → Apple Books on iPad. Push-only; pen marks stay with the human.",
  "author": {
    "name": "Pavel Derendyaev",
    "email": "dddpaul@gmail.com"
  },
  "homepage": "https://github.com/dddpaul/claude-skills",
  "repository": "https://github.com/dddpaul/claude-skills",
  "license": "Apache-2.0"
}
```

### Push procedure

On a push trigger the skill:

1. Resolves the absolute path of the source `.md` file. Hard-fail if not `.md`.
2. Computes slug = `basename(source)` without extension. On collision in the target dir, append `-<sha1(absolute-path)[:6]>` (lifted from offdesk).
3. Resolves project root via `git rev-parse --show-toplevel`, falling back to `dirname(source)`. The root's basename becomes the iCloud subfolder name.
4. Resolves iCloud target:
   ```
   ICLOUD_DIR="${READING_ICLOUD_DIR:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Reading}"
   TARGET_DIR="$ICLOUD_DIR/<project-basename>"
   mkdir -p "$TARGET_DIR"
   ```
5. Converts MD → PDF via `scripts/md-to-pdf.py <source.md> <target.pdf>`, which uses the `markdown` package + weasyprint with CSS from `references/styles.css`. Dependencies pulled via `uv add weasyprint markdown` at install time; macOS needs `cairo`, `pango`, `gdk-pixbuf` installed (brew).
6. Writes atomically: convert to `$TARGET_DIR/.<slug>.pdf.tmp`, then `mv` to `$TARGET_DIR/<slug>.pdf` so iCloud only sees complete files.
7. Reports the final iCloud path so the user can tap-to-open in Files.app on iPad → Open in Books.

No frontmatter, no manifest, no metadata — PDF is opaque.

### PDF layout for pen annotations

`references/styles.css` defaults:

- Page size: **A4 portrait** (Books reads naturally in portrait).
- Margins: 20mm top/bottom/left, **~35mm right** — wide gutter for marginalia. Right-handed bias; revisit if a lefty complains.
- Line height: **1.4** (normal reading; pen underlines fit between lines, notes go in the margin, no need to loosen).
- Font: `Georgia, "Times New Roman", serif`, 12pt body, 18/15/13 for H1/H2/H3.
- Code: `Menlo, Consolas, monospace`, 10pt, light-grey background, **no syntax highlighting in v0.1**.
- Links: underlined, **black** (Books doesn't follow them; blue is just ink-noise).
- Images: `max-width: 100%` so they don't overflow.
- Page breaks: `h1, h2 { page-break-before: auto; break-inside: avoid; }` to prevent orphan headings.

CSS lives in `references/` so the user can override without touching the script.

### Trigger phrases (SKILL.md frontmatter)

- EN push: "send to books", "read on ipad", "review on books"
- RU push: "положи это в books", "положи это в книги", "почитаю на айпаде"

No pull triggers (push-only design).

## Scope cuts

- **No read-back path.** No annotation export, no OCR, no callout pull. Apple Pencil marks stay on iPad.
- **No Books library auto-import.** User taps the file in Files.app and chooses "Open in Books". One tap; saves a brittle URL-scheme dance.
- **No AirDrop / email fallback.** iCloud Drive is the only transport; failures are loud.
- **No EPUB output.** Apple Books pen annotations don't work on EPUB — PDF only.
- **No syntax highlighting in v0.1** (deferred; revisit if user complains).
- **No bidirectional sync with offdesk.** Different surface, different skill, different repo plugin.
- **No Happy plugin code.** Happy is just the chat channel that triggers the skill remotely.
- **No multi-file push in v0.1** — one file at a time; folder-push deferred to v0.2.
- **No auto-cleanup of old PDFs** in v0.1 (offdesk doesn't either); revisit in v0.2.

## Open questions

- **Cleanup policy.** Should the skill prune old PDFs from iCloud (by age, count, or git-status)? Defer to v0.2.
- **Multi-file push.** "Send the whole `docs/` folder" — defer to v0.2.
- **iCloud sync confirmation.** Skill writes the file and exits; if iPad doesn't see it, user pulls-to-refresh in Files.app. No `brctl` poll (undocumented).
- **Left-handed gutter.** Right-margin gutter assumes right-handed pen use. Add a config knob in v0.2 if needed.
- **Font choice.** Georgia is a safe default; user may prefer system sans (San Francisco) — easy to change in `styles.css`.

## Hand-off

Next: invoke `ralph-task` with `feature=reading-books` to decompose this design into backlog tasks. The Phase-4 override binds the slug `reading-books` to the eventual `feature:reading-books` label so `/ralph-review feature=reading-books` can later evaluate cumulative consistency against this doc.
