# Studio Style Preset

A restrained draw.io look: white boxes on lightly tinted zones, IBM Plex type, and colour kept for meaning only. Red
marks refused paths and boxes that hold secrets, amber marks gates and masking, green marks the trusted path. Use it
when the user asks for "studio style" or the "studio preset". Worked examples:

| Example | File |
|---------|------|
| Zones, boxes, fence, coloured edges ("Who reads what") | [assets/studio-example.drawio](../assets/studio-example.drawio) |
| Kafka platform: group, chips, data stores, person, async and two-way edges | [assets/studio-kafka-example.drawio](../assets/studio-kafka-example.drawio) |
| BPMN order process | [assets/studio-bpmn-example.drawio](../assets/studio-bpmn-example.drawio) |

All grid, spacing and routing rules from SKILL.md still apply: 10px grid for geometry, waypoints and label offsets,
40px horizontal and 30px vertical gaps, explicit entry and exit points, no edge through a box.

## Palette

Light only. Use these eleven values and nothing else.

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
| bg | #f4f6f8 | optional page background around the diagram |

Set `background="#ffffff"` on `mxGraphModel` (or `#f4f6f8` when the diagram sits on a page of its own).

## Fonts

| Role | Font | Style fragment |
|------|------|----------------|
| All diagram text | IBM Plex Sans 400 and 600 | `fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;` |
| Code labels: globs, commands, file names, topics | IBM Plex Mono 400 | `fontFamily=IBM Plex Mono;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BMono%3A400;` |
| Diagram title, if any | IBM Plex Sans Condensed 600 | `fontFamily=IBM Plex Sans Condensed;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%2BCondensed%3A600;` |

`fontSource` is the URL-encoded Google Fonts CSS URL, so the diagram renders where the font is not installed. Every
style string below already carries the right fragment.

## Translation choices

The style was first drawn as SVG. These are the decisions made when moving it to mxGraph:

| Topic | Choice |
|-------|--------|
| Semibold | Titles and labels are html labels with `<span style="font-weight:600">…</span>`. The Sans `fontSource` loads the 400 and 600 faces, so the 600 face is used, not a synthetic bold. `fontStyle=1` is not used. |
| Letter-spacing, two-line text | Need `html=1`. Zone labels are `<span style="font-weight:600;letter-spacing:.08em">LABEL</span>`; box text is title, `<br>`, then a subtitle span. |
| Mono text | `fontSource` is per cell and a font named only inside an html label is not loaded. So every Mono text (a code line, a chip, a code note, a code edge label) is its own cell whose style sets `fontFamily=IBM Plex Mono` and the Mono `fontSource`. |
| Corner radius | `absoluteArcSize=1` with `arcSize` read as a diameter: 20, 16, 12 and 8 give the 10, 8, 6 and 4px radii. The person pill is the exception: `arcSize=50` without `absoluteArcSize`. |
| Text inset | Geometry stays on the 10px grid; the 16px inset comes from `spacing=0;spacingLeft=16`. A code line inside a box is a text cell with the box's x and width, so its 16px inset matches the title. |
| Zone label position | `spacingTop=13` on 10.5px text puts the baseline about 22px down. The fence uses `verticalAlign=bottom;spacingBottom=13` for its bottom-left label. Zone labels stay muted, the fence one included. |
| Arrowheads | `endArrow=block;endFill=1;endSize=9`; the head takes the edge's `strokeColor`. Check the size against a render. |
| Edge labels | `labelBackgroundColor=none;verticalAlign=bottom;spacingBottom=2` puts the label just above a horizontal run. On a vertical run add `verticalAlign=middle;align=left;spacingBottom=0;spacingLeft=6` to put it just to the right. A label stays at relative `x=0`; move it with an on-grid `offset` point, or use a free text cell on the grid. |
| Dashes | `dashPattern` counts in stroke widths, so values are given as in the spec. |
| Stroke widths | Fractional widths (1.2, 1.5, 1.6) go straight into `strokeWidth`. |

## Zones

Rounded rectangles, 10px radius. The label sits top-left, 16px in and about 22px down: 10.5px, semibold, uppercase,
muted, letter-spacing .08em. Value: `<span style="font-weight:600;letter-spacing:.08em">EXTERNAL MODELS</span>`.

