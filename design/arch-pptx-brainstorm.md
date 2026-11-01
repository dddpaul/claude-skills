# Arch-pptx: architecture diagrams as PPTX slides in the studio preset

## Architecture decision

A new skill `plugins/architect/skills/arch-pptx/` renders studio-preset architecture diagrams as **native, editable PPTX shapes** through a shipped helper library (`scripts/studio_pptx.py`); Claude writes a small build script per diagram and QA-renders via LibreOffice → PNG. An embedded draw.io PNG render is the documented fallback path (chosen: both paths). The canvas is 16:9 at 13.33×7.5 in = 1280×720 px at 96 dpi, with 1 draw.io px = 9525 EMU, so arch-draw geometry (10px grid, 40/30px gaps, sizes, radii) ports 1:1.

## Components / flows

- `SKILL.md` — triggers ("architecture diagram in pptx/powerpoint", "studio slide", "diagram as pptx"); boundary fences: draw.io files → arch-draw, AK committee decks → pptx-arch-style, the bank's arch-slide standard → that skill; preconditions (Python 3.11+, IBM Plex Sans/Mono/Condensed installed); the build → QA-render loop; the fallback section.
- `references/style-studio-pptx.md` — the PPTX port of arch-draw's `style-studio.md`: the eleven-token palette verbatim, px→pt conversions (strokes 1.2→0.9, 1.5→1.125, 1.6→1.2, 2→1.5; fonts 13px→9.75pt, 11.5→8.625, 11→8.25, 10.5→7.875, 18→13.5), translation choices (semibold→bold, letter-spacing via `spc` XML, custom dashes via `custDash`, block arrowheads via `tailEnd`, edge labels as text boxes above the run).
- `scripts/studio_pptx.py` — a `Diagram` class over python-pptx, one function per preset kind: `zone` (external/internal/repo/fence), `box` (plain/secret/gate; subtitle or code line), `chip`, `store`, `person`, `group`, `title`, `note`, `edge` (default/deny/ok/gate × plain/async/two-way, explicit anchors + waypoints, label placement), `add_png` (fallback embed).
- `tests/` — hermetic pytest: token integrity, px→EMU/pt conversions, per-kind shape properties, `custDash`/`tailEnd` XML, a smoke build-and-reopen.
- QA loop (documented, not pytest): `libreoffice --headless --convert-to pdf` → `pdftoppm` → Read PNG → fix overlaps/overflow.
- Doc parity: `plugins/architect/.claude-plugin/plugin.json` 0.2.0→0.3.0 + description; `.claude-plugin/marketplace.json` architect entry description; root `README.md` (new `### arch-pptx` subsection, tree entries, install line "arch-describe + arch-draw + arch-pptx").

## Scope cuts

- BPMN kinds (start/end/error events, tasks, exclusive gateway) — stay draw.io-only in arch-draw; add by addendum if a slide needs them.
- No auto-layout, no YAML DSL — Claude places elements on the grid in the per-request build script.
- No legend component, no dark mode, no font embedding (PPTX via python-pptx cannot embed fonts).
- No draw.io→PPTX conversion; the fallback is a PNG image on the slide.
- Codex-side packaging: none; Claude-only skill.

## Open questions

- None blocking. A legend component can be added by addendum if diagrams repeatedly need one.

## Hand-off

Next: `ralph-task` with `feature=arch-pptx` to create the implementation task from the Distilled block below.

## Distilled for ralph-task

**Direction:** Option A — new skill `plugins/architect/skills/arch-pptx/` that renders studio-preset architecture diagrams as native, editable PPTX shapes through a shipped helper library, with an embedded draw.io PNG as the documented fallback.

**Locked decisions (with rationale):**

