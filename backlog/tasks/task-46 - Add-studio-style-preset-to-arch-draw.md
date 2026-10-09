---
id: TASK-46
title: Add studio style preset to arch-draw
status: To Do
assignee: []
created_date: '2026-10-09 05:38'
updated_date: '2026-10-09 07:12'
labels:
  - 'feature:arch-draw-studio'
dependencies: []
priority: medium
ordinal: 46000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

arch-draw only knows the generic draw.io look: pastel fills, #6c8ebf-style strokes, Courier New. The user wants
draw.io diagrams in the restrained style of a security-architecture diagram first drawn as an HTML artifact
("Credential Fence"): white boxes on lightly tinted zones, IBM Plex type, and colour kept for meaning only. Red marks
refused paths and boxes that hold secrets, amber marks gates and masking, and green marks the trusted path. This task
turns that style into a selectable arch-draw preset named `studio`, with the exact values below, so that later
diagrams can be drawn in it without re-deriving the style.

The preset must also carry ordinary architecture diagrams (Kafka, Camunda 8, C4 container level) and BPMN
process flows, so it adds the element kinds that the original figure did not need, in the same palette.

## Scope

In scope:
- A `studio` preset reference: palette, fonts and an mxGraph style string for every element kind in the Style spec
  below.
- A "Style presets" section in SKILL.md. It names the default (the existing palettes, unchanged) and says when to use
  `studio` (the user asks for "studio style" or "studio preset"). It links the reference. The frontmatter description
  mentions the preset.
- An example `.drawio` that redraws the "Who reads what" diagram (Example section) in the preset.
- The kinds in "Architecture extension" and "BPMN" below, in the same reference, and two more examples: a Kafka
  platform and an order process in BPMN.
- In the "Style presets" section: with studio, the patterns in SKILL.md (Kafka, Camunda 8, BPMN) are drawn with
  studio kinds instead of the default palette colours.
- One line about the preset in README's arch-draw section, the four new files added to README's Project Structure
  tree, and the architect plugin's version bumped from 0.1.1 to 0.2.0 (broadened trigger).

Out of scope:
- Changing the existing default palettes, the Complete Example, the checklist, cheatsheet.md or agent-prompt.md.
- Dark mode or adaptive colours. The dark palette below is recorded for a later task only and stays out of the
  preset files.
- pptx or any other output format, and the presentation plugin.
- Python generators, linters or tests for the preset.
- BPMN pools, lanes, intermediate and boundary events, other gateway types, and C4 notation beyond the person
  kind.

## Style spec (studio, light)

Palette:

| Token | Hex | Use |
|-------|-----|-----|
| panel | #ffffff | canvas background, box fill |
| fg | #18202b | box titles, default edges and their arrowheads |
| muted | #5a6575 | subtitles, zone labels, code labels |
| line | #c3ccd7 | plain box strokes, external and repo zone strokes |
| ext | #eaf0f8 | external zone fill |
| int | #e9f4ec | internal zone fill |
| repo | #f1efe9 | repository / data zone fill |
| deny | #b3362b | refused edges, secret-holding and deny boxes |
| gate | #a8681a | gate boxes, masked edges, fence zone, fence notes |
| ok | #2c7a4b | trusted edges, internal zone stroke |
| bg | #f4f6f8 | page around the diagram in the HTML original; optional draw.io page background |

Fonts:
- IBM Plex Sans (400 and 600) for all diagram text.
- IBM Plex Mono 400 for code labels (globs, commands, file names).
- IBM Plex Sans Condensed 600 for a diagram title, if there is one.
- In draw.io set `fontFamily=` plus a `fontSource=` Google Fonts URL (URL-encoded) so the diagram renders where the
  font is not installed.

Zones are rounded rectangles with a 10px corner radius. Their label sits top-left, 16px in and about 22px down:
10.5px, semibold, uppercase, muted, letter-spacing .08em.

| Zone | Fill | Stroke | Dash |
|------|------|--------|------|
| external | ext | line, 1 | 5 4 |
| internal | int | ok, 1 | solid |
| repo | repo | line, 1 | solid |
| fence | none | gate, 1 | 3 4; label bottom-left |

