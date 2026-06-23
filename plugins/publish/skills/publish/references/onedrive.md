# OneDrive (provider)

OneDrive is treated as a **transport**, not as a consumer device. The
publish skill drops a rendered PDF into a per-project subfolder under the
configured OneDrive root and trusts the OneDrive client to sync it to every
signed-in device.

## Mount-only — no rclone, no Graph API in v1

v1 supports only the **mounted** path that the OneDrive client provisions
on macOS:

```text
~/Library/CloudStorage/OneDrive-<account>/...
```

No `rclone`, no Microsoft Graph upload, no headless path. Rationale:

- The host's existing OneDrive sync already does the upload — adding a
  second uploader would create a race and require credentials the user has
  not provisioned.
- The mount surface is identical in shape to the `google-drive` provider
  (a path the user already trusts), keeping the skill's surface tiny.

If you need headless upload (CI, a remote box without the desktop client),
that is a separate backlog task — not in v1.

## Personal vs Work/School

Modern macOS OneDrive provisions two different naming conventions:

| Account type | Mount path |
|---|---|
| Personal | `~/Library/CloudStorage/OneDrive-Personal` |
| Work / School | `~/Library/CloudStorage/OneDrive-<Org>` (org name from tenant) |

The skill does not distinguish between them — both match the
`OneDrive-*` glob, both are treated as transports. If you have multiple
mounts signed in on the same machine (e.g. one Personal + one Work), set
`PUBLISH_ONEDRIVE_DIR` to the absolute path of the desired mount.

## Multi-account hard-fail

The default root is a glob, not a literal path:

```text
~/Library/CloudStorage/OneDrive-*
```

The `*` matches the account-suffixed directory described above. The
resolver applies these rules:

| Glob matches | Behavior |
|---|---|
| 0 | `ProviderResolutionError` — message names `PUBLISH_ONEDRIVE_DIR` as the env var to set |
| exactly 1 | use the single match as the root |
| >1 (multi-account) | `ProviderResolutionError` — message names `PUBLISH_ONEDRIVE_DIR`, lists the matches, never auto-picks |

The multi-account hard-fail is **intentional**: silently picking the first
match would route documents to the wrong account half the time on machines
signed in to both Personal and Work/School. The skill refuses and asks the
user to set `PUBLISH_ONEDRIVE_DIR` to the absolute path of the desired
mount.

## Default root

```text
~/Library/CloudStorage/OneDrive-*
```

Override with `PUBLISH_ONEDRIVE_DIR` in your shell profile. The env var
wins verbatim — when it is set, the glob is **not** consulted. The skill
reads the env var at every invocation; restart the shell after editing.

## Push-only — annotations stay in OneDrive's ecosystem

Any markup the human makes in OneDrive Preview, Adobe Acrobat, or another
viewer lives in that viewer's local store and does not round-trip back in
a form the skill can read. The publish skill therefore does **no**
annotation pull-back: any markup the human makes stays with the human.

## Slug collision

Two source files with identical basenames collide in
`<root>/Reading/<project>/<basename>.pdf`. Resolution is identical to the
icloud and google-drive providers: suffix the slug with
`-<sha1(absolute_source_path)[:6]>` when a collision is detected. Use a
stable hash so the same source always maps to the same slug.

## macOS prerequisites

Install [OneDrive for Mac](https://www.microsoft.com/en-us/microsoft-365/onedrive/download)
and sign in to the account whose mount should receive the PDF. On a
multi-account install (e.g. Personal + Work), you must set
`PUBLISH_ONEDRIVE_DIR` explicitly — the skill will not auto-pick.

The skill also assumes the [[pdf]] skill is already runnable (weasyprint +
IBM Plex fonts).
