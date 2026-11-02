---
name: arch-pptx
description: Render a free-form architecture diagram in the studio preset (white boxes on tinted zones, IBM Plex type, colour only for deny/gate/ok meaning) as native, editable PowerPoint shapes on a 16:9 slide, through a shipped python-pptx helper, with an embedded draw.io PNG as the fallback. Use when the user asks for a studio-style architecture diagram in PPTX or PowerPoint, a "studio slide", or "arch-pptx". Not for draw.io files (use arch-drawio), architecture committee (AK) review decks (use ak-style), bank-standard sequence diagrams (use abs-puml), or bank-standard slides — a bank layer landscape, a topic × function matrix, or an AS IS / TO BE systems map routes to abs-slide even when the user says "studio".
---

# Studio Architecture Diagrams in PPTX

Draw an architecture diagram as native PowerPoint shapes in the studio preset: zones, groups, boxes, chips, data
stores, people and coloured edges that stay editable in PowerPoint. Claude writes a small build script per diagram on
top of [scripts/studio_pptx.py](scripts/studio_pptx.py), checks it with `qa()`, renders it to PNG and fixes what the
render shows.

The studio look is a personal/generic diagram style, not a bank standard: a bank AK deliverable uses `ak-style` or
`abs-slide`.

## Boundaries

| Ask | Skill |
|-----|-------|
| Free-form architecture diagram as native PPTX shapes, studio look | **arch-pptx** |
| Draw.io diagram file, any style including studio; BPMN | `arch-drawio` |
| Architecture committee (AK) review deck | `ak-style` |
| Bank-standard sequence diagram (PlantUML) | `abs-puml` |
| Bank layer landscape, topic × function matrix, AS IS / TO BE systems map | `abs-slide` |

## Preconditions

| Need | Why |
|------|-----|
| Python 3.11+ with `python-pptx` (`uv run --with python-pptx` outside this repo) | the helper builds the deck |
| IBM Plex Sans, IBM Plex Mono, IBM Plex Sans Condensed installed | the preset's type; python-pptx cannot embed fonts, so the render and every viewer need them |
| LibreOffice (`soffice`) | the QA render |

Check the fonts with `fc-list : family | grep -i "IBM Plex"`. Without them the render falls back to another face and
the text widths no longer match the layout; say so instead of shipping a check made with the wrong font.

## Workflow

1. **Plan the layout on the 10px grid.** Sketch zones, then boxes inside them, 40px apart horizontally and 30px
   vertically. Pick each element's kind by meaning (see the colour table in the reference), not by name.
2. **Write the build script** next to the output, importing the helper:

   ```python
   import sys
   sys.path.insert(0, "<skill-dir>/scripts")
   from studio_pptx import Diagram

   d = Diagram()                       # 1280x720 px canvas, white background
   d.title(40, 30, 600, "Order platform")
   d.zone(240, 80, 740, 480, "Order platform", kind="internal")
   api = d.box(280, 310, 180, 60, "API gateway", sub="auth · limits", kind="gate")
   svc = d.box(540, 310, 200, 60, "Orders service", code="orders-svc")
   d.edge([api.right(), svc.left()], kind="gate", label="checked")
   for issue in d.qa():
       print(issue)
   d.save("order-platform.pptx")
   ```

   [scripts/sample_diagram.py](scripts/sample_diagram.py) uses every kind and is the template to copy.
3. **Run it and fix every `qa()` line.** It reports off-grid geometry, shapes off the canvas, overlapping boxes, text
   over boxes or across a zone border, boxes hiding a zone label, edges through boxes and text that probably does not
   fit.
4. **Render and look.**

   ```bash
   soffice --headless --convert-to \
     'png:impress_png_Export:{"PixelWidth":{"type":"long","value":"2560"},"PixelHeight":{"type":"long","value":"1440"}}' \
     --outdir /tmp/arch-pptx order-platform.pptx
   ```

   This exports the first slide; for a multi-slide deck convert to PDF and run `pdftoppm -png -r 192`. Read the PNG
   and fix what `qa()` cannot see: a label crowding an arrowhead, an edge running along a border, a crowded corner.
   Repeat until clean.

## Helper API

All coordinates are px on the 1280×720 canvas. Every call returns a `Node` (or `Edge`); `node.left()`, `.right()`,
`.top()`, `.bottom()` take a fraction along that side (default 0.5) and return the anchor point for an edge.

| Call | Draws |
|------|-------|
| `zone(x, y, w, h, label, kind)` | `external` / `internal` / `repo` tinted zone, or a dashed `fence` (label bottom-left) |
| `group(x, y, w, h, label)` | white group inside a zone: a cluster, a namespace |
| `box(x, y, w, h, title, sub=None, code=None, kind)` | `plain` / `secret` (`deny`) / `gate` box, subtitle or Mono code line |
| `chip(x, y, w, label, kind)` | 30px topic or queue chip, `plain` or `deny` |
| `store(x, y, w, h, title, sub=None, kind)` | data store cylinder, `plain` or `secret` |
| `person(x, y, w, h, title, sub=None)` | user or role pill |
| `title(x, y, w, text)` | diagram title, Plex Sans Condensed |
| `note(x, y, w, h, text, color="gate", mono=False)` | free note |
| `edge(points, kind, is_async, two_way, label, label_at, label_segment, mono_label)` | `default` / `deny` / `ok` / `gate` polyline through explicit points |
| `add_png(path)` | fallback: a PNG full-bleed on a new slide |
| `new_slide()`, `qa(page)`, `save(path)` | deck handling |

Edges have no auto-routing: pass the anchor points and every corner. Draw a fence after the zones it crosses.

## Fallback: embed a draw.io PNG

When pixel-exactness or later draw.io editing matters more than editable shapes, draw the diagram with `arch-drawio`
in the studio preset, export it at 2× (2560×1440 for a 1280×720 page) and place it:

```python
d = Diagram()
d.add_png("diagram.png")   # fills a 16:9 slide edge to edge; other ratios are fitted and centred
d.save("diagram.pptx")
```

## References

- [references/style-studio-pptx.md](references/style-studio-pptx.md) — palette, fonts, px→pt table, per-kind values and
  the draw.io → DrawingML translation choices
- [assets/studio-pptx-example.pptx](assets/studio-pptx-example.pptx) and its render
  [assets/studio-pptx-example.png](assets/studio-pptx-example.png) — the sample diagram

## Not covered

BPMN kinds (use `arch-drawio`), auto-layout, a legend component, dark mode, font embedding and draw.io → PPTX shape
conversion.
