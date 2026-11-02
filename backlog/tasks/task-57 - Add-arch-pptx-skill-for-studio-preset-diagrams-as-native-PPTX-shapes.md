---
id: TASK-57
title: Add arch-pptx skill for studio-preset diagrams as native PPTX shapes
status: In Progress
assignee: []
created_date: '2026-11-02T09:16:00Z'
updated_date: '2026-11-02 09:46'
labels:
  - 'feature:arch-pptx'
dependencies: []
priority: medium
ordinal: 57000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**Direction:** Option A — new skill `plugins/architect/skills/arch-pptx/` that renders studio-preset architecture diagrams as native, editable PPTX shapes through a shipped helper library, with an embedded draw.io PNG as the documented fallback. Includes the locked boundary against the bank-adjacent `arch` plugin neighbours (final names).

**Locked decisions (with rationale):**

- **Native shapes are the primary path; PNG embed the fallback:** the helper ports the preset to python-pptx so slides stay editable in PowerPoint, and `add_png` places a 2× draw.io export full-bleed when pixel-exactness or draw.io editing matters more. *Rationale:* the user chose both paths; native matches the repo's python-pptx toolchain.
- **Diagram kinds only:** zones (external/internal/repo/fence), boxes (plain/secret/gate), group, chip, data store, person, title, note; all four edge kinds plus async and two-way. *Rationale:* full preset parity minus BPMN, which stays in `arch-drawio`.
- **Helper + bespoke script, no DSL:** the skill ships tokens and primitives; each request gets a small build script that places elements on the 10px grid. *Rationale:* best layout quality; matches how the pptx skills work.
- **1px = 9525 EMU on a 1280×720px canvas:** `arch-drawio` coordinates, gaps and radii port unchanged; the helper converts px→pt for strokes and font sizes. *Rationale:* the studio geometry carries over 1:1.
- **Translations documented in the reference:** semibold→bold, letter-spacing via `spc`, dashes via `custDash` (`5 4`, `3 4`, `4 3`), arrowheads via `tailEnd`, edge labels as text boxes. *Rationale:* PPTX lacks these draw.io features natively; the reference records each mapping.
- **Edges have no auto-routing:** anchors and waypoints are explicit; "no edge through a box" is the author's job, caught in the QA render. *Rationale:* reasoned placement beats generic routing for one-off diagrams.
- **Home and name:** `plugins/architect/skills/arch-pptx/`, next to `arch-drawio`; architect plugin 1.0.0→1.1.0 (minor: new skill). *Rationale:* `arch-drawio` stays the studio preset's source of truth; the subject is diagramming.
- **Fonts:** IBM Plex Sans/Mono/Condensed required and listed as a precondition. *Rationale:* the preset's type; python-pptx cannot embed fonts.
- **Bank-standard requests route away:** `arch-pptx` carries no bank layer model — no fixed layers, no service-to-layer map, no channel bands, no ABS statuses or block marks — and fences `abs-slide`, `abs-puml`, `ak-style` and `arch-drawio` by name in its SKILL.md description. A request shaped like a bank layer landscape, a topic × function matrix, or an AS IS / TO BE systems map routes to `abs-slide` even when the user says "studio". *Rationale:* four PPTX/diagram-producing skills already exist across the two repos; without explicit fences the triggers blur.
- **The studio look is not a bank standard:** `arch-pptx` positions itself as the personal/generic diagram look; a bank AK deliverable must use `ak-style` or `abs-slide`. SKILL.md says so in one line.
- **No bank-internal identifiers in any arch-pptx file:** no bank host name, no internal repo URL, no layer-model vocabulary anywhere in the skill (public-repo rule).
- **Mechanics precedent, content contract different:** the resemblance to `abs-slide`'s shape (hidden yaml + builder + PNG check) is noted in the reference as prior art only; nothing is shared at runtime, and the two skills never import from each other.

**Scope cuts:**

- BPMN kinds (start/end/error events, tasks, exclusive gateway) — stay draw.io-only in `arch-drawio`; add by addendum if a slide needs them.
- No auto-layout, no YAML DSL — Claude places elements on the grid in the per-request build script.
- No legend component, no dark mode, no font embedding (PPTX via python-pptx cannot embed fonts).
- No draw.io→PPTX conversion; the fallback is a PNG image on the slide.
- Codex-side packaging: none; Claude-only skill.
- Contributing the studio preset to the bank-adjacent `arch` plugin's repo — a separate decision there, out of scope here.