Boxes are rounded rectangles with a 6px corner radius and panel fill. Their text is left-aligned 16px in. The title
is 13px semibold fg. Under it comes a subtitle at 11.5px muted, or a code line at 11px IBM Plex Mono muted.

| Box | Stroke | Width |
|-----|--------|-------|
| plain | line | 1.2 |
| secret / deny | deny | 1.6 |
| gate | gate | 2 |

Edges are straight or orthogonal, with a filled triangle arrowhead in the edge colour, its tip at the line end. The
SVG marker is 7 units in stroke-width units, so it renders about 10.5px long and wide on a 1.5px edge. In draw.io
that is `endArrow=block;endFill=1`; start from `endSize=9` and check it against a render.

| Edge | Colour | Width | Meaning |
|------|--------|-------|---------|
| default | fg | 1.5 | neutral flow |
| deny | deny | 1.6 | a path that is refused |
| ok | ok | 1.6 | trusted, allowed path |
| gate | gate | 1.6 | passes a control; the output is masked |

Edge labels are 11.5px IBM Plex Sans in the edge colour. They sit just above the line, with no background box (on a
vertical run, just to its right, like "git"). A code-like edge label (a flag, a tool name) uses the 11px mono muted
style instead. A free note inside a fence uses the 11.5px label style in gate colour.

Notes on translating the SVG to draw.io (decide, then record the choice in the reference):
- Semibold: `fontStyle=1` is bold (700). Use that, or an html label with `font-weight:600`.
- Letter-spacing and the two-line box text need html labels (`html=1`).
- `fontSource` is per cell, and a font named only inside an html label is not loaded. So Mono text (a code line,
  a code label) is its own text cell with `fontFamily=IBM Plex Mono` and the Plex Mono `fontSource`.
- Corner radius: use `absoluteArcSize=1` with `arcSize`. draw.io reads `arcSize` as a diameter there, so 20, 16, 12
  and 8 give the 10, 8, 6 and 4px radii. Confirm by render when draw.io is available.
- Fractional stroke widths (1.2, 1.5, 1.6) are fine in `strokeWidth`.

Dark palette, recorded only (out of scope): bg #11151b, fg #e2e7ee, muted #98a3b2, line #394351, panel #19202a,
ext #172130, int #15241b, repo #221f19, deny #f0776b, gate #e5a347, ok #62c08a.

## Architecture extension (studio, light)

The original figure only needs zones, boxes and edges. Kafka, Camunda 8 or C4 container diagrams also need the kinds
below. They use only the eleven palette values and the fonts above.

| Kind | Shape | Fill | Stroke | Text |
|------|-------|------|--------|------|
| group | rounded rectangle, 8px radius | panel | line, 1 | zone-label style, top-left 16px in, about 22px down |
| data store | `shape=cylinder3`, `size=10` | panel | line, 1.2 (secret: deny, 1.6) | box title and subtitle, centred |
| chip | rounded rectangle, 4px radius, 30px high | panel | line, 1 | 11px IBM Plex Mono muted, centred |
| chip, deny | same as chip | panel | deny, 1 | 11px IBM Plex Mono in deny |
| person | pill (`arcSize=50`, not absolute) | panel | line, 1.2 | box title and subtitle, centred |

- A group sits inside a zone and holds boxes, chips and data stores: a Kafka or Zeebe cluster, a Kubernetes
  namespace. It is modelled on the artifact's white cards (panel fill, 1px line border, 8px radius).
- A chip is a topic, queue, partition or other named channel. It is modelled on the artifact's chips. A coloured
  chip colours its text and border together, as the artifact's amber chip does.
- A person is a user or role (C4 person). It sits outside the zones.

Two edge modifiers combine with any edge kind:

| Modifier | Style | Meaning |
|----------|-------|---------|
| async | `dashed=1;dashPattern=4 3` | asynchronous message or event (publishes, consumes) |
| two-way | `startArrow=block;startFill=1`, start size equal to the end size | replication, Raft, sync both ways |

