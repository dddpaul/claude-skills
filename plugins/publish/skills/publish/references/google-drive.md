# Google Drive (provider)

Google Drive is treated as a **transport**, not as a consumer device. The
publish skill drops a rendered PDF into a per-project subfolder under the
configured Google Drive root and trusts the Google Drive for desktop client
to sync it to every signed-in device.

## Mount-only — no rclone in v1

v1 supports only the **mounted** path that Google Drive for desktop
provisions on macOS:

```text
~/Library/CloudStorage/GoogleDrive-<account>/My Drive/...
```

No `rclone`, no service-account JSON, no headless upload. Rationale:

- The host's existing Google Drive sync already does the upload — adding a
  second uploader would create a race and require credentials the user has
  not provisioned.
- The mount surface is identical in shape to the `icloud` provider (a path
  the user already trusts), keeping the skill's surface tiny.

If you need headless upload (CI, a remote box without the desktop client),
that is a separate backlog task — not in v1.

## Multi-account hard-fail

The default root is a glob, not a literal path:

```text
~/Library/CloudStorage/GoogleDrive-*/My Drive/Reading
```

The `*` matches the account-suffixed directory that Google Drive for
desktop creates per signed-in account. The resolver applies these rules:

| Glob matches | Behavior |
|---|---|
| 0 | `ProviderResolutionError` — message names `PUBLISH_GOOGLE_DRIVE_DIR` as the env var to set |
| exactly 1 | use the single match as the root |
| >1 (multi-account) | `ProviderResolutionError` — message names `PUBLISH_GOOGLE_DRIVE_DIR`, lists the matches, never auto-picks |

The multi-account hard-fail is **intentional**: silently picking the first
match would route documents to the wrong account half the time on shared
laptops. The skill refuses and asks the user to set
`PUBLISH_GOOGLE_DRIVE_DIR` to the absolute path of the desired account's
`My Drive/Reading` directory.

## Default root

```text
~/Library/CloudStorage/GoogleDrive-*/My Drive/Reading
```

Override with `PUBLISH_GOOGLE_DRIVE_DIR` in your shell profile. The env var
wins verbatim — when it is set, the glob is **not** consulted. The skill
reads the env var at every invocation; restart the shell after editing.

## Push-only — annotations stay in Google's ecosystem

Any markup the human makes in Google Drive Preview, Adobe Acrobat, or
another viewer lives in that viewer's local store and does not round-trip
back in a form the skill can read. The publish skill therefore does **no**
annotation pull-back: any markup the human makes stays with the human.

## Slug collision

Two source files with identical basenames collide in
`<root>/Reading/<project>/<basename>.pdf`. Resolution is identical to the
icloud provider: suffix the slug with `-<sha1(absolute_source_path)[:6]>`
when a collision is detected. Use a stable hash so the same source always
maps to the same slug.

## macOS prerequisites

Install [Google Drive for desktop](https://support.google.com/drive/answer/10838124)
and sign in to the account whose `My Drive/Reading` should receive the
PDF. On a multi-account install, you must set `PUBLISH_GOOGLE_DRIVE_DIR`
explicitly — the skill will not auto-pick.

The skill also assumes the [[pdf]] skill is already runnable (weasyprint +
IBM Plex fonts).
