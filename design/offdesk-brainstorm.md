# Offdesk

User-level Claude skill for sending markdown documents from any project to a
personal Obsidian vault synced to a secondary device (phone/tablet) for
off-desk reading and review, with annotated feedback returning to the
originating project on the laptop.

Brainstormed 2026-06-13 in the `confush` (upmark) project context. Mirrored
here from `~/.claude/brainstorms/offdesk-brainstorm.md` as the canonical
design doc — see the addendum at the bottom for the impl-home decision that
supersedes the original hand-off section.

## Architecture decision

- **Transport:** Syncthing P2P between laptop and the secondary device. No
  cloud, no bot, no VPS, no PDF rendering, no Telegram.
- **Vault path on laptop:** `~/Obsidian/android/` (device-specific subdir; an
  iPad would get `~/Obsidian/ipad/` as a parallel vault).
- **Vault path on Android:** `/storage/emulated/0/Obsidian/android/`.
- **Reader app:** Obsidian Android, with the synced folder opened as a vault.
- **Skill mechanics:** Claude performs file copy / grep / frontmatter merge
  operations ad-hoc per the SKILL.md instructions. No compiled CLI tool.

## Components / flows

### Vault layout

```
~/Obsidian/android/                   # Syncthing-root
├── .obsidian/                        # vault config (Templates plugin, toolbar)
├── .stignore                         # syncthing ignore patterns
├── CONVENTIONS.md                    # reference doc for the user
├── <project-basename>/               # one subdir per source project
│   ├── <file>.md
│   └── ...
└── _scratch/                         # md not associated with any project
```

### Push (laptop → device)

Trigger phrases (skill should match any): "положи это в offdesk", "send to
offdesk", "send to phone for review", "обработай для phone", "review later".

1. Resolve project root via `git rev-parse --show-toplevel` (fallback: `pwd`).
2. Project slug = `basename(project_root)`.
3. `mkdir -p ~/Obsidian/android/<slug>/`.
4. Read the source md; parse any existing frontmatter.
5. **Merge** `offdesk-*` keys into the existing frontmatter — do NOT prepend a
   second `---` block, that would break YAML:
   - `offdesk-source: <relative path from project root>`
   - `offdesk-project-root: <absolute project root>`
   - `offdesk-copied-at: <ISO 8601 UTC timestamp>`
6. Keep all existing keys untouched (`confluence-*` from upmark, jekyll/hugo
   fields, etc.).
7. Write to `~/Obsidian/android/<slug>/<filename>.md`. Syncthing propagates.

### Pull (device → laptop)

Trigger phrases: "посмотри фидбэк", "что я там накорябал", "review my offdesk
notes", "check feedback".

1. Project slug from `cwd` / `git rev-parse --show-toplevel`.
2. `grep -nrE '^>\s*\[!ai\]' ~/Obsidian/android/<slug>/`.
3. For each hit, parse the file's frontmatter to extract `offdesk-source` and
   `offdesk-project-root` for source-back mapping.
4. Report findings to the user with `<source-file>:<line>` location and the
   callout content.
5. If the user wants Claude to apply changes (e.g., per `>[!fix]`), confirm
   before modifying the source file.

### Annotation convention

- `>[!ai] question or comment for Claude` — block-level Obsidian callout.
  Claude addresses these.
- `>[!todo] reminder for the user themselves` — block-level callout. Claude
  ignores these (`grep -nrE '^>\s*\[!todo\]'` is for the user, not Claude).
- Multi-line callouts: each subsequent line also starts with `>`. Obsidian
  Android auto-inserts `>` on Enter when inside an existing callout.
- Both `>[!ai]` and `> [!ai]` (no-space and with-space) render correctly in
  Obsidian — the grep regex `^>\s*\[!ai\]` handles both.

### Cleanup before pushing source upstream

If the source is also pushed elsewhere (e.g., back to Confluence via `upmark
push`), strip `offdesk-*` keys from the frontmatter and any `>[!ai]` callouts
from the body before push. Vault copies stay annotated as history.

### Manual setup the user does once (not part of the skill code)

- `brew install syncthing && brew services start syncthing` on macOS.
- Syncthing WebUI at http://127.0.0.1:8384: Add Folder, path
  `~/Obsidian/android`, label "offdesk-android", folder ID `offdesk-android`.
- Install Syncthing on Android (F-Droid is the cleanest channel).
- Pair devices: scan QR from laptop WebUI on Android, accept the connection
  request on the laptop side, accept the shared folder on Android.