Colour meaning in general diagrams, for the usage note in the reference:
- deny: refused or failing paths (rejections, dead letters, errors) and components that hold secrets.
- gate: components whose job in the diagram is to check or transform what passes (auth, policy, schema validation,
  redaction, rate limiting), and the edges leaving them.
- ok: trusted or explicitly allowed paths, when the diagram contrasts them with others.
- Everything else stays neutral. A name is not a kind: an API gateway or a Zeebe gateway is a gate box only when the
  diagram is about what it checks.
- Camunda 8: a group for the Zeebe cluster, boxes for brokers and gateways, two-way edges for Raft, data stores for
  Elasticsearch or OpenSearch. C4 container level: zones as system boundaries, boxes with a "[Container: tech]"
  subtitle, person for users.

## BPMN (studio, light)

| Element | Shape | Fill | Stroke | Label |
|---------|-------|------|--------|-------|
| start event | circle 40x40 | panel | fg, 1.5 | below, 11.5px muted, centred |
| end event | circle 40x40 | panel | fg, 3 | below, 11.5px muted, centred |
| error end event | circle 40x40 | panel | deny, 3 | below, 11.5px in deny, centred |
| task | rounded rectangle, 6px radius, 120x60 | panel | line, 1.2 | box title, centred |
| exclusive gateway | rhombus 40x40 | panel | fg, 1.5 | above, 11.5px muted, centred |

Sequence flows are default edges and message flows are async default edges. Branch labels ("yes", "no") are edge
labels; a branch that leads to an error end is a deny edge. Pools, lanes, intermediate and boundary events, and other
gateway types are out of scope. Events and the gateway are 40px so that their centres line up with a 60px task's
centre on the 10px grid.

## Example: "Who reads what"

Geometry comes from the original SVG (viewBox 980x440), as x,y then width x height. Snap it to arch-draw's 10px grid.
The grid rule covers waypoints and edge-label offsets too (the right-side route at x=965 becomes 970). The labels are
sample content for a public repo: keep them exactly as generic as below.

Zones:
- external "EXTERNAL MODELS": 20,20 230x210
- internal "INTERNAL MODEL": 20,334 230x92
- fence "FENCES · CLAUDE AND CODEX ONLY": 290,126 360x236, label bottom-left
- repo "PROJECT REPOSITORY": 690,20 270x320

Boxes (kind: title / subtitle):
- 40,56 190x56, plain: Claude Code / left pane · Anthropic
- 40,140 190x56, plain: Codex / right pane · OpenAI
- 40,362 190x50, plain: opencode / scratch pane · internal MCP
- 380,147 200x70, deny: File deny / Claude: deny rules + sandbox / Codex: permission profile
- 310,254 140x64, gate: Git guard / hook, both agents
- 490,254 140x64, gate: Redact driver / git textconv
- 710,56 230x56, plain: Source code / src, docs, tests
- 710,150 230x64, secret: Config with credentials / `application* · .env* · *.pem …` (code line, its own Plex Mono
  text cell inside the box)
- 710,254 230x64, secret: Git history / may hold secrets

Edges (7). The first three leave the external zone's border, not a box, because the zone as a whole reads.
- external zone → Source code, default, "reads code"
- external zone → File deny, deny, "reads config"
- external zone bottom-right → down → Git guard, default, "git"
- Git guard → Redact driver, default, "passes"
- Redact driver → Git history, gate, "masked"
- opencode → right along the bottom → up the right side → Config with credentials, ok, labelled "reads config and
  history raw" on the bottom run. If a relative x=0 label with an on-grid offset does not land on the bottom run, use
  a free text cell in ok colour on the grid.
- opencode → Git history, ok. It shares the bottom and right-side route and has no label of its own.

Free note under the two gate boxes, in gate colour: "blocked: show rev:path, grep, cat-file …".

