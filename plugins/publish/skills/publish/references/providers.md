# Providers

The publish skill names providers by **transport** rather than by consumer
device. iCloud Drive (the transport) is named `icloud`; Apple Books on iPad
is one of several possible *consumers* of that transport. New consumers
(e.g. Preview on Mac, Documents on iPad) can be added without renaming the
provider.

## Table

| Provider | Env var | Default root |
|---|---|---|
| icloud | `PUBLISH_ICLOUD_DIR` | `~/Library/Mobile Documents/com~apple~CloudDocs` |
| google-drive | `PUBLISH_GOOGLE_DRIVE_DIR` | `~/Library/CloudStorage/GoogleDrive-*/My Drive` (glob) |
| onedrive | `PUBLISH_ONEDRIVE_DIR` | `~/Library/CloudStorage/OneDrive-*` (glob) |

The default root is resolved at every invocation; restart the shell after
editing your profile (`~/.zshrc` / `~/.bashrc`) before pushing.

## Resolution order

For each push:

1. Identify the provider from the matched trigger phrase.
2. Read the provider's env var. If set and non-empty, use it as the root
   (trailing slash stripped). The glob below is **not** consulted when the
   env var is set — the env value wins verbatim.
3. If the env var is unset and the provider's default root is a literal
   path (e.g. `icloud`), use it.
4. If the env var is unset and the provider's default root is a glob (e.g.
   `google-drive`, `onedrive`), expand the glob and apply:

   | Glob matches | Behavior |
   |---|---|
   | 0 | hard-fail; message names the env var to set |
   | exactly 1 | use the single match as the root |
   | >1 (multi-account) | hard-fail; message names the env var, lists matches, never auto-picks |

5. The final layout under the root is symmetric across providers:

   ```text
   <provider-root>/Reading/<project-basename>/<slug>.pdf
   ```

## Trigger mapping

Each trigger phrase maps to exactly one provider.

`icloud` (eight phrases):

- EN: "send to books", "read on ipad", "review on books", "send to icloud"
- RU: "положи это в books", "положи это в книги", "почитаю на айпаде", "положи в icloud"

`google-drive` (seven phrases):

- EN: "send to gdrive", "send to google drive", "read on gdrive", "read on drive"
- RU: "положи в gdrive", "положи в гугл драйв", "отправь на драйв"

`onedrive` (six phrases):

- EN: "send to onedrive", "send to one drive", "read on onedrive"
- RU: "положи в onedrive", "положи в ванндрайв", "отправь на onedrive"

Generic phrases ("publish this" / "отправь это") match no specific
provider; the resolver returns a needs-disambiguation sentinel and the
skill asks the user before proceeding.

There is no fallback to the legacy v0.x env var used by the pre-rename
`reading` plugin — setting it has no effect on the publish skill.

See [[icloud]] for iCloud-as-transport notes, [[google-drive]] for Google
Drive notes (mount-only rationale, multi-account hard-fail), and
[[onedrive]] for OneDrive notes (Personal vs Work/School mounts).
