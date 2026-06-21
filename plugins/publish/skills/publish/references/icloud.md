# iCloud (provider)

iCloud Drive is treated as a **transport**, not as a consumer device. The
publish skill drops a rendered PDF into a per-project subfolder under the
configured iCloud root and trusts iCloud's own sync to push it to every
signed-in device.

## Apple Books on iPad is one consumer

Apple Books on iPad is the canonical consumer for v1 — but it is **one**
consumer of the iCloud transport, not the transport itself. Other
consumers include:

- **Files.app on iPad / iPhone** — tap-to-open in any PDF viewer.
- **Preview / Finder on Mac** — the same file lands under
  `~/Library/Mobile Documents/com~apple~CloudDocs/Reading/...` on every
  signed-in Mac.
- **Documents (Readdle) on iPad** — opens the file from Files.app like
  Books, but supports a different markup workflow.

Naming the provider after the transport (`icloud`) rather than the
consumer (`books`, `ipad`) means adding a new consumer never requires a
provider rename.

## Default root

```text
~/Library/Mobile Documents/com~apple~CloudDocs/Reading
```

Override with `PUBLISH_ICLOUD_DIR` in your shell profile. The skill reads
the env var at every invocation; restart the shell after editing.

## Push-only — pen marks stay with the human

Apple Pencil annotations made in Books on iPad live in Books' local data
store and do not round-trip back to iCloud Drive in a form the skill can
read. The publish skill therefore does **no** annotation pull-back: any
markup the human makes stays on the iPad, with the human.

If you need a fresh copy with structural changes from the laptop, re-run
the same trigger — the slug is stable per source path, so the new PDF
overwrites the old one atomically (`.tmp` + `os.replace`) and iCloud
re-syncs it.

## Slug collision

Two source files with identical basenames (e.g., `~/work/foo/notes.md`
and `~/play/bar/notes.md`) would collide in
`<root>/Reading/<project>/notes.pdf`. Resolution: suffix the slug with
`-<sha1(absolute_source_path)[:6]>` when a collision is detected.

Example: `notes` and `notes-a1b2c3` (where `a1b2c3` is the first 6 hex
chars of `sha1(absolute_source_path)`). Use a stable hash so the same
source always maps to the same slug.

## macOS prerequisites

Before the first push, install weasyprint's native deps and the IBM Plex
fonts used by the default stylesheet (see the [[pdf]] skill for the full
list). The publish skill assumes the PDF skill is already runnable.