Rendering, done by hand where draw.io desktop is installed (Ralph's devcontainer has no draw.io):
`/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -o "$TMPDIR/studio.png" <file>`. Compare the PNG with
the Style spec and the geometry above, and with the original artifact if you can open it. Add the result to
the task notes.

## Example: Kafka platform

A new diagram, not a redraw, so it has no fixed geometry. Lay it out with arch-draw's own rules: 10px grid, at least
40px between elements horizontally and 30px vertically, explicit entry and exit points, no edge through a box. Place
the chips so that the producer and consumer edges can run straight.

```
 PRODUCERS (internal)   DATA PLATFORM (repo)                              CONSUMERS (internal)
 [Order service]          KAFKA CLUSTER (group)                           [Fulfilment service]
 [Payment service]          [broker-1] <-> [broker-2] <-> [broker-3]      [Analytics sink]
 (Orders DB)                |orders.v1|  |payments.v1|  |orders.dlq|      (Warehouse)
                            replication factor 3 · min.insync.replicas 2
                          [Schema Registry] (gate)
                                      (On-call engineer, person, below the zones)
```

Zones and group:
- internal zone "PRODUCERS" on the left, repo zone "DATA PLATFORM" in the middle, internal zone "CONSUMERS" on the
  right.
- group "KAFKA CLUSTER" inside DATA PLATFORM.

Elements (kind: title / subtitle):
- plain boxes: Order service / Java · Spring Boot; Payment service / Go (PRODUCERS); Fulfilment service / Kotlin;
  Analytics sink / Kafka Connect (CONSUMERS); broker-1 / KRaft; broker-2 / KRaft; broker-3 / KRaft (in the group).
- gate box: Schema Registry / Avro · BACKWARD (in DATA PLATFORM, below the group).
- data stores: Orders DB / PostgreSQL (PRODUCERS); Warehouse / ClickHouse (CONSUMERS).
- chips in the group: `orders.v1`, `payments.v1`; deny chip: `orders.dlq`.
- free code note in the group: "replication factor 3 · min.insync.replicas 2".
- person below the zones: On-call engineer / person.

Edges (11):
- Order service → Orders DB, default, "writes"
- Order service → `orders.v1`, default async, "publishes"
- Payment service → `payments.v1`, default async, "publishes"
- Order service → Schema Registry, default, "checks schema"
- `orders.v1` → Fulfilment service, default async, "consumes"
- `payments.v1` → Analytics sink, default async, "consumes"
- Analytics sink → Warehouse, default, "loads"
- Fulfilment service → `orders.dlq`, deny async, "dead letter"
- On-call engineer → `orders.dlq`, default, "replays"
- broker-1 ↔ broker-2 and broker-2 ↔ broker-3, default two-way, no label (two edges)

## Example: order process (BPMN)

A left-to-right strip, laid out with the same rules:

```
(Order received) -> [Validate order] -> <Valid?> --yes--> [Reserve stock] -> [Notify customer] -> (Order confirmed)
                                            |
                                            no (deny)
                                            v
                                     (Order rejected, error end)
```

Elements: start event "Order received"; tasks "Validate order", "Reserve stock", "Notify customer"; exclusive gateway
"Valid?"; end event "Order confirmed"; error end event "Order rejected", below the gateway.

Sequence flows (6): start → Validate order; Validate order → gateway; gateway → Reserve stock, "yes"; Reserve stock →
Notify customer; Notify customer → end event; gateway → error end event, deny, "no".

Render the two new examples the same way. There is no original to compare them with, so check that they read
clearly and match the first example's look, and add the result to the task notes.

## Files

- `plugins/architect/skills/arch-draw/references/style-studio.md` (to-create): the preset. It holds the palette, fonts,
  one style string per element kind (extension and BPMN kinds included), the translation choices and a usage note
  with the colour meanings for general diagrams.
- `plugins/architect/skills/arch-draw/assets/studio-example.drawio` (to-create): the "Who reads what" example.
- `plugins/architect/skills/arch-draw/assets/studio-kafka-example.drawio` (to-create): the Kafka platform example.
- `plugins/architect/skills/arch-draw/assets/studio-bpmn-example.drawio` (to-create): the order process example.
- `plugins/architect/skills/arch-draw/SKILL.md` (exists): a "Style presets" section, a Quick Reference link and the
  description mention.
- `README.md` (exists): one line in the arch-draw section, and the Project Structure tree lists
  `references/style-studio.md` and the three `assets/studio-*.drawio` files under arch-draw.
- `plugins/architect/.claude-plugin/plugin.json` (exists): version 0.2.0.
- `plugins/architect/skills/arch-draw/references/cheatsheet.md` and `agent-prompt.md` (exist): do not change.

## Source

Source: ~/.claude@3a02761fb333
Style origin: a private HTML artifact, "Credential Fence" (its "Who reads what" figure). It is not in this repo,
and the spec above is complete without it.

## Before starting (destination Claude validation checklist)

Before running this task, verify:
1. All `(exists)` file paths in the Files section still exist in this repo.
2. Each AC is objectively pass/fail (a grep, test invocation, build command, or visible behavior — not "works correctly").
3. All dependencies in the task's frontmatter are status=Done.
4. Out-of-scope items are not accidentally pulled in by ambiguous AC.

If anything is unclear or any check fails: STOP and ask the user. Do NOT start work blindly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 references/style-studio.md gives an mxGraph style string for each element kind: four zones (external, internal, repo, fence), three boxes (plain, secret/deny, gate), four edges (default, deny, ok, gate), zone label, box title and subtitle, code label and edge label
- [ ] #2 Every hex colour in style-studio.md and the three assets/studio-*.drawio files is one of the eleven light-palette values in the task's Style spec: grep -ohi '#[0-9a-f]\{6\}' over those four files, lowercased and deduplicated, lists nothing else
- [ ] #3 Preset text styles use fontFamily IBM Plex Sans or IBM Plex Mono with a fontSource Google Fonts URL; every cell with IBM Plex Mono text (including every chip and the code line of Config with credentials, which is a text cell of its own) declares the IBM Plex Mono fontSource; and grep finds no Helvetica or Courier New in style-studio.md or any assets/studio-*.drawio file
- [ ] #4 assets/studio-example.drawio parses (uv run python -c "import xml.etree.ElementTree as E; E.parse('plugins/architect/skills/arch-draw/assets/studio-example.drawio')"), has the 4 zones, 9 boxes, 7 edges and the free note from the Example section, and every x, y, width and height is a multiple of 10
- [ ] #5 SKILL.md has a 'Style presets' section naming the default palettes and studio (used when the user asks for studio style), linking references/style-studio.md and saying that with studio the SKILL.md patterns (Kafka, Camunda 8, BPMN) are drawn with studio kinds, and its frontmatter description mentions the studio preset
- [ ] #6 git diff master shows no change to references/cheatsheet.md or references/agent-prompt.md, and the only removed line in SKILL.md is the old frontmatter description
- [ ] #7 README's arch-draw section mentions the studio preset and its Project Structure tree lists references/style-studio.md and the three assets/studio-*.drawio files; plugins/architect/.claude-plugin/plugin.json has version 0.2.0; uv run ruff check . passes; and uv run pytest has no failures other than test_helper_renders_canonical_decision_tree, which already fails on master
- [ ] #8 references/style-studio.md gives an mxGraph style string for each extension and BPMN kind: group, data store (plain and secret), chip (plain and deny), person, the async and two-way edge modifiers, start event, end event, error end event, task and exclusive gateway; and its usage note gives the deny, gate and ok meanings for general diagrams
- [ ] #9 assets/studio-kafka-example.drawio parses with the same ElementTree check as AC #4, has the 3 zones, the group, 8 boxes, 2 data stores, 3 chips, the person, the free code note and the 11 edges of the Kafka example, and every x, y, width and height is a multiple of 10
- [ ] #10 assets/studio-bpmn-example.drawio parses with the same ElementTree check as AC #4, has the start event, 3 tasks, the exclusive gateway, the end event, the error end event and the 6 sequence flows of the BPMN example, and every x, y, width and height is a multiple of 10
<!-- AC:END -->