- Install Obsidian on Android (Play Store), open
  `/storage/emulated/0/Obsidian/android/` as a vault.
- In Obsidian Android: enable the built-in **Templates** plugin. Create
  `_templates/ai-callout.md` (content: `>[!ai] `, with trailing space and the
  cursor expected to land after `] `) and `_templates/todo-callout.md`
  (content: `>[!todo] `). Bind both to the bottom toolbar via Settings →
  Mobile → Manage toolbar options.
- `.stignore` in the vault root:
  ```
  .obsidian/workspace.json
  .obsidian/workspace-mobile.json
  .obsidian/workspace.json.tmp
  .DS_Store
  *.swp
  *.sync-conflict-*
  ```

## Scope cuts

- **No standalone CLI tool.** The skill instructs Claude to perform copy +
  frontmatter merge + grep directly. If certain operations get awkward to
  inline, a helper Python script can be added later under
  `~/.claude/skills/offdesk/scripts/`.
- **No PDF rendering, Telegram bot, or VPS.** Earlier candidates explored
  during the brainstorm and rejected for complexity.
- **No automatic feedback application.** Claude always confirms before
  modifying source files based on `>[!ai]` content.
- **No symlinks.** Each vault file is a real copy. Re-pushing the same source
  updates the vault copy (with a confirmation prompt if unprocessed feedback
  exists in the vault copy).
- **No iPad / second device for now.** If/when added, a parallel vault
  `~/Obsidian/ipad/` with its own Syncthing folder.

## Open questions

- **Multi-device strategy:** per-device vaults (`~/Obsidian/{android,ipad}/`)
  vs. one shared vault for all reading devices. Tentative: per-device to
  avoid review conflicts across devices.
- **Re-push conflict policy:** if the vault copy has unprocessed `>[!ai]`
  callouts and the user pushes the same source again, the skill should
  prompt "overwrite (loses pending review)?". Exact UX deferred to
  implementation.
- **Frontmatter parser library:** `ruamel.yaml` (already used in upmark),
  `PyYAML`, the `yq` CLI, or hand-rolled. Deferred to implementation.
- **Slug collision:** two projects with identical basenames will collide in
  `~/Obsidian/android/`. Tentative: suffix with a short hash of
  `project_root` when collision detected.
- **Cleanup ergonomics:** how does the user signal "this vault copy is fully
  reviewed, you can archive/delete it"? Possible: rename to `_archive/<…>.md`,
  or add `offdesk-archived-at` to frontmatter. Deferred.

## Hand-off

Implement in a **separate project** (not confush/upmark).

Bootstrap outline for the implementing project:

1. Create a fresh directory (e.g., `~/Private/Projects/ai/offdesk/`).
2. Run `ralph-init` there.
3. Reference this brainstorm via `~/.claude/brainstorms/offdesk-brainstorm.md`
   as design source. The new project's `design/offdesk-brainstorm.md` can be
   a copy of this file, or a thin pointer to it.
4. Write `~/.claude/skills/offdesk/SKILL.md` with the push and pull
   procedures described above. The skill instructs Claude to do the copy +
   frontmatter merge + grep operations directly — no compiled CLI tool
   required in the first cut.
5. User does the manual setup steps (Syncthing, Obsidian Android, templates,
   toolbar buttons) once.

After the SKILL.md exists, the skill becomes invocable from any project
context, e.g.: `/offdesk push design/upmark-pull-attachments-prd.md` or just
natural-language triggers ("положи это в offdesk", "посмотри фидбэк").

---

## Addendum: device-neutral default + configurable vault path (added 2026-06-14)

### Why

The original brainstorm hardcoded the laptop vault path as `~/Obsidian/android/`
because the only confirmed reader device at the time was an Android phone.
That coupling has two problems:

1. **Misleading default.** The folder name says "android" but the content
   inside is just markdown — nothing Android-specific. A user with only an
   iPad gets a confusing default name, and the "iPad would get a parallel
   vault" plan multiplies device-named folders even though Syncthing treats
   them identically.
2. **No override mechanism.** A user with a non-default Obsidian layout
   (e.g., `~/Documents/Obsidian/`, or an existing vault they want to reuse)
   has to fork the SKILL.md to point at it.

### What changed

- **Default vault path renamed:** `~/Obsidian/android/` → `~/Obsidian/offdesk/`.
  Device-neutral, matches the skill name, doesn't lie about content.
