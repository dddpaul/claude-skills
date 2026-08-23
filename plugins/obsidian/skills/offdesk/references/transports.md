# Transports

The offdesk skill names a **transport** by the mechanism that carries the
Obsidian vault between the laptop and the reading device, not by the
device: `syncthing` is P2P sync to a phone or tablet, `icloud` is an
Obsidian vault living in iCloud Drive (typically read on an iPad).

Both transports are the same skill with a different vault root. Layout,
frontmatter keys, annotation convention, slug-collision rule, and pull
semantics are identical; only the root differs.

The routing and resolution rules below are implemented — and regression
tested — in [scripts/transports.py](../scripts/transports.py). This page is
the prose version of that module; if the two ever disagree, the module is
authoritative.

## Table

| Transport | Env var | Default root |
|---|---|---|
| syncthing (default) | `OFFDESK_SYNCTHING_VAULT` | `~/Obsidian/offdesk` |
| icloud | `OFFDESK_ICLOUD_VAULT` | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/*` (glob) |

`syncthing` additionally honours `OFFDESK_OBSIDIAN_VAULT`, the name this
knob had before transports existed. It is a supported alias, not a
deprecation: it sits below `OFFDESK_SYNCTHING_VAULT` and above the literal
default, and setting it keeps working silently with no warning.

Roots are resolved at every invocation; restart the shell after editing
your profile (`~/.zshrc` / `~/.bashrc`) before pushing or pulling.

## Resolution order

For each transport, first match wins:

| Transport | Order |
|---|---|
| syncthing | `OFFDESK_SYNCTHING_VAULT` → `OFFDESK_OBSIDIAN_VAULT` → `~/Obsidian/offdesk` |
| icloud | `OFFDESK_ICLOUD_VAULT` → glob `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/*` |

1. Identify the transport from the matched trigger phrase (push) or the
   scan scope (pull).
2. Read the transport's env vars in the order above. The first one that is
   set and non-empty is used verbatim, with a trailing slash stripped. The
   default root is **not** consulted when an env var is set.
3. If no env var is set and the default root is a literal path
   (`syncthing`), expand `~` and use it.
4. If no env var is set and the default root is a glob (`icloud`), expand
   the glob, keep only directories, and apply:

   | Glob matches | Behavior |
   |---|---|
   | 0 | hard-fail; message names `OFFDESK_ICLOUD_VAULT` as the var to set |
   | exactly 1 | use the single match as the vault root |
   | >1 | hard-fail; message names the env var, lists every match, never auto-picks |

   The vault directory name is chosen by the user when the vault is created
   in Obsidian on iOS, which is why the default cannot be a literal path
   and why more than one match is plausible. Guessing would write review
   notes into the wrong vault, so the skill stops instead. Only directories
   count as candidates — the pattern ends in a bare `*`, so a stray file
   beside the vaults must not turn a single-vault machine into a spurious
   multi-match failure.

5. The layout under the root is symmetric across transports:

   ```text
   <vault-root>/<project-basename>/<filename>.md
   ```

   There is no `Reading/` wrapper — that is [[publish]] vocabulary for a
   different job (rendered PDF, push-only).

## Trigger mapping

Push targets exactly one transport; there is no push-to-both.

`syncthing` (eight phrases — every phrase the skill shipped before iCloud
existed, unchanged):

- EN: "send to offdesk", "send to phone for review", "review later", "check later"
- RU: "положи это в offdesk", "положи это в оффдеск", "посмотрю позже", "проверю позже"

`icloud` (six phrases — always explicitly marked):

- EN: "send to offdesk icloud", "offdesk icloud", "offdesk on icloud"
- RU: "положи в offdesk icloud", "положи в оффдеск айклауд", "оффдеск айклауд"

A push phrase that names no transport routes to `syncthing`. This is the
one place offdesk departs from [[publish]], whose resolver returns a
needs-disambiguation sentinel: publish's providers are peers, while
offdesk has an installed base of project folders in the Syncthing vault,
so the default keeps every pre-existing phrase meaning what it meant.
Beyond the exact phrases, a push utterance carrying the marker word
`icloud` / `айклауд` routes to `icloud`, so a marked-but-unlisted phrase
is never silently written to the Syncthing vault.

Pull scans **both** vaults unless the phrase names one:

- both — EN: "review my offdesk notes", "check offdesk feedback";
  RU: "посмотри оффдеск фидбэк", "проверь оффдеск"
- icloud only — EN: "check offdesk icloud", "review my offdesk icloud notes";
  RU: "проверь оффдеск айклауд", "посмотри оффдеск айклауд фидбэк"
- syncthing only — EN: "check offdesk syncthing", "review my offdesk syncthing notes";
  RU: "проверь оффдеск синктинг", "посмотри оффдеск синктинг фидбэк"

## Trigger vocabulary is anchored on "offdesk"

No offdesk phrase may contain `ipad`, `айпад`, `books`, or `книги`. Those
belong to the [[publish]] skill's `icloud` provider, which renders markdown
to PDF and is push-only — the opposite contract to this skill's verbatim
`.md` round-trip. A shared utterance would be unresolvable between the two
skills, so offdesk phrases name the skill ("offdesk" / "оффдеск") and,
optionally, the transport — never the device. The trigger sets of the two
skills are asserted disjoint by
[tests/test_trigger_collisions.py](../tests/test_trigger_collisions.py).

See [[setup]] for the one-time per-transport setup, including where an
Obsidian iOS vault lands on the Mac.