**Acceptance criteria (sketch):**

- `plugins/architect/skills/arch-pptx/` exists with `SKILL.md` (studio-only triggers, boundary fences naming `abs-slide`, `abs-puml`, `ak-style`, `arch-drawio`, font precondition, one-line "bank-standard deliverables" note), `references/style-studio-pptx.md`, `scripts/studio_pptx.py`, `tests/`.
- The helper reproduces the preset: the eleven tokens exact; per-kind fill/stroke/radius/font conversions; `custDash` and `tailEnd` XML present.
- A sample deck (zone + box + chip + store + person + all four edge kinds) builds, re-opens with python-pptx, and QA-renders to PNG with no overlaps.
- `add_png` embeds a provided PNG full-bleed on a slide.
- `references/style-studio-pptx.md` contains no bank layer model vocabulary and no ABS tokens — preset tables only.
- A grep of the skill's files finds no bank host, internal repo URL, or layer-model vocabulary.
- `uv run ruff check .` passes; `uv run pytest` passes with the repo's known baseline failure excluded.
- Version and docs: architect `plugin.json` at 1.1.0 with an updated description; `.claude-plugin/marketplace.json` architect entry updated; root `README.md` gets a `### arch-pptx` subsection (including the one-line boundary-table sentence), tree entries and install line updated.

**Implementation checklist:**

- Write `scripts/studio_pptx.py`: tokens, px→EMU/pt conversions, `Diagram`, `zone`/`box`/`chip`/`store`/`person`/`group`/`title`/`note`/`edge`/`add_png`.
- Write `references/style-studio-pptx.md`: the port of the studio style reference with the PPTX translation table, free of bank layer-model vocabulary.
- Write `SKILL.md`: frontmatter triggers and the four neighbour fences (`abs-slide`, `abs-puml`, `ak-style`, `arch-drawio`), the bank-standard-deliverables note, preconditions, the build → QA loop, the fallback section.
- Write the tests: token integrity, conversions, per-kind properties, XML checks, smoke build-and-reopen.
- Build and QA-render the sample diagram; iterate until clean.
- Bump the architect plugin to 1.1.0, update its description, the marketplace entry and the root README (new subsection with the boundary sentence).
- `uv run ruff check . && uv run pytest`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 plugins/architect/skills/arch-pptx/ exists with SKILL.md naming studio-only triggers and fencing abs-slide, abs-puml, ak-style, and arch-drawio by name, plus a font precondition and a one-line bank-standard-deliverables note
- [ ] #2 plugins/architect/skills/arch-pptx/references/style-studio-pptx.md exists, reproduces the eleven studio tokens exactly, and contains no bank layer-model vocabulary or ABS tokens
- [ ] #3 plugins/architect/skills/arch-pptx/scripts/studio_pptx.py implements the Diagram class with zone, box, chip, store, person, group, title, note, edge (default/deny/ok/gate x plain/async/two-way), and add_png
- [ ] #4 A sample deck containing a zone, a box, a chip, a store, a person, and all four edge kinds builds, re-opens cleanly with python-pptx, and QA-renders via LibreOffice to PNG with no shape overlaps
- [ ] #5 add_png embeds a provided PNG full-bleed on a slide
- [ ] #6 plugins/architect/skills/arch-pptx/tests/ hermetically verifies token integrity, px-to-EMU/pt conversions, per-kind shape properties, and the custDash/tailEnd XML output
- [ ] #7 grep across plugins/architect/skills/arch-pptx/ finds no bank host name, internal repo URL, or layer-model vocabulary
- [ ] #8 uv run ruff check . passes and uv run pytest passes with the repo's known baseline failure excluded
- [ ] #9 plugins/architect/.claude-plugin/plugin.json is bumped to 1.1.0 with an updated description, the architect entry in .claude-plugin/marketplace.json is updated, and root README.md gets a new arch-pptx subsection (with the boundary sentence), tree entries, and an updated install line
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: helper studio_pptx.py (tokens, px/pt conversions, Diagram with all preset kinds, freeform edges with custDash/tailEnd, add_png, qa() layout checks); sample_diagram.py; reference port; SKILL.md with four fences; hermetic tests incl. boundary grep; QA render via LibreOffice AppImage (no system soffice; Plex fonts installed to ~/.local/share/fonts); bump architect to 1.1.0 + marketplace + README.
<!-- SECTION:NOTES:END -->