- **Configurable via `OFFDESK_OBSIDIAN_VAULT` env var:** the skill reads
  `$OFFDESK_OBSIDIAN_VAULT` at invocation. If set, it's used verbatim (after
  `~`-expansion and trailing-slash normalization). If unset or empty,
  defaults to `~/Obsidian/offdesk/`. No config file, no precedence chain
  — single env var, single default.
- **Per-project subdir convention unchanged:** still
  `$VAULT_ROOT/<project-slug>/<file>.md`. Slug-collision logic from the
  brainstorm still applies (short hash suffix).
- **Android-side path** (`/storage/emulated/0/Obsidian/android/`) is **not**
  affected by `OFFDESK_OBSIDIAN_VAULT` — that's a Syncthing folder mapping the user
  configures once on the Android device, independent of the laptop env var.
  The Syncthing folder ID can stay `offdesk-android` or be renamed to
  `offdesk` at the user's discretion; setup docs should mention both.
- **Multi-device open question partially resolved:** with a configurable
  laptop path, a future iPad user just sets `OFFDESK_OBSIDIAN_VAULT=~/Obsidian/ipad`
  in a separate shell or Syncthing config. No code change needed for the
  per-device case. The "shared vault across devices" case still costs
  nothing extra — point both Syncthing folders at the same laptop path.

### Implementation checklist

The implementer should:

1. In `plugins/obsidian/skills/offdesk/SKILL.md`, the **push** procedure
   step 3 becomes: `VAULT_ROOT="${OFFDESK_OBSIDIAN_VAULT:-$HOME/Obsidian/offdesk}"`,
   normalize trailing slash, then `mkdir -p "$VAULT_ROOT/<slug>/"`. Same
   pattern in the pull procedure for the grep target.
2. SKILL.md must explicitly document the env var contract (default
   `~/Obsidian/offdesk`, set via shell profile for persistence) near the
   top of the body so users can override without reading the procedure
   sections in full.
3. Setup docs (`references/setup.md` or equivalent) update the Syncthing
   step to use the new default path and mention that the laptop folder
   name is now the user's choice (`OFFDESK_OBSIDIAN_VAULT` env var) but the
   Syncthing folder label and Android-side path are independent.
4. Marketplace entry description should refer to "Obsidian vault" generically,
   not "phone/tablet" specifically (since the laptop path is now
   device-agnostic).
5. The brainstorm's "Manual setup" section above still references
   `~/Obsidian/android/` and `offdesk-android`. Setup docs in the
   implementation should use the **new** defaults; the brainstorm body is
   frozen historical context per the no-edit-prior-sections rule.
6. No backward-compatibility shim needed — this is v0.1.0 with zero users.

### Why

The original "Hand-off" section above proposes bootstrapping a fresh
`~/Private/Projects/ai/offdesk/` project for offdesk. That made sense at the
time of brainstorming (2026-06-13), when offdesk's host project (`confush`)
was project-scoped and couldn't host a user-level skill. Later that same
day, the `claude-skills` repo was restructured into a Claude Code plugin
marketplace organized by domain (`dddpaul-claude-skills` marketplace,
`plugins/<domain>/` layout), and the marketplace brainstorm explicitly
anticipated `obsidian` as a future plugin domain. That changes the
calculus: this repo is now the canonical distribution channel for
user-level Claude skills, and the `obsidian` domain is already named as
forward-compatible scope.

### What changed

Implementation home shifts from a fresh `~/Private/Projects/ai/offdesk/`
project to **`plugins/obsidian/skills/offdesk/` inside this repo**. Concretely:

| Item | Original plan | Revised plan |
|------|---------------|--------------|
| Repo | new `~/Private/Projects/ai/offdesk/` | `claude-skills` (this repo) |
| Skill path | `~/.claude/skills/offdesk/SKILL.md` | `plugins/obsidian/skills/offdesk/SKILL.md` (installed via plugin marketplace) |
| Distribution | manual symlink or `claude config add skills` | `/plugin install obsidian@dddpaul-claude-skills` |
| Plugin domain | n/a | new `obsidian` plugin, version `0.1.0`, registered in `.claude-plugin/marketplace.json` |
| Plugin owner / license | n/a | Pavel Derendyaev / Apache-2.0 (consistent with `architect` and `presentation`) |
| Helper scripts | `~/.claude/skills/offdesk/scripts/` (if needed) | `plugins/obsidian/skills/offdesk/scripts/` (if needed) — same relative-to-skill convention as `arch-draw/references/` |