| Zone | Fill | Stroke | Dash |
|------|------|--------|------|
| external | ext | line, 1 | 5 4 |
| internal | int | ok, 1 | solid |
| repo | repo | line, 1 | solid |
| fence | none | gate, 1 | 3 4; label bottom-left |

```text
external:
rounded=1;absoluteArcSize=1;arcSize=20;whiteSpace=wrap;html=1;fillColor=#eaf0f8;strokeColor=#c3ccd7;strokeWidth=1;dashed=1;dashPattern=5 4;align=left;verticalAlign=top;spacing=0;spacingLeft=16;spacingTop=13;fontSize=10.5;fontColor=#5a6575;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

internal:
rounded=1;absoluteArcSize=1;arcSize=20;whiteSpace=wrap;html=1;fillColor=#e9f4ec;strokeColor=#2c7a4b;strokeWidth=1;align=left;verticalAlign=top;spacing=0;spacingLeft=16;spacingTop=13;fontSize=10.5;fontColor=#5a6575;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

repo:
rounded=1;absoluteArcSize=1;arcSize=20;whiteSpace=wrap;html=1;fillColor=#f1efe9;strokeColor=#c3ccd7;strokeWidth=1;align=left;verticalAlign=top;spacing=0;spacingLeft=16;spacingTop=13;fontSize=10.5;fontColor=#5a6575;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

fence:
rounded=1;absoluteArcSize=1;arcSize=20;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#a8681a;strokeWidth=1;dashed=1;dashPattern=3 4;align=left;verticalAlign=bottom;spacing=0;spacingLeft=16;spacingBottom=13;fontSize=10.5;fontColor=#5a6575;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;
```

Zone label text style alone (for a free label cell, or appended to a group):

```text
align=left;verticalAlign=top;spacing=0;spacingLeft=16;spacingTop=13;fontSize=10.5;fontColor=#5a6575;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;
```

Draw a fence after the zones it overlaps; it has no fill, so it never hides them.

## Boxes

Rounded rectangles, 6px radius, panel fill, text left-aligned 16px in. Title 13px semibold fg; under it a subtitle at
11.5px muted, or a code line at 11px IBM Plex Mono muted.

| Box | Stroke | Width |
|-----|--------|-------|
| plain | line | 1.2 |
| secret / deny | deny | 1.6 |
| gate | gate | 2 |

```text
plain:
rounded=1;absoluteArcSize=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#c3ccd7;strokeWidth=1.2;align=left;verticalAlign=middle;spacing=0;spacingLeft=16;spacingRight=8;fontSize=13;fontColor=#18202b;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

secret / deny:
rounded=1;absoluteArcSize=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#b3362b;strokeWidth=1.6;align=left;verticalAlign=middle;spacing=0;spacingLeft=16;spacingRight=8;fontSize=13;fontColor=#18202b;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

gate:
rounded=1;absoluteArcSize=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#a8681a;strokeWidth=2;align=left;verticalAlign=middle;spacing=0;spacingLeft=16;spacingRight=8;fontSize=13;fontColor=#18202b;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;
```

