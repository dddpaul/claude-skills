# Skill renaming: one naming rule across both skill repos

## Architecture decision

Adopt one rule everywhere: **the prefix says whose standard, the suffix says the medium or artifact.** `arch-*` = generic architecture skills in the public repo; `abs-*` = the bank's ABS 2030 standards in the agent-skills repo; `ak-*` / `core-*` = deck styles, named by audience. Style names never appear in skill names: a new look is a preset file inside the medium skill (`style-<name>.md`), promoted to its own `<audience>-style` skill only when it carries its own tooling.

## Components / flows

Renames in the public repo (this one):

| Now | Becomes | Reason |
|-----|---------|--------|
| `arch-describe` | `arch-describe` | unchanged: text in, text out, no ambiguity |
| `arch-draw` | `arch-drawio` | suffix = medium; "draw" would clash with the drawing skill `arch-pptx` |
| new skill | `arch-pptx` | medium-named, so future style presets need no rename |
| `pptx-arch-style` | `ak-style` | audience (AK committee) + artifact; takes "arch" out of the middle |
| `pptx-core-style` | `core-style` | parallel to `ak-style` |
| `pptx-compare` | `pptx-compare` | unchanged: a tool, name is medium + verb |

Renames in the agent-skills repo (bank-internal; advised, executed there):

| Now | Becomes | Reason |
|-----|---------|--------|
| `arch-puml` | `abs-puml` | the `abs-` prefix separates bank standards from generic `arch-*` |
| `arch-slide` | `abs-slide` | ends the collision with the PPTX diagram skill `arch-pptx` |

Doc-parity surfaces per public-repo rename (each task's Files section carries these):

- The skill directory `plugins/<plugin>/skills/<old>/` → `<new>/`, including `scripts/` and `tests/` sub trees (pptx-arch-style's tests move with it; the known baseline-failing test keeps failing at its new path).
- The SKILL.md frontmatter `name` and `description`; the description keeps the old name as a quoted trigger phrase ("use when asked for `arch-draw` or draw.io diagrams") so existing habits keep matching during the transition.
- References and scripts that self-reference the old name (a repo-wide grep for `arch-draw`, `pptx-arch-style`, `pptx-core-style` finds them).
- The owning plugin's `.claude-plugin/plugin.json` version bump: renames are major per the repo's SemVer rule — `architect` 0.2.0 → 1.0.0 (this rename), `presentation` → 1.0.0 (covers both of its renames in one bump).
- `.claude-plugin/marketplace.json` entry description, if it enumerates skill names.
- Root `README.md`: the `### <skill>` section heading and body, the tree lines, the `/plugin install` comment lines.
- The memory note that records the baseline pytest failure by its `pptx-arch-style` path — updated when that rename lands.

Ordering: the renames run **before** the arch-pptx implementation task is created, so the new skill's fences and the distilled task block reference final names. `design/arch-pptx-brainstorm.md` carries a dated addendum mapping its neighbour names to the new ones rather than rewriting its tables.

## Scope cuts

- No move of `pptx-arch-style` to the bank repo (the structural-split option was declined): it stays here under `ak-style`, public content included.
- No content changes to any style guide or the studio preset: pure renames plus transition trigger phrases.
- `arch-describe` and `pptx-compare` keep their names.
- The bank-repo renames are advised only; this repo's tooling never touches that repo, and no bank host or repo URL appears in any public file.
- Old names stay in descriptions as trigger phrases indefinitely, until they grate; removing them later is a patch bump, not a task.

## Open questions

- None blocking. The SemVer majors follow the repo rule as written; if 0.x minor-as-breaking is preferred instead, say so before the task is created.

## Hand-off

Next: `ralph-task` with `feature=skill-renaming` to create the public-repo rename task from the Distilled block below, after explicit design sign-off. The bank-repo checklist is executed by the user there.

## Distilled for ralph-task

**Direction:** Full renaming scheme — `arch-draw` → `arch-drawio` (architect plugin), `pptx-arch-style` → `ak-style` and `pptx-core-style` → `core-style` (presentation plugin); pure renames with transition trigger phrases.

**Locked decisions (with rationale):**

- **One rule:** prefix = whose standard (`arch-` generic here, `abs-` bank there), suffix = medium/artifact; deck styles named by audience (`ak-style`, `core-style`). *Rationale:* ends the verb/medium/artifact suffix mix and the `arch-` collision across the two marketplaces.
- **Styles never appear in names:** new looks land as `style-<name>.md` presets inside the medium skill; a style with its own tooling becomes a new `<audience>-style` skill. *Rationale:* the scheme must survive future styling without renames.
- **Old names remain as trigger phrases** in each renamed skill's description. *Rationale:* existing invocations keep matching; removal later is a patch bump.
- **Major version bumps:** `architect` 0.2.0 → 1.0.0, `presentation` → 1.0.0. *Rationale:* the repo's SemVer rule names renames as major.
- **Order:** this task precedes the arch-pptx implementation task, which references the final names.

**Scope cuts:**

- No `ak-style` move to the bank repo; no content changes; `arch-describe` and `pptx-compare` unchanged; bank-repo renames advised only.

**Acceptance criteria (sketch):**

- Skill directories, SKILL.md `name` fields and README sections read `arch-drawio`, `ak-style`, `core-style`; both plugin manifests bumped to 1.0.0; every JSON file parses.
- Each renamed description still matches its old name as a quoted trigger phrase.
- A repo-wide grep for `arch-draw`, `pptx-arch-style`, `pptx-core-style` finds only: the transition trigger phrases, the design history docs (`design/*.md`), and this task file.
- `uv run ruff check .` and `uv run pytest` pass with the repo's known baseline failure excluded, at the moved test paths.

**Implementation checklist:**

- `git mv plugins/architect/skills/arch-draw plugins/architect/skills/arch-drawio`; update its SKILL.md name/description (+ old-name trigger) and any self-references in `references/`.
- `git mv plugins/presentation/skills/pptx-arch-style .../ak-style` and `.../pptx-core-style .../core-style`; same SKILL.md and self-reference updates (scripts, tests, references).
- Bump `architect` and `presentation` `plugin.json` to 1.0.0; update descriptions if they enumerate skills.
- Update `.claude-plugin/marketplace.json` entries if they enumerate skill names.
- Update root `README.md`: section headings and bodies, tree lines, install comment lines.
- Repo-wide grep for the three old names; fix every live-code or live-doc hit except transition triggers and design history.
- Update the baseline-failure memory note to the moved test path.
- `uv run ruff check . && uv run pytest`.