Nothing in the brainstorm's body changes — vault layout, push/pull flows,
annotation convention, scope cuts, open questions all still apply
unchanged. Only the *housing* moves.

### Implementation checklist

The implementer (autonomous Ralph or interactive) should:

1. Register a new plugin entry in `.claude-plugin/marketplace.json`:
   ```json
   {
     "name": "obsidian",
     "source": "./plugins/obsidian",
     "description": "Obsidian vault tooling — offdesk push/pull for off-desk markdown review on phone/tablet via Syncthing."
   }
   ```
2. Create `plugins/obsidian/.claude-plugin/plugin.json` (same shape as
   architect/presentation manifests: version `0.1.0`, author Pavel
   Derendyaev, license Apache-2.0, homepage and repository
   `https://github.com/dddpaul/claude-skills`).
3. Create `plugins/obsidian/skills/offdesk/SKILL.md` with the frontmatter
   trigger phrases from the brainstorm (EN + RU push and pull) and the
   procedural body covering: project-root resolution, slug derivation,
   frontmatter merge for push, callout grep + source mapping for pull,
   pre-upstream-push cleanup, and confirmation rules.
4. Reference helper scripts only if a flow gets awkward to inline (e.g., the
   YAML merge in push step 5). Defer the scripts vs. inline decision per
   the brainstorm's "no standalone CLI tool" scope cut.
5. README.md updates: add an `Obsidian` row to the Skills section with a
   `*Plugin: obsidian*` tag, register the new plugin in the Project
   Structure tree, and add `/plugin install obsidian@dddpaul-claude-skills`
   to the Installation block.
6. Document the manual user-setup steps (Syncthing on macOS, Syncthing on
   Android, Obsidian Android, templates and toolbar) in the SKILL.md body or
   a sibling `references/setup.md` — these are explicitly **out of scope**
   for the skill code (the brainstorm says the user does them once) but
   need to be discoverable.
7. No need to bootstrap a separate ralph-init project; this repo already has
   the full Ralph infrastructure (backlog, hooks, devcontainer, CLAUDE.md).

After landing, the user-global brainstorm at
`~/.claude/brainstorms/offdesk-brainstorm.md` can stay for historical
context — this `design/offdesk-brainstorm.md` plus addendum is the
authoritative source for implementation going forward.

---

## Addendum: trigger refinements (added 2026-06-14)

### Why

The trigger lists in the original Push/Pull sections were a first-pass set drafted during the initial brainstorm. Two problems surfaced once they were carried into TASK-3's frontmatter spec: several phrases were too generic and would collide with non-offdesk asks (bare "check feedback" or "посмотри фидбэк" could fire on any feedback discussion), and a few were too narrow or one-off ("обработай для phone", "что я там накорябал" — situational phrasings that wouldn't recur). A refined trigger set was applied. This addendum carries the change into the canonical design doc so `/ralph-review feature=offdesk` reads the same intent the implementer (TASK-3) reads.

### What changed

The original Push and Pull trigger lists in the brainstorm body above are superseded by these refined sets:

- **Push (EN):** "send to offdesk", "send to phone for review", "review later", "check later"
- **Push (RU):** "положи это в offdesk", "положи это в оффдеск", "посмотрю позже", "проверю позже"
- **Pull (EN):** "review my offdesk notes", "check offdesk feedback"
- **Pull (RU):** "посмотри оффдеск фидбэк", "проверь оффдеск"

Notable deltas vs the original:

- **Removed for being too generic:** "check feedback", "посмотри фидбэк".
- **Removed for being too narrow/one-off:** "обработай для phone", "что я там накорябал".
- **Added Cyrillic spelling of "оффдеск"** so RU triggers don't depend on remembering the Latin-spelled "offdesk".
- **Added delayed-review phrasings** ("review later" / "check later" / "посмотрю позже" / "проверю позже") so the natural "I'll look at this from the couch later" intent reaches the skill.

Everything else in the brainstorm body — vault layout (subject to the vault-path addendum above), push/pull procedural steps, annotation convention, cleanup flow, scope cuts, open questions — is unchanged.

### Implementation checklist

