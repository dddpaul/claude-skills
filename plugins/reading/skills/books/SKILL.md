---
name: books
description: Push a markdown file from the active project into iCloud Drive as a PDF so Apple Books on iPad picks it up for off-desk reading with Apple Pencil annotations. Push-only — no read-back, no annotation extraction, no Books auto-import. Push triggers (EN) "send to books", "read on ipad", "review on books"; push triggers (RU) "положи это в books", "положи это в книги", "почитаю на айпаде".
---

# Books

User-level skill that converts a markdown file from the active project into a
PDF, drops it into an iCloud Drive subfolder, and trusts iCloud + Apple Books
to surface it on the iPad. The skill is **push-only**: Apple Pencil
annotations stay on the iPad, with the human, not with Claude.

The skill performs MD → PDF conversion directly via `scripts/md-to-pdf.py`
(weasyprint + the `markdown` package), then `mkdir -p` + `os.replace` for an
atomic publish into iCloud Drive.

## iCloud target path

Default iCloud Drive root on the laptop:

```text
~/Library/Mobile Documents/com~apple~CloudDocs/Reading
```

Override: set `READING_ICLOUD_DIR` in your shell profile (`~/.zshrc` or
`~/.bashrc`) to point at any directory under iCloud Drive (or elsewhere). The
skill reads it at every invocation; restart the shell after editing.

Every push step that touches iCloud resolves the root with:

```bash
ICLOUD_DIR="${READING_ICLOUD_DIR:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Reading}"
ICLOUD_DIR="${ICLOUD_DIR%/}"   # strip trailing slash for consistency
```

## Push

Trigger phrases (any of):

- EN: "send to books", "read on ipad", "review on books"
- RU: "положи это в books", "положи это в книги", "почитаю на айпаде"

Procedure:

1. **Resolve the source path.** Take the absolute path of the source markdown
   file. **Hard-fail if the extension is not `.md`** — this skill ships
   markdown only; PDF/EPUB inputs are out of scope.
2. **Compute the slug** = `Path(source).stem` (the filename without the `.md`
   extension). On collision in the target directory, append
   `-<sha1(absolute_source_path)[:6]>` — mirrors the offdesk slug-collision
   pattern at [`plugins/obsidian/skills/offdesk/SKILL.md`](../../../obsidian/skills/offdesk/SKILL.md).
3. **Resolve the project root** via `git rev-parse --show-toplevel`. If the
   command fails (not a git repo), fall back to `dirname(source)`. The
   `basename` of the project root becomes the iCloud subfolder name.
4. **Resolve the iCloud target** and ensure the per-project subdir exists:
   ```bash
   ICLOUD_DIR="${READING_ICLOUD_DIR:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Reading}"
   TARGET_DIR="$ICLOUD_DIR/<project-basename>"
   mkdir -p "$TARGET_DIR"
   ```
5. **Convert MD → PDF** by invoking the conversion script with the source
   markdown and the target PDF path:
   ```bash
   uv run plugins/reading/skills/books/scripts/md-to-pdf.py \
       "<source.md>" \
       "$TARGET_DIR/<slug>.pdf"
   ```
6. **Atomic write.** The script writes the PDF to a hidden temporary file
   alongside the target (`.<slug>.pdf.tmp`), then `os.replace`s it to the
   final `<slug>.pdf` so iCloud only sees complete files.
7. **Report the final iCloud path** to the user so they can tap-to-open in
   Files.app on iPad → Open in Books.

## PDF layout

`references/styles.css` produces the default layout:

- Page size: **A4 portrait**.
- Margins: **20mm symmetric** on all sides.
- Line height: **1.4** — underlines fit between lines, notes go in the
  margin.
- Font: `'IBM Plex Serif', 'PT Serif', 'Apple Color Emoji', 'Times New Roman', serif`,
  12pt body, with `font-variant-numeric: lining-nums` so digits sit on the
  baseline; 18/15/13 pt for H1/H2/H3.
- Code: `'IBM Plex Mono', Menlo, Consolas, monospace`, 10pt, light-grey
  background. No syntax highlighting in v0.1.
- Links: underlined, blue (`#0050b3`).
- Images: `max-width: 100%`.
- Page breaks: `h1, h2 { page-break-before: auto; break-inside: avoid; }` to
  prevent orphan headings.

CSS lives in `references/` so the user can override without touching the
script.

## Dependencies

The skill needs both the `markdown` and `weasyprint` Python packages, plus
their native dependencies on macOS.

Python packages — installed via `uv` in the repo root:

```bash
uv add weasyprint markdown
```

macOS system prerequisites — install via Homebrew **before** the first push,
or weasyprint will fail to render with a cryptic Cairo/Pango error:

```bash
brew install cairo pango gdk-pixbuf
brew install --cask font-ibm-plex
```

The cairo/pango/gdk-pixbuf trio are runtime dependencies for weasyprint's PDF
rendering pipeline. `font-ibm-plex` installs the IBM Plex Serif / Mono families
used by the default stylesheet; without them weasyprint falls back to PT Serif
or Times New Roman.

## Slug collision

Two source files with identical basenames (e.g., `~/work/foo/notes.md` and
`~/play/bar/notes.md`) would collide in `$TARGET_DIR/notes.pdf`. Resolution:
suffix the slug with a short hash of the absolute source path when a
collision is detected.

Example: `notes` and `notes-a1b2c3` (where `a1b2c3` is the first 6 hex chars
of `sha1(absolute_source_path)`). Use a stable hash so the same source
always maps to the same slug.

This mirrors the offdesk pattern at
[`plugins/obsidian/skills/offdesk/SKILL.md`](../../../obsidian/skills/offdesk/SKILL.md).

## Out of scope (v0.1)

- **No pull triggers, no annotation extraction.** Pen marks stay on iPad
  with the human.
- **No Books library auto-import.** User taps the file in Files.app and
  chooses "Open in Books" — saves a brittle URL-scheme dance.
- **No EPUB output.** Apple Books pen annotations don't work on EPUB.
- **No AirDrop / email fallback.** iCloud Drive is the only transport.
- **No syntax highlighting** in code blocks (deferred to v0.2).
- **No multi-file push** (one file at a time; folder-push deferred to v0.2).
- **No auto-cleanup** of old PDFs in iCloud (deferred to v0.2).