- **Native shapes are the primary path; PNG embed the fallback:** the helper ports the preset to python-pptx so slides stay editable in PowerPoint, and `add_png` places a 2× draw.io export full-bleed when pixel-exactness or draw.io editing matters more. *Rationale:* the user chose both paths; native matches the repo's python-pptx toolchain.
- **Diagram kinds only:** zones (external/internal/repo/fence), boxes (plain/secret/gate), group, chip, data store, person, title, note; all four edge kinds plus async and two-way. *Rationale:* full preset parity minus BPMN, which stays in arch-draw.
- **Helper + bespoke script, no DSL:** the skill ships tokens and primitives; each request gets a small build script that places elements on the 10px grid. *Rationale:* best layout quality; matches how the pptx skills work.
- **1px = 9525 EMU on a 1280×720px canvas:** arch-draw coordinates, gaps and radii port unchanged; the helper converts px→pt for strokes and font sizes. *Rationale:* the studio geometry carries over 1:1.
- **Translations documented in the reference:** semibold→bold, letter-spacing via `spc`, dashes via `custDash` (`5 4`, `3 4`, `4 3`), arrowheads via `tailEnd`, edge labels as text boxes. *Rationale:* PPTX lacks these draw.io features natively; the reference records each mapping.
- **Edges have no auto-routing:** anchors and waypoints are explicit; "no edge through a box" is the author's job, caught in the QA render. *Rationale:* reasoned placement beats generic routing for one-off diagrams.
- **QA loop outside pytest:** LibreOffice → PDF → PNG → Read → fix; pytest stays hermetic. *Rationale:* the repo's documented pptx toolchain; LibreOffice in pytest would be slow and flaky.
- **Home and name:** `plugins/architect/skills/arch-pptx/`, next to arch-draw; architect plugin 0.2.0→0.3.0 (minor: new skill). *Rationale:* arch-draw stays the studio preset's source of truth; the subject is diagramming.
- **Fonts:** IBM Plex Sans/Mono/Condensed required and listed as a precondition. *Rationale:* the preset's type; python-pptx cannot embed fonts.

**Scope cuts:**

- BPMN kinds, auto-layout, YAML DSL, legend component, dark mode, font embedding, draw.io→PPTX conversion, Codex-side packaging.

**Acceptance criteria (sketch):**

- `plugins/architect/skills/arch-pptx/` exists with `SKILL.md` (studio-only triggers, boundary fences, font precondition), `references/style-studio-pptx.md`, `scripts/studio_pptx.py`, `tests/`.
- The helper reproduces the preset: the eleven tokens exact; per-kind fill/stroke/radius/font conversions; `custDash` and `tailEnd` XML present.
- A sample deck (zone + box + chip + store + person + all four edge kinds) builds, re-opens with python-pptx, and QA-renders to PNG with no overlaps.
- `add_png` embeds a provided PNG full-bleed on a slide.
- `uv run ruff check .` passes; `uv run pytest` passes with the repo's known baseline failure excluded.
- Version and docs: architect `plugin.json` at 0.3.0 with an updated description; `.claude-plugin/marketplace.json` architect entry updated; root `README.md` `### arch-pptx` subsection, tree entries and install line updated.

**Implementation checklist:**

- Write `scripts/studio_pptx.py`: tokens, px→EMU/pt conversions, `Diagram`, `zone`/`box`/`chip`/`store`/`person`/`group`/`title`/`note`/`edge`/`add_png`.
- Write `references/style-studio-pptx.md`: the port of `style-studio.md` with the PPTX translation table.
- Write `SKILL.md`: frontmatter triggers and fences, preconditions, the build → QA loop, the fallback section.
- Write the tests: token integrity, conversions, per-kind properties, XML checks, smoke build-and-reopen.
- Build and QA-render the sample diagram; iterate until clean.
- Bump the architect plugin to 0.3.0, update its description, the marketplace entry and the root README.
- `uv run ruff check . && uv run pytest`.

---

## Addendum: boundary with the agent-skills project (added 2026-11-01)

### Why