- TASK-3 description trigger lists already updated to match.
- TASK-3 AC verifying frontmatter triggers already updated to substring set: 'send to offdesk', 'положи это в offdesk', 'review my offdesk notes', 'посмотри оффдеск фидбэк'.
- TASK-4 description Example block and AC verifying README triggers already updated to: 'положи это в offdesk', 'посмотри оффдеск фидбэк'.
- User-global brainstorm at `~/.claude/brainstorms/offdesk-brainstorm.md` is intentionally NOT updated — it stays as the historical pre-update snapshot. This in-repo design doc plus its addenda is the authoritative trigger set for implementation and review.

---

## Addendum: iCloud transport for iPad + Obsidian (added 2026-08-23)

### Why

The skill was designed around Syncthing to a phone/tablet, with Obsidian on Android. The user now wants the same
round-trip against an **iPad**: open the note from iCloud in Obsidian, add `>[!ai]` callouts, pull them back. Syncthing
stays in use, so this is an added transport, not a migration.

Nothing currently covers this. The `publish` skill reaches iCloud but always renders markdown to PDF (an explicit
decision — its v1.4 passthrough allowlist is `.pdf/.pptx/.key/.docx` and deliberately excludes `.md`), and it is
push-only by contract. `offdesk` has the right semantics — verbatim `.md`, frontmatter merge, callout pull-back — but
its vault root is a single path. Investigation confirmed Syncthing is nowhere in the skill's mechanics: push is a
frontmatter merge plus a write to `$VAULT_ROOT/<slug>/<file>.md`, pull is a grep over the same directory. Syncthing
appears only in prose. The transport is just "which directory syncs," so a second one is additive.

### What changed

**Transport model.** Two named transports, `syncthing` and `icloud`, using the same vocabulary `publish` uses for
providers: one env var per transport, a table in `references/`, glob resolution with a hard-fail that never auto-picks.

**Root resolution.** Per transport, first match wins:

| Transport | Resolution order |
|---|---|
| `icloud` | `OFFDESK_ICLOUD_VAULT` → glob `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/*` |
| `syncthing` | `OFFDESK_SYNCTHING_VAULT` → `OFFDESK_OBSIDIAN_VAULT` (back-compat alias) → `~/Obsidian/offdesk` |

The alias is mandatory, not a courtesy: `OFFDESK_OBSIDIAN_VAULT` is already set in the user's profile with seven project
folders behind it. It keeps working silently, with no deprecation warning. Glob resolution follows the `publish` rules
exactly — 0 matches hard-fails naming the env var, exactly 1 is used, more than 1 hard-fails listing the candidates and
never guesses (the Obsidian iOS vault name is user-chosen, so multiple vaults are plausible).

**Push routing — `syncthing` is the default.** All eight existing trigger phrases keep their current meaning, so
established muscle memory and the seven existing project folders are untouched. `icloud` requires an explicit marker.

**Trigger vocabulary — anchored on "offdesk", never on the device.** A device-named phrase would collide with `publish`,
which already owns "read on ipad" / "почитаю на айпаде" for its icloud provider. The two skills do different things
(rendered PDF into `Reading/`, push-only, versus verbatim `.md` into an Obsidian vault with pull-back), so the utterance
must not be ambiguous. No offdesk phrase may contain `ipad` / `айпад` / `books` / `книги`; no publish phrase may contain
`offdesk` / `оффдеск`. This is enforced by a test that greps both SKILL.md files and fails on a non-empty intersection.

```text
syncthing (default — the existing eight phrases, unchanged):
  EN: "send to offdesk", "send to phone for review", "review later", "check later"
  RU: "положи это в offdesk", "положи это в оффдеск", "посмотрю позже", "проверю позже"

icloud (new — always explicitly marked):
  EN: "send to offdesk icloud", "offdesk icloud", "offdesk on icloud"
  RU: "положи в offdesk icloud", "положи в оффдеск айклауд", "оффдеск айклауд"
```

**Layout is unchanged and symmetric across transports** — `<vault-root>/<project-slug>/<filename>.md`. No `Reading/`
wrapper; that is `publish` vocabulary for a different job. The existing slug-collision rule (suffix
`sha1(project-root)[:6]`) applies unchanged.

