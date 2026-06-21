# Providers

The publish skill names providers by **transport** rather than by consumer
device. iCloud Drive (the transport) is named `icloud`; Apple Books on iPad
is one of several possible *consumers* of that transport. New consumers
(e.g. Preview on Mac, Documents on iPad) can be added without renaming the
provider.

## Table

| Provider | Env var | Default root |
|---|---|---|
| icloud | `PUBLISH_ICLOUD_DIR` | `~/Library/Mobile Documents/com~apple~CloudDocs/Reading` |

The default root is resolved at every invocation; restart the shell after
editing your profile (`~/.zshrc` / `~/.bashrc`) before pushing.

## Resolution order

For each push:

1. Identify the provider from the matched trigger phrase.
2. Read the provider's env var. If set and non-empty, use it as the root
   (trailing slash stripped).
3. If the env var is unset, use the provider's default root from the table
   above.
4. The final layout under the root is symmetric across providers:

   ```text
   <provider-root>/Reading/<project-basename>/<slug>.pdf
   ```

## v1 scope

v1 ships **icloud only**. The table above lists exactly one row. There is
no fallback to the legacy v0.x env var used by the pre-rename `reading`
plugin — setting it has no effect on the publish skill.

Trigger → provider mapping for v1 (all eight icloud triggers route to
`icloud`):

- EN: "send to books", "read on ipad", "review on books", "send to icloud"
- RU: "положи это в books", "положи это в книги", "почитаю на айпаде", "положи в icloud"

Generic phrases ("publish this" / "отправь это") match no specific
provider; the resolver returns a needs-disambiguation sentinel and the
skill asks the user before proceeding.

See [[icloud]] for iCloud-as-transport notes.