Box title and subtitle (the box's `value`, html-escaped in the XML attribute):

```html
<span style="font-weight:600">Claude Code</span><br><span style="font-size:11.5px;color:#5a6575">left pane · Anthropic</span>
```

A box with a code line instead of a subtitle: the box holds only the title and is top-aligned — replace
`verticalAlign=middle` with `verticalAlign=top;spacingTop=12` — and the code line is a separate cell 30px below the
box top, same x and width, 20px high:

```text
code label:
text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacing=0;spacingLeft=16;fontSize=11;fontColor=#5a6575;fontFamily=IBM Plex Mono;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BMono%3A400;
```

A free code note (centred, e.g. a cluster setting) uses the same style with `align=center` and no `spacingLeft`.

## Edges

Straight or orthogonal, filled triangle arrowhead in the edge colour.

| Edge | Colour | Width | Meaning |
|------|--------|-------|---------|
| default | fg | 1.5 | neutral flow |
| deny | deny | 1.6 | a path that is refused |
| ok | ok | 1.6 | trusted, allowed path |
| gate | gate | 1.6 | passes a control; the output is masked |

```text
default:
edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;endSize=9;strokeColor=#18202b;strokeWidth=1.5;fontSize=11.5;fontColor=#18202b;labelBackgroundColor=none;verticalAlign=bottom;spacingBottom=2;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

deny:
edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;endSize=9;strokeColor=#b3362b;strokeWidth=1.6;fontSize=11.5;fontColor=#b3362b;labelBackgroundColor=none;verticalAlign=bottom;spacingBottom=2;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

ok:
edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;endSize=9;strokeColor=#2c7a4b;strokeWidth=1.6;fontSize=11.5;fontColor=#2c7a4b;labelBackgroundColor=none;verticalAlign=bottom;spacingBottom=2;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

gate:
edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;endSize=9;strokeColor=#a8681a;strokeWidth=1.6;fontSize=11.5;fontColor=#a8681a;labelBackgroundColor=none;verticalAlign=bottom;spacingBottom=2;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;
```

Add the exit and entry points (`exitX=1;exitY=0.5;entryX=0;entryY=0.5;`) after the base string. To leave a zone at a
point that is not a fraction of its size, use `exitDx` / `exitDy` from a corner, e.g. `exitX=1;exitY=0;exitDy=70`.

### Edge labels

The edge's `value` is its label: 11.5px IBM Plex Sans in the edge colour, just above the line, no background. The
edge styles above already carry it. Variants appended to the edge style:

```text
edge label on a vertical run (just to the right of the line):
verticalAlign=middle;align=left;spacingBottom=0;spacingLeft=6;

code-like edge label (a flag, a tool name):
fontSize=11;fontColor=#5a6575;fontFamily=IBM Plex Mono;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BMono%3A400;
```

A code-like label replaces the Sans font, so append its fragment after the edge style (later keys win). A label that
does not land where it should is a free text cell on the grid instead, in the edge colour.

### Free notes and title

```text
free note (e.g. inside a fence, in gate colour; use the edge colour for a label cell):
text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacing=0;fontSize=11.5;fontColor=#a8681a;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

diagram title (value: <span style="font-weight:600">Title</span>):
text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacing=0;fontSize=18;fontColor=#18202b;fontFamily=IBM Plex Sans Condensed;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%2BCondensed%3A600;
```

The 18px title size is this preset's choice; the original figure had no title.

## Architecture kinds

For Kafka, Camunda 8 and C4 container diagrams. Same palette, same fonts.

| Kind | Shape | Fill | Stroke | Text |
|------|-------|------|--------|------|
| group | rounded rectangle, 8px radius | panel | line, 1 | zone-label style, top-left |
| data store | `shape=cylinder3`, `size=10` | panel | line, 1.2 (secret: deny, 1.6) | box title and subtitle, centred |
| chip | rounded rectangle, 4px radius, 30px high | panel | line, 1 | 11px IBM Plex Mono muted, centred |
| chip, deny | same as chip | panel | deny, 1 | 11px IBM Plex Mono in deny |
| person | pill | panel | line, 1.2 | box title and subtitle, centred |

- A **group** sits inside a zone and holds boxes, chips and data stores: a Kafka or Zeebe cluster, a Kubernetes
  namespace.
- A **chip** is a topic, queue, partition or other named channel. A coloured chip colours its text and border
  together. Chip text is plain (no html spans): the cell's own Mono font renders it.
- A **person** is a user or role (C4 person). It sits outside the zones.

```text
group:
rounded=1;absoluteArcSize=1;arcSize=16;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#c3ccd7;strokeWidth=1;align=left;verticalAlign=top;spacing=0;spacingLeft=16;spacingTop=13;fontSize=10.5;fontColor=#5a6575;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

data store:
shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=10;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#c3ccd7;strokeWidth=1.2;align=center;verticalAlign=middle;fontSize=13;fontColor=#18202b;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

data store, secret:
shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=10;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#b3362b;strokeWidth=1.6;align=center;verticalAlign=middle;fontSize=13;fontColor=#18202b;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

chip:
rounded=1;absoluteArcSize=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#c3ccd7;strokeWidth=1;align=center;verticalAlign=middle;fontSize=11;fontColor=#5a6575;fontFamily=IBM Plex Mono;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BMono%3A400;

chip, deny:
rounded=1;absoluteArcSize=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#b3362b;strokeWidth=1;align=center;verticalAlign=middle;fontSize=11;fontColor=#b3362b;fontFamily=IBM Plex Mono;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BMono%3A400;

person:
rounded=1;arcSize=50;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#c3ccd7;strokeWidth=1.2;align=center;verticalAlign=middle;fontSize=13;fontColor=#18202b;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;
```

A chip is 30px high and a box is best 50px high next to it: then their centres differ by a whole 10px step, and an edge
from the box to the chip runs straight.

### Edge modifiers

Append to any edge kind:

| Modifier | Style | Meaning |
|----------|-------|---------|
| async | `dashed=1;dashPattern=4 3;` | asynchronous message or event (publishes, consumes) |
| two-way | `startArrow=block;startFill=1;startSize=9;` | replication, Raft, sync both ways |

## BPMN kinds

| Element | Shape | Fill | Stroke | Label |
|---------|-------|------|--------|-------|
| start event | circle 40x40 | panel | fg, 1.5 | below, 11.5px muted, centred |
| end event | circle 40x40 | panel | fg, 3 | below, 11.5px muted, centred |
| error end event | circle 40x40 | panel | deny, 3 | below, 11.5px in deny, centred |
| task | rounded rectangle, 6px radius, 120x60 | panel | line, 1.2 | box title, centred |
| exclusive gateway | rhombus 40x40 | panel | fg, 1.5 | above, 11.5px muted, centred |

```text
start event:
ellipse;aspect=fixed;html=1;fillColor=#ffffff;strokeColor=#18202b;strokeWidth=1.5;labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top;spacingTop=2;fontSize=11.5;fontColor=#5a6575;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

end event:
ellipse;aspect=fixed;html=1;fillColor=#ffffff;strokeColor=#18202b;strokeWidth=3;labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top;spacingTop=2;fontSize=11.5;fontColor=#5a6575;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

error end event:
ellipse;aspect=fixed;html=1;fillColor=#ffffff;strokeColor=#b3362b;strokeWidth=3;labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top;spacingTop=2;fontSize=11.5;fontColor=#b3362b;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

task (value: <span style="font-weight:600">Validate order</span>):
rounded=1;absoluteArcSize=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#c3ccd7;strokeWidth=1.2;align=center;verticalAlign=middle;fontSize=13;fontColor=#18202b;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;

exclusive gateway:
rhombus;html=1;fillColor=#ffffff;strokeColor=#18202b;strokeWidth=1.5;labelPosition=center;verticalLabelPosition=top;align=center;verticalAlign=bottom;spacingBottom=2;fontSize=11.5;fontColor=#5a6575;fontFamily=IBM Plex Sans;fontSource=https%3A%2F%2Ffonts.googleapis.com%2Fcss%3Ffamily%3DIBM%2BPlex%2BSans%3A400%2C600;
```

Sequence flows are default edges; message flows are default edges with the async modifier. Branch labels ("yes",
"no") are edge labels; a branch that leads to an error end is a deny edge. Events and the gateway are 40px so their
centres line up with a 60px task's centre on the 10px grid (task at y, event at y+10). Pools, lanes, intermediate and
boundary events, and other gateway types are not part of the preset.

## Usage: colour meaning in general diagrams

| Colour | Use it for |
|--------|------------|
| deny | refused or failing paths (rejections, dead letters, errors) and components that hold secrets |
| gate | components whose job in the diagram is to check or transform what passes (auth, policy, schema validation, redaction, rate limiting), and the edges leaving them |
| ok | trusted or explicitly allowed paths, when the diagram contrasts them with others |

- Everything else stays neutral: plain boxes, default edges.
- A name is not a kind. An API gateway or a Zeebe gateway is a gate box only when the diagram is about what it
  checks.
- Kafka: a group for the cluster, plain boxes for brokers with two-way edges between them, chips for topics (a deny
  chip for a dead-letter topic), async edges for publish and consume, a gate box for a schema registry.
- Camunda 8: a group for the Zeebe cluster, boxes for brokers and gateways, two-way edges for Raft, data stores for
  Elasticsearch or OpenSearch.
- C4 container level: zones as system boundaries, boxes with a "[Container: tech]" subtitle, person for users.