**iCloud materialization.** An earlier draft made `brctl download` a mandatory pre-step for pull. That was dropped as
over-engineering: on this macOS version an evicted iCloud file is a *dataless file under its own name*, and an ordinary
read materializes it transparently, so grep works — it may simply block while downloading. Note that
`defaults read com.apple.bird optimize-storage` returns `1` on this machine, so eviction is permitted; "everything is
local" is not guaranteed. The one narrow failure that survives is a legacy `.<name>.md.icloud` stub, where the file is
absent under its own name and grep silently reports no annotations. That is closed after the fact rather than up front:
**only when pull returns zero annotations**, check the project folder for `*.icloud` stubs and report unmaterialized
files instead of "no feedback". Search scope stays pinned to `<vault>/<slug>/` — a `find` across the whole iCloud tree
was measured at over two minutes before being killed.

**Pull spans both vaults by default.** Annotations are made away from the desk, and remembering which device they were
left on is exactly the friction the skill exists to remove. Cost is two directory-scoped greps. An explicit phrase
("check offdesk icloud") narrows to one transport. Results are merged and each line is tagged with its transport and
the file's mtime — the mtime directly answers "has iCloud propagated yet, or did I come back too early":

```text
[icloud, 2h ago]     design/foo.md:42 — is this still true after the split?
[syncthing, 3d ago]  design/bar.md:17 — check the numbers here
```

The same source file annotated in both vaults yields **two independent annotation sets, not duplicates** — they were
written on different devices. Group by source file, show both, do not deduplicate.

**Frontmatter gains `offdesk-transport: icloud|syncthing`** on push, so a vault copy is self-describing and stays
correct if a vault later moves. The Cleanup section needs no edit: it already strips all `offdesk-*` keys by wildcard.

**Push targets exactly one transport.** No push-to-both — it would fan out state that later has to be merged back.

