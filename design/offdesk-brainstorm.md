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
