# Plugin Marketplace Distribution

## Architecture decision

Repackage the `claude-skills` repo as a **single Claude Code plugin marketplace** (Option A: monorepo marketplace). The repo itself becomes the marketplace; domain-grouped plugins live as siblings under `plugins/`. Teammates register the marketplace once, then install whichever domain plugins they want via `/plugin install`.

- **Marketplace name:** `dddpaul-claude-skills` (owner-namespaced to avoid collisions with other `claude-skills` marketplaces a teammate might add).
- **Repo folder name:** stays `claude-skills` (no git remote rename).
- **Plugins (domains):** `architect` (arch-describe, arch-draw), `presentation` (pptx-core-style, pptx-arch-style). Future: `obsidian`, and more domains as they're added.
- **Per-plugin SemVer:** each `plugin.json` carries its own `version`, both start at `0.1.0`. Plugins ship independently.
- **No git tags / no staging branch:** marketplace follows `master`. Bumping `version` in `plugin.json` and merging to `master` *is* the release.

## Components / flows

### Repo layout (after migration)

```
claude-skills/
├── .claude-plugin/marketplace.json              # marketplace manifest (NEW)
└── plugins/
    ├── architect/
    │   ├── .claude-plugin/plugin.json           # NEW
    │   └── skills/
    │       ├── arch-describe/                   # moved from /arch-describe
    │       └── arch-draw/                       # moved from /arch-draw
    └── presentation/
        ├── .claude-plugin/plugin.json           # NEW
        └── skills/
            ├── pptx-core-style/                 # moved from /pptx-core-style
            └── pptx-arch-style/                 # moved from /pptx-arch-style
```

### Manifest contents

**`.claude-plugin/marketplace.json`**

```json
{
  "name": "dddpaul-claude-skills",
  "owner": { "name": "Pavel Derendyaev" },
  "plugins": [
    {
      "name": "architect",
      "source": "./plugins/architect",
      "description": "Architecture documentation and diagramming skills — describe IT systems with ASCII diagrams (arch-describe) and generate draw.io XML diagrams (arch-draw)."
    },
    {
      "name": "presentation",
      "source": "./plugins/presentation",
      "description": "Presentation style guides for the pptx skill — corporate core-style and architecture-committee arch-style."
    }
  ]
}
```

**`plugins/architect/.claude-plugin/plugin.json`** and **`plugins/presentation/.claude-plugin/plugin.json`** — both follow the same shape:

```json
{
  "name": "<architect|presentation>",
  "description": "<one-line>",
  "version": "0.1.0",
  "author": { "name": "Pavel Derendyaev" },
  "homepage": "https://github.com/dddpaul/claude-skills",
  "repository": "https://github.com/dddpaul/claude-skills",
  "license": "Apache-2.0"
}
```

### Migration flow

```bash
mkdir -p .claude-plugin
mkdir -p plugins/architect/.claude-plugin    plugins/architect/skills
mkdir -p plugins/presentation/.claude-plugin plugins/presentation/skills

git mv arch-describe    plugins/architect/skills/arch-describe
git mv arch-draw        plugins/architect/skills/arch-draw
git mv pptx-core-style  plugins/presentation/skills/pptx-core-style
git mv pptx-arch-style  plugins/presentation/skills/pptx-arch-style

# write the three manifest files
```

No internal-path rewrites required — every relative link inside a `SKILL.md` (e.g., `arch-draw/SKILL.md` → `references/cheatsheet.md`) stays relative to its skill directory.

### Teammate install / update / uninstall

```
/plugin marketplace add https://github.com/dddpaul/claude-skills
/plugin install architect@dddpaul-claude-skills
/plugin install presentation@dddpaul-claude-skills

/plugin marketplace update dddpaul-claude-skills   # later, to pull version bumps
/plugin uninstall architect@dddpaul-claude-skills  # if needed
```

### Maintainer flow per change

1. Branch off `master` (master-guard hook enforces this).
2. Edit skills, run lint/tests.
3. Bump `version` in only the `plugin.json` files whose plugins changed.
4. Commit, PR, merge to `master`. Teammates pick it up on next `marketplace update`.

### Versioning bump rules

- **patch** — content tweak inside a skill body, typo, clearer description.
- **minor** — added a new skill to the plugin, broadened triggers, added a script.
- **major** — renamed/removed a skill, narrowed triggers in a breaking way.

### README and CLAUDE.md updates

- README: replace the "Installation" section (drops the obsolete `claude config add skills` line and settings.json snippet); redraw the "Project Structure" tree; tag each skill summary with its plugin (`*Plugin: architect*`, `*Plugin: presentation*`); update "Creating New Skills" to show the `plugins/<domain>/skills/<name>/` template plus a note about registering new domains in `marketplace.json`.
- CLAUDE.md: one bullet under "Project-Specific" noting that skills live under `plugins/<domain>/skills/<name>/` and that adding a skill should bump the owning plugin's `version`.

## Scope cuts

- **Option B (one repo per domain)** — rejected. Cleanest isolation but forces teammates to `marketplace add` N times and complicates cross-domain shared content. Overkill for a small known team.
- **Option C (per-plugin git tags)** — rejected for now. Buys release reproducibility (pin `architect-v1.2.0` independently from `master`) but adds tag ceremony. Revisit when uncontrolled `master`-tracking becomes a problem.
- **Topic-themed marketplace name** (e.g., `archpres`, `cc-pack`) — rejected. Owner-prefixed `dddpaul-claude-skills` is collision-proof and self-describing.
- **Renaming skills to drop verbose prefixes** (e.g., `pptx-core-style` → `core-style` inside the `presentation` plugin) — rejected. Skill names appear in trigger phrases and skill-body cross-references; renaming has high churn for cosmetic gain.
- **Symlinking instead of moving skills** — rejected. Skills were never published, so a plain `git mv` is cleaner. `git mv` also preserves blame history.
- **Per-skill scripts / hooks / commands / agents** — none today; manifest schema supports them when needed.
- **Public discoverability / open-source polish** — out of scope per audience answer (small known team).

## Open questions

- **Author identity on `plugin.json`** — currently `Pavel Derendyaev` from git config. Re-confirm at implementation time vs. using the `dddpaul` handle.
- **Stable-release timing** — when does `architect` graduate from `0.x` to `1.0.0`? No deadline; bump when the trigger set is stable enough that breaking changes would warrant a heads-up to teammates.
- **Future `obsidian` plugin domain** — design is forward-compatible (just add a `plugins/obsidian/` and a marketplace.json entry), but the obsidian skill set itself is not specified yet.
- **Discovery / announcement to teammates** — out of scope here; README install instructions are enough for the small-team case. If the team grows, revisit.

## Hand-off

Next: `ralph-prd` to formalize as PRD, then `ralph-backlog` to generate tasks.