**A resolver module is introduced.** The skill currently has no resolver by design ("performs file copy, frontmatter
merge, and grep directly — no compiled CLI tool"), which was fine for one hardcoded vault. Two transports add env
precedence, glob expansion with a 0/1/>1 contract, and trigger mapping — rules that are easy to get subtly wrong in
prose and impossible to regression-test. `scripts/transports.py` mirrors `publish`'s `scripts/providers.py`, whose test
suite supplies the shape to copy.

**Versioning.** `obsidian` plugin `0.2.1 → 0.3.0` — minor: additive transport plus broadened triggers, nothing removed.

**Delivered as one task.** Splitting the resolver from the docs would leave the skill advertising a transport it cannot
resolve.

### Implementation checklist

- Add `plugins/obsidian/skills/offdesk/scripts/transports.py` — transport constants, env precedence, glob resolution,
  trigger mapping; modelled on `plugins/publish/skills/publish/scripts/providers.py`.
- Extend `merge-frontmatter.py` with `--offdesk-transport`.
- Rework `SKILL.md`: frontmatter triggers, transport section, push routing, pull-both semantics, zero-result stub check,
  `offdesk-transport` key. Replace "Syncthing-synced" framing with transport-neutral wording.
- Add `references/transports.md` — table, resolution order, trigger mapping.
- Add an iCloud section to `references/setup.md` — create the vault in Obsidian on iOS, where it lands on the Mac, which
  env var to set.
- Add `tests/test_transports.py` and `tests/test_trigger_collisions.py` (offdesk has no tests today).
- Update `README.md` `### offdesk`, `plugins/obsidian/.claude-plugin/plugin.json` (0.3.0 + description), and the
  `obsidian` entry in `.claude-plugin/marketplace.json`.

### Distilled for ralph-task

**Direction:** Option B — multi-transport `offdesk`: add an `icloud` transport alongside the existing Syncthing vault,
using the named-transport vocabulary `publish` already uses for providers, so `.md` round-trips through an Obsidian
vault on iCloud for iPad review.

**Locked decisions (with rationale):**

- **Two named transports, `syncthing` + `icloud`, one env var each.** *Rationale:* mirrors `publish`'s provider model,
  which already solved env-vs-glob resolution and multi-match ambiguity in this same repo.
- **`icloud` root defaults to the glob `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/*`.** *Rationale:* the
  Obsidian iOS vault name is chosen by the user, so the path cannot be a literal.
- **Glob contract: 0 → hard-fail naming the env var; 1 → use; >1 → hard-fail listing candidates, never auto-pick.**
  *Rationale:* byte-identical to the `google-drive` / `onedrive` rule; silently guessing a vault would write notes into
  the wrong one.
- **`OFFDESK_OBSIDIAN_VAULT` remains a working alias for `syncthing`, ahead of the literal default and behind
  `OFFDESK_SYNCTHING_VAULT`.** *Rationale:* it is already set in the user's profile with seven project folders behind it.
- **`syncthing` is the default transport; all eight existing phrases keep their meaning.** *Rationale:* preserves muscle
  memory and existing folders; `icloud` is opt-in per push.
- **offdesk triggers are anchored on "offdesk"/"оффдеск" and must never contain `ipad`/`айпад`/`books`/`книги`.**
  *Rationale:* those belong to `publish`'s icloud provider, which renders PDF and is push-only — a shared utterance
  would be unresolvable.
- **Layout stays `<vault-root>/<project-slug>/<filename>.md` for both transports.** *Rationale:* symmetric and already
  proven; `Reading/` is `publish` vocabulary for a different job.
- **Pull spans both vaults by default, tagged with transport and mtime; an explicit phrase narrows to one.**
  *Rationale:* the user should not have to recall which device an annotation was left on; mtime exposes sync lag.
- **No `brctl` on the happy path; only on a zero-annotation result, check for `*.icloud` stubs and report
  unmaterialized files.** *Rationale:* dataless files materialize transparently on read, so a pre-download is wasted
  work; the stub case is the only silent-miss path and is cheaper to catch after the fact.
- **Pull search scope is pinned to `<vault>/<slug>/`.** *Rationale:* a `find` over the whole iCloud tree was measured at
  >2 minutes.
- **New frontmatter key `offdesk-transport`; Cleanup unchanged.** *Rationale:* makes a vault copy self-describing; the
  existing `offdesk-*` wildcard already strips it.
- **One task, `obsidian` plugin bumped `0.2.1 → 0.3.0`.** *Rationale:* additive feature; splitting would ship a skill
  advertising a transport it cannot resolve.
- **All artifacts authored in English**, with RU trigger phrases kept verbatim as data.

**Scope cuts:**

- No push to both transports in one invocation.
- No `brctl download` on the pull happy path.
- No deduplication of annotations across vaults.
- No migration of the seven existing project folders out of the Syncthing vault.
- No deprecation warning or removal for `OFFDESK_OBSIDIAN_VAULT`.
- No transports beyond these two (no dropbox/box/etc.).
- No changes to `publish`'s triggers, providers, or behaviour.
- No `Reading/`-style subfolder inside the vault.

**Acceptance criteria (sketch):**

- `transports.py` resolves the `syncthing` root with precedence `OFFDESK_SYNCTHING_VAULT` → `OFFDESK_OBSIDIAN_VAULT` →
  `~/Obsidian/offdesk`, proven by tests covering all three tiers.
- `transports.py` expands the `icloud` glob and returns the single match; 0 matches raises an error naming
  `OFFDESK_ICLOUD_VAULT`; >1 raises an error listing every match.
- Each of the eight existing offdesk phrases resolves to `syncthing`; each new icloud phrase resolves to `icloud`.
- A test asserts the offdesk and publish trigger sets are disjoint and that no offdesk phrase contains
  `ipad`/`айпад`/`books`/`книги`.
- `merge-frontmatter.py` accepts `--offdesk-transport` and writes an `offdesk-transport` key without disturbing existing
  frontmatter keys.
- `SKILL.md` documents both transports, the syncthing default, pull-across-both with transport+mtime tagging, and the
  zero-result `.icloud` stub check; no remaining claim that the vault is Syncthing-only.
- `references/transports.md` exists with the transport table, resolution order, and trigger mapping.
- `references/setup.md` has an iCloud section covering vault creation on iOS, the resulting Mac path, and the env var.
- `README.md` `### offdesk` names both transports with at least three example trigger phrases.
- `plugins/obsidian/.claude-plugin/plugin.json` is `0.3.0`, and the `obsidian` entry in `.claude-plugin/marketplace.json`
  describes both transports.
- `uv run ruff check .` passes and `uv run pytest` shows no new failures.

**Implementation checklist:**

- Write `scripts/transports.py` modelled on `publish`'s `providers.py`.
- Add `--offdesk-transport` to `merge-frontmatter.py`.
- Rework `SKILL.md` (frontmatter, transports, push routing, pull semantics, stub check, transport-neutral prose).
- Write `references/transports.md`; add the iCloud section to `references/setup.md`.
- Write `tests/test_transports.py` and `tests/test_trigger_collisions.py`.
- Update `README.md`, `plugin.json` (0.3.0), and `.claude-plugin/marketplace.json`.
- Run `uv run ruff check .` and `uv run pytest`.
