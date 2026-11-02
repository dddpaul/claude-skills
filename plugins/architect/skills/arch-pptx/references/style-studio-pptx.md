# Studio Style Preset in PPTX

The PPTX port of the studio preset whose source of truth is arch-drawio's
[style-studio.md](../../arch-drawio/references/style-studio.md): white boxes on lightly tinted zones, IBM Plex type,
colour only for meaning. Red marks refused paths and boxes that hold secrets, amber marks gates and masking, green marks
the trusted path. Every value below is applied by [scripts/studio_pptx.py](../scripts/studio_pptx.py); this file
records what each value is and how a draw.io feature was translated to DrawingML.

## Canvas and units

| Item | Value |
|------|-------|
| Slide | 16:9, 13.333 × 7.5 in = 1280 × 720 px at 96 dpi |
| Geometry | 1 px = 9525 EMU; draw.io coordinates, sizes, gaps and radii port unchanged |
| Strokes and fonts | given in px as in the preset, written in pt: 1 px = 0.75 pt |
| Grid | 10 px for every shape and waypoint; 40 px horizontal and 30 px vertical gaps |

The draw.io rules still apply: explicit entry and exit points, no edge through a box, labels on the grid.

## Palette

Light only. Use these eleven values and nothing else.

| Token | Hex | Use |
|-------|-----|-----|
| panel | #ffffff | slide background, box fill |
| fg | #18202b | box titles, default edges and their arrowheads |
| muted | #5a6575 | subtitles, zone labels, code labels |
| line | #c3ccd7 | plain box strokes, external and repo zone strokes |
| ext | #eaf0f8 | external zone fill |
| int | #e9f4ec | internal zone fill |
| repo | #f1efe9 | repository / data zone fill |
| deny | #b3362b | refused edges, secret-holding and deny boxes |
| gate | #a8681a | gate boxes, masked edges, fence zone, fence notes |
| ok | #2c7a4b | trusted edges, internal zone stroke |
| bg | #f4f6f8 | optional slide background when the diagram stands on its own |

`Diagram(background="panel")` is the default; pass `background="bg"` for a standalone slide.

## Fonts

| Role | Font | Size px → pt |
|------|------|--------------|
| Box, store and person titles | IBM Plex Sans, bold | 13 → 9.75 |
| Subtitles, notes, edge labels | IBM Plex Sans | 11.5 → 8.62 |
| Zone and group labels | IBM Plex Sans, bold, upper case | 10.5 → 7.87 |
| Code lines, chips, code notes, code edge labels | IBM Plex Mono | 11 → 8.25 |
| Diagram title | IBM Plex Sans Condensed, bold | 18 → 13.5 |

DrawingML stores sizes in hundredths of a point, so 8.625 and 7.875 pt land on 8.62 and 7.87. python-pptx cannot
embed fonts: the three families must be installed wherever the deck is opened or rendered, or the text falls back to
another face and widths change.

## Stroke widths

| px | pt | Used by |
|----|----|---------|
| 1 | 0.75 | zones, groups, chips |
| 1.2 | 0.9 | plain boxes, plain stores, person |
| 1.5 | 1.125 | default edges |
| 1.6 | 1.2 | secret boxes and stores, deny / ok / gate edges |
| 2 | 1.5 | gate boxes |

## Translation choices

| draw.io | PPTX |
|---------|------|
| Semibold 600 (`font-weight:600` span) | `b="1"`: PowerPoint has no weight axis, so the Bold face is used |
| `letter-spacing:.08em` | `spc` on `a:rPr` in hundredths of a point: .08 × 10.5 px = 0.84 px = 0.63 pt → `spc="63"` |
| `dashPattern=5 4` / `3 4` / `4 3` | `a:custDash` with one `a:ds`; both count in stroke widths, DrawingML in 1/1000 %: `5 4` → `d="500000" sp="400000"` |
| `endArrow=block;endFill=1;endSize=9` | `a:tailEnd type="triangle" w="lg" len="lg"` on the edge's `a:ln`; the head takes the line colour |
| `startArrow=block` (two-way) | `a:headEnd` with the same attributes |
| `absoluteArcSize=1;arcSize=d` | `roundRect` with `adj` = radius / min(width, height); radii 10, 8, 6, 4 px as in the preset |
| person `arcSize=50` | `roundRect` with `adj` = 0.5 (a pill) |
| `shape=cylinder3;size=10` | `can` with a 20 px top ellipse: `adj` = 20 / min(width, height) |
| `spacingLeft=16` and friends | text-frame insets (`lIns`, `tIns`, …) in EMU; geometry stays on the grid |
| Edge `value` as label | a separate text box in the edge colour: just above a horizontal run, 6 px right of a vertical one, or at an explicit point |
| Code line cell inside a box | a separate Mono text box 30 px below the box top, same x and width, 20 px high |
| Orthogonal edge with waypoints | one freeform (`a:custGeom`) open polyline through the explicit points, no fill |
| Theme styling | the `p:style` element is removed from every shape so no theme fill, line or shadow leaks in |

