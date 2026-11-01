---
id: TASK-56
title: 'Rename skills to the arch-drawio, ak-style and core-style scheme'
status: In Progress
assignee: []
created_date: '2026-11-01T20:03:00Z'
updated_date: '2026-11-01 20:09'
labels:
  - 'feature:skill-renaming'
dependencies: []
priority: high
ordinal: 56000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Skill names mix verb, medium and artifact suffixes (arch-draw, arch-slide, arch-style), flip prefix order (arch-draw vs pptx-arch-style), and share the arch- prefix across two marketplaces with different meanings: generic skills in this public repo and the bank's ABS 2030 standards in the separate agent-skills repo. One rule fixes it: the prefix says whose standard, the suffix says the medium or artifact. The bank-repo renames (arch-puml -> abs-puml, arch-slide -> abs-slide) are advised separately and are NOT part of this task.

## Direction

Full renaming scheme: arch-draw -> arch-drawio (architect plugin), pptx-arch-style -> ak-style and pptx-core-style -> core-style (presentation plugin); pure renames with transition trigger phrases.

## Locked decisions (with rationale)

- **One rule:** prefix = whose standard (arch- generic here, abs- bank there), suffix = medium/artifact; deck styles named by audience (ak-style, core-style). *Rationale:* ends the verb/medium/artifact suffix mix and the arch- collision across the two marketplaces.
- **Styles never appear in names:** new looks land as style-<name>.md presets inside the medium skill; a style with its own tooling becomes a new <audience>-style skill. *Rationale:* the scheme must survive future styling without renames.
- **Old names remain as trigger phrases** in each renamed skill's description. *Rationale:* existing invocations keep matching; removal later is a patch bump.
- **Major version bumps:** architect 0.2.0 -> 1.0.0, presentation -> 1.0.0. *Rationale:* the repo's SemVer rule names renames as major.
- **Order:** this task precedes the arch-pptx implementation task, which references the final names.

## Scope cuts

- No ak-style move to the bank repo; no content changes to any skill; arch-describe and pptx-compare unchanged; bank-repo renames advised only.

## Files

- `plugins/architect/skills/arch-draw/` (exists) - renamed into the first target directory below
- `plugins/presentation/skills/pptx-arch-style/` (exists) - renamed into the second target directory below
- `plugins/presentation/skills/pptx-core-style/` (exists) - renamed into the third target directory below
- `plugins/architect/.claude-plugin/plugin.json` (exists) - version 0.2.0 -> 1.0.0
- `plugins/presentation/.claude-plugin/plugin.json` (exists) - version -> 1.0.0
- `.claude-plugin/marketplace.json` (exists) - entries updated if they enumerate skill names
- `README.md` (exists) - skill section headings and bodies, tree lines, /plugin install comment lines

Target directories:

```text
plugins/architect/skills/arch-drawio/
plugins/presentation/skills/ak-style/
plugins/presentation/skills/core-style/
```

## Implementation checklist

- git mv plugins/architect/skills/arch-draw plugins/architect/skills/arch-drawio; update its SKILL.md name and description (add the old name as a quoted trigger phrase) and any self-references in references/.
- git mv plugins/presentation/skills/pptx-arch-style plugins/presentation/skills/ak-style; same SKILL.md and self-reference updates (scripts, tests, references).
- git mv plugins/presentation/skills/pptx-core-style plugins/presentation/skills/core-style; same.
- Bump architect and presentation plugin.json to 1.0.0; update their descriptions if they enumerate skill names.
- Update .claude-plugin/marketplace.json entries if they enumerate skill names.
- Update README.md: section headings and bodies, tree lines, install comment lines.
- Repo-wide grep for arch-draw, pptx-arch-style and pptx-core-style; fix every live-code or live-doc hit except transition trigger phrases and files under design/.
- uv run ruff check . && uv run pytest.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The architect skill lives at plugins/architect/skills/arch-drawio with SKILL.md name arch-drawio, and its description still matches the old name arch-draw as a quoted trigger phrase; references/ carry no stale self-references
- [x] #2 plugins/presentation/skills/ak-style/ holds the former pptx-arch-style with SKILL.md name ak-style, the old name pptx-arch-style as a quoted trigger phrase, and no stale self-references in scripts, tests or references
- [x] #3 plugins/presentation/skills/core-style/ holds the former pptx-core-style with SKILL.md name core-style and the old name pptx-core-style as a quoted trigger phrase
- [x] #4 architect plugin.json is at version 1.0.0 and presentation plugin.json at 1.0.0, and python -m json.tool parses both plus .claude-plugin/marketplace.json
- [x] #5 README.md uses the new names in the skill section headings and bodies, the tree lines and the /plugin install comment lines
- [x] #6 A repo-wide grep for arch-draw, pptx-arch-style and pptx-core-style finds only the transition trigger phrases, files under design/, and this task file
- [x] #7 uv run ruff check . and uv run pytest pass with the repo's known baseline failure (test_helper_renders_canonical_decision_tree) excluded, at the moved test paths
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: git mv the three skill dirs; rewrite SKILL.md names + add quoted old names as trigger phrases; fix self-references in scripts/tests/references/assets; cross-refs in pptx-compare; bump both plugin.json to 1.0.0; update marketplace.json + README + .gitignore; leave historical backlog task files untouched (records, not live docs); ruff + pytest.

Note on AC #6: the literal grep also hits historical backlog task files (task-1/2/21-31/43-46) and design/; those are immutable records of past work, not live code or live docs, so per the implementation checklist (fix live-code/live-doc hits only) they were left untouched. Outside design/ and backlog/, the only remaining hits are the three quoted transition trigger phrases in the renamed SKILL.md descriptions. pytest: 448 passed, 1 failed = known baseline test_helper_renders_canonical_decision_tree (vendored node_modules absent).

Commit: `0e9e2fd` - task-56: rename arch-draw to arch-drawio, pptx-arch-style to ak-style, pptx-core-style to core-style; bump both plugins to 1.0.0
<!-- SECTION:NOTES:END -->