The user's bank skills live in a separate repo, installed locally as the `alfa-agent-skills` marketplace (public design docs here refer to it generically; never name its host). Its `arch` plugin v0.4.0 ships two skills built on one shared bank layer model: `arch-puml`, the bank's ABS 2030 PlantUML sequence standard, and `arch-slide`, which builds a single PowerPoint slide laying out the functions and systems of one topic across the bank's architecture layers (layered slide, topic × function matrix, or AS IS / TO BE systems map, with block statuses, marks and a legend, from a hidden `<topic>.slide.yaml`). This repo already carries the third bank-adjacent surface, `presentation:pptx-arch-style` (the approved AK committee deck style). A skill that also produces "architecture slides in PPTX" needs its boundary against all of these written down, or the triggers will blur.

### What changed

The boundary is a two-axis line: **bank-standard materials vs. everything else**, and **landscape/matrix slide vs. free-form diagram**.

| Ask | Skill |
|-----|-------|
| Bank-layer landscape, topic × function matrix, AS IS / TO BE systems map as one slide | `arch-slide` (agent-skills `arch` plugin) |
| Bank ABS 2030 sequence diagram (PlantUML) | `arch-puml` (agent-skills `arch` plugin) |
| AK committee review deck (full style) | `pptx-arch-style` (this repo) |
| Draw.io diagram file, any style incl. studio | `arch-draw` (this repo) |
| Free-form architecture diagram as native PPTX shapes in the studio look | `arch-pptx` (this repo) |

Locked by this addendum:

- **arch-pptx implements no bank layer model.** It knows nothing about fixed layers, the service-to-layer map, channel bands, ABS statuses or block marks; those inputs have no place in its helper or reference. A request shaped like arch-slide ("systems by bank layers", "AS IS / TO BE map", "topic × functions") routes to arch-slide, even when the user says "studio".
- **The studio look is not a bank standard.** arch-pptx positions itself as the personal/generic diagram look; a bank AK deliverable must use pptx-arch-style or arch-slide. The SKILL.md says so in one line.
- **The description fences all four neighbours** in arch-pptx's frontmatter: arch-slide, arch-puml, pptx-arch-style, arch-draw — by skill name, generically where the neighbour is bank-internal. No bank host, repo URL or internal names appear in any arch-pptx file (public-repo rule).
- **Mechanics precedent, content contract different:** arch-slide's shape (hidden yaml + builder + PNG check) resembles arch-pptx's helper + QA loop; the resemblance is noted in the reference as prior art, nothing is shared at runtime — the two skills stay in different repos and never import from each other.
- **Out of scope:** contributing the studio preset to the agent-skills repo. If the bank later wants it, that is a separate decision there.

### Implementation checklist

- In `SKILL.md`: add the four fences to the description and a one-line "bank-standard deliverables" note in the body.
- In `references/style-studio-pptx.md`: no bank layer model, no ABS tokens — keep the preset tables only.
- Root README `### arch-pptx` subsection: one sentence on the boundary, matching the table above.

### Distilled for ralph-task

Extends the parent block below; everything else there is unchanged.

**Direction:** unchanged — Option A, plus the boundary against the agent-skills `arch` plugin.

**Locked decisions (with rationale):**

- **Bank-standard requests route away:** arch-pptx carries no bank layer model and fences `arch-slide`, `arch-puml`, `pptx-arch-style` and `arch-draw` by name in its description. *Rationale:* three PPTX-producing skills already exist; without explicit fences the triggers blur.
- **No bank-internal identifiers in arch-pptx files.** *Rationale:* this repo is public.

**Scope cuts:**

- Contributing the studio preset to the agent-skills repo.

**Acceptance criteria (sketch):**

- arch-pptx's SKILL.md names all four neighbours as fences, and a grep of the skill's files finds no bank host, repo URL or layer-model vocabulary.

**Implementation checklist:**

- Add the fences and the one-line bank note to `SKILL.md`; keep the reference free of layer-model vocabulary; one boundary sentence in the README subsection.

---

## Addendum: neighbour names renamed (added 2026-11-01)

The renaming scheme in `design/skill-renaming-brainstorm.md` renames the neighbours this design fences. Read throughout the sections above: `arch-draw` as `arch-drawio`, `arch-slide` as `abs-slide`, `arch-puml` as `abs-puml`, `pptx-arch-style` as `ak-style`. The implementation task distilled below uses the new names.