There is no routing. Every edge lists its anchor points and corners; the helper's `qa()` and the rendered PNG catch an
edge through a box.

## Zones

Rounded rectangles, 10 px radius. Label top-left, 16 px in and 13 px down; a fence puts it bottom-left, 13 px up.

| Zone | Fill | Stroke | Dash |
|------|------|--------|------|
| external | ext | line, 1 | 5 4 |
| internal | int | ok, 1 | solid |
| repo | repo | line, 1 | solid |
| fence | none | gate, 1 | 3 4 |

Add a fence after the zones it crosses; it has no fill, so it never hides them.

## Boxes

Rounded rectangles, 6 px radius, panel fill, text left-aligned 16 px in (8 px right inset). Title 13 px bold fg; under
it a subtitle at 11.5 px muted, or a code line at 11 px Mono muted (then the title is top-aligned 12 px down).

| Box | Stroke | Width |
|-----|--------|-------|
| plain | line | 1.2 |
| secret / deny | deny | 1.6 |
| gate | gate | 2 |

## Architecture kinds

| Kind | Shape | Fill | Stroke | Text |
|------|-------|------|--------|------|
| group | rounded rectangle, 8 px radius | panel | line, 1 | zone-label style, top-left |
| data store | can, 20 px top ellipse | panel | line, 1.2 (secret: deny, 1.6) | box title and subtitle, centred |
| chip | rounded rectangle, 4 px radius, 30 px high | panel | line, 1 | 11 px Mono muted, centred |
| chip, deny | same as chip | panel | deny, 1 | 11 px Mono in deny |
| person | pill | panel | line, 1.2 | box title and subtitle, centred |

A chip is 30 px high and a box is best 50 px high next to it: their centres then differ by a whole 10 px step and an
edge between them runs straight. Edge end points sit on shape anchors, so a chip-centre end point may be 5 px off the
grid; inner waypoints may not.

## Edges

| Edge | Colour | Width | Meaning |
|------|--------|-------|---------|
| default | fg | 1.5 | neutral flow |
| deny | deny | 1.6 | a path that is refused |
| ok | ok | 1.6 | trusted, allowed path |
| gate | gate | 1.6 | passes a control; the output is masked |

| Modifier | PPTX | Meaning |
|----------|------|---------|
| async | `a:custDash` 4 3 | asynchronous message or event (publishes, consumes) |
| two-way | `a:headEnd` as well as `a:tailEnd` | replication, Raft, sync both ways |

Edge labels are 11.5 px Sans in the edge colour, no background; a code-like label (a flag, a tool name) is 11 px Mono
muted. Free notes are 11.5 px Sans in a meaning colour (gate inside a fence) or 11 px Mono muted.

## Colour meaning

| Colour | Use it for |
|--------|------------|
| deny | refused or failing paths (rejections, dead letters, errors) and components that hold secrets |
| gate | components whose job in the diagram is to check or transform what passes (auth, policy, schema validation, redaction, rate limiting), and the edges leaving them |
| ok | trusted or explicitly allowed paths, when the diagram contrasts them with others |

Everything else stays neutral. A name is not a kind: an API gateway is a gate box only when the diagram is about what
it checks.

## Not in this port

BPMN kinds (events, tasks, gateways) stay draw.io-only in arch-drawio. There is no legend component, no dark mode, no
auto-layout and no font embedding.

## Prior art

The mechanics (a per-slide builder script checked against a PNG render) resemble those of the `abs-slide` skill in
another repository. That is precedent only: the content contracts differ, nothing is shared at runtime and the
two skills never import from each other.
