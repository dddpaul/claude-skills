---
name: pptx-arch-style
description: Architectural presentation style guide. Apply this style when creating or editing PPTX presentations for architecture committee reviews. Defines colors, fonts, layouts, tables, and visual patterns extracted from the approved presentation. Triggers on requests to create architectural slides, AK presentations, or when told to use "pptx-arch-style" or "arch-style".
---

# Alfa Architecture Presentation Style Guide

## Slide Dimensions

- **Size:** 10.000in x 5.625in (16:9 widescreen)
- **PptxGenJS:** `pres.layout = "LAYOUT_16x9"`
- **Corner radius:** in OOXML, `<a:gd name="adj" fmla="val N"/>` where `N` is in 1/100000 of the shape's shorter side. In pptxgenjs, the equivalent is `rectRadius: N / 100000`. Real decks have been observed using values from 6000 to 23000 (6% to 23% of shorter side). Two named references: `adj=5000 → rectRadius: 0.05` (subtle), `adj=9595 → rectRadius: 0.096` (equals about 10%, used for red highlight markers). For any target radius in inches, compute `adj = round((radius_in / min(w_in, h_in)) × 100000)`, capped at 50000.
- **Origin:** Google Slides template "Modern Business", adapted

## Color Palette

### Primary Colors

| Token | Hex | Usage |
|-------|-----|-------|
| **Red (brand)** | `#F12D16` | Header accent line, red annotations |
| **Dark gray** | `#595959` | Page number badge |
| **Black** | `#000000` | Slide titles, primary body text |
| **White** | `#FFFFFF` | Content slide backgrounds, text on dark fills |

### Accent Colors (Theme)

| Token | Hex | Usage |
|-------|-----|-------|
| accent1 | `#176451` | Fallback background (only visible if image overlay missing) |
| accent3 | `#D3EAC9` | Light green fills |
| accent4 | `#B6D7A8` | Medium green fills |
| accent5 | `#93C47D` | Green accents |

### Semantic Status Colors

| Status | Shape | Fill | Border | Text |
|--------|-------|------|--------|------|
| **Done / Positive** | `roundRect` adj=5000 | `#E8F5E9` | `#82B366` (1.5pt solid) | `#2E7D32` |
| **Planned / Amber** | `roundRect` adj=5000 | `#FFF8E1` | `#D6B656` (1.5pt solid) | `#8D6E00` |
| **Not verified** | `roundRect` adj=5000 | `#F5F7FA` | none | `#999999` |
| **Red / Negative** | `roundRect` adj=9595 | none | `#FF0000` (2.25pt solid) | `#FF0000` |

### Content Box Colors

| Purpose | Fill | Defined under |
|---------|------|----------|
| Key message (green) | `#D9EAD3` | Plain Content Boxes → Green message box |
| Context / footnote / secondary | `#D9D9D9` | Plain Content Boxes → Gray footnote box |
| Table header row | `#065A82` (dark teal-blue) | Table Style B → Header row |
| Checklist checkbox cells | `#F3F3F3` | Table Style A → Column 1 |

### Colors outside the palette

If a deck contains hex values not listed in the tables above (e.g., Material Design `#2196F3`, `#4CAF50`, `#FF9800`), the linter emits a `warning` (not error). Generators MUST map such colors to the closest palette equivalent at generation time:

| Observed (non-spec) | Map to (spec) |
|---|---|
| MD blue `#2196F3` and similar blues | `#065A82` |
| MD green `#4CAF50` and similar greens | `#82B366` |
| MD orange `#FF9800` / amber-like | `#D6B656` |
| MD purple `#9C27B0` and similar | flag for review (no canonical equivalent) |
| Light yellow `#FFF8E0` (typo of `#FFF8E1`) | `#FFF8E1` |

Intermediate grays not listed in the palette (`#404040`, `#B8B8B8`, `#BFBFBF`, `#C8C8C8`) should snap to the nearest listed gray (`#333333`, `#666666`, `#999999`, `#CCCCCC`).

## Typography

### Font Pairing

| Role | Font | Fallback chain |
|------|------|----------|
| **Titles (content slides)** | Arial | Helvetica, sans-serif |
| **Body text, lists** | Roboto Condensed | Arial Narrow, Helvetica Narrow, Arial, sans-serif |
| **Title slide main** | Roboto Condensed | Arial, sans-serif |
| **Tables** | Arial | Helvetica, sans-serif |
| **Numbered circles, diagram labels, stat callouts, group headers, footnote boxes** | Arial | Helvetica, sans-serif |

**Cyrillic fallback (mandatory).** Set `eastAsia="Arial Narrow"` (or `eastAsia="Arial"` for Arial-only roles) on every `<a:rPr>` carrying Cyrillic-bearing text. Roboto Condensed has limited Cyrillic glyph coverage in some weights and will silently fall back to a system font without this override.

**Forbidden: theme-font placeholders.** Never set `<a:latin typeface="+mj-lt"/>` or `+mn-lt`, `+mj-ea`, `+mn-ea`, `+mj-cs`, `+mn-cs`. These resolve to the theme's major/minor fonts (typically Calibri) and break the Arial/Roboto Condensed contract. Always set explicit `Arial` or `Roboto Condensed`.

### Size Scale

Approved sizes (pt): **7, 8, 9, 10, 10.5, 11, 12, 13, 14, 15, 16, 20, 24, 28, 32, 36, 40.5, 52**. Any size outside this set = violation. **5pt and smaller are forbidden as body text** (unreadable on projection). The three smallest-and-largest carve-outs are role-specific: `7pt` is allowed for protocol labels above flow-arrows only (see Diagram Conventions); `28pt` and `32pt` are allowed for stat-callout big numbers only (see Stat Callout Boxes).

**Legacy 22pt migration.** Content slide titles MUST be 24pt, not the legacy 22pt that pre-canary decks used. The linter's `text-runs-use-approved-font-and-size` rule will fire on any 22pt run — re-emit the title at 24pt rather than re-adding 22pt to the scale. Title length is the load-bearing variable: a 24pt title MUST fit on a single line in the 9.234in title box (no 2-line wraps — see [[#Content Slide Anatomy]] for the hard rule). When the literal title would wrap, split it into a short head as the title and the remainder as the subtitle.

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Title slide main title | 52pt | Bold | `#F3F3F3` |
| Section divider text | 40.5pt | Regular | `#EFEFEF` |
| Big section heading (oversized hero) | 36pt | Bold | `#000000` |
| Stat callout big number | 28pt / 32pt | Bold | `#FFFFFF` |
| Content slide title | 24pt | Bold | `#000000` |
| Subheading (intra-slide) | 20pt | Bold | `#000000` |
| Subheading (smaller) | 16pt | Bold | `#000000` |
| Page number | 15pt | Regular | `#FFFFFF` on `#595959` |
| Speaker info (title slide) | 15pt | Bold | `#434343` |
| Card title | 13pt | Bold | `#000000` |
| Table Style A column 1 (checkbox) | 13pt | Bold | `#000000` |
| Row title (group/category) | 12pt | Bold | `#333333` |
| Funnel subtitle / arrow annotations | 12pt | Regular | per callout |
| Group header bar text / row count | 11pt | Bold | `#FFFFFF` or `#065A82` |
| Card subtitle | 11pt | Regular | `#666666` |
| Section header in box | 10.5pt | Bold | `#000000` |
| Body text | 10.5pt | Regular | `#000000` |
| Summary box title | 10pt | Bold | semantic color |
| Summary box body | 10pt | Regular | `#333333` |
| Row metric | 10pt | Regular | `#888888` |
| Subtitle line | 10pt | Regular | `#666666` |
| Table body text (Style C — sparse) | 10pt | Regular | `#333333` |
| Table header text (Style C — sparse) | 10pt | Bold | `#000000` |
| Table body text (Style B — dense) | 9pt | Regular | `#333333` |
| Table header text (Style B — dense) | 9pt | Bold | `#FFFFFF` |
| Footnote box text | 9pt | Regular | `#666666` |
| Footer / source | 8pt | Regular | `#666666` |
| Flow box description | 8pt | Regular | `#333333` |
| Protocol labels | 7pt | Regular | `#666666` |

### Paragraph Spacing

| Context | Line spacing | Space after |
|---------|-------------|-------------|
| Title slide title | 90% | 0 |
| Body numbered list | 100% | 6pt |
| Table cells (Style A, Style B — dense) | 100% | 0 |
| Table cells (Style C — sparse) | 115% | 0 |
| Section divider | 90% | 0 |

**Padding convention.** When the spec says "Padding L/R=0.100in, T/B=0.050in" for a box, this refers to **the text-bearing shape positioned offset from the container shape** by the stated amount — not to `bodyPr` insets (`lIns`, `rIns`, `tIns`, `bIns`). In real decks, the box and its text are two separate `<p:sp>` elements: container shape, then text shape inset by the padding amount. Text shape MUST have `lIns="0" tIns="0" rIns="0" bIns="0"` (zero internal insets).

## Layout System

### Content Slide Anatomy

Every content slide has these fixed elements:

```
┌─────────────────────────────────────────────────┐
│[##]  Slide Title (24pt bold Arial)              │ <- title zone (y=0, h=0.626, middle-aligned)
│═══════════════════════════════════════════════════│ <- red line at y=0.500 (brand-constant, under page badge)
│      Subtitle (10pt, #666666)                   │ <- subtitle (y=0.550, h=0.220)
│                                                 │
│  Content area                                   │ <- from y≈0.787 to y≈5.10
│  (body, tables, diagrams, images)               │
│                                                 │
│  Source: ... (8pt, #666666)                     │ <- footer, near bottom
└─────────────────────────────────────────────────┘
```

- **Page number badge:** top-left corner (0, 0), 0.496in x 0.518in, `#595959` fill, white 15pt centered text
- **Red accent line:** x=0, y=0.500, w=10.00, h=0.042 (full width, no margin), color `#F12D16`. **The red line is a brand constant** sitting flush under the page-badge bottom edge (badge ends at y=0.518; line top at y=0.500 sits visually under it). Do NOT move it down to absorb long titles — that is what split-into-subtitle is for (see the hard rule below).
- **Title text box:** x=0.750, y=0, w=9.234, h=0.626, `valign: 'middle'` (anchor `ctr`). A 24pt single-line title (~0.30in glyph height) centers at y≈0.313, text bottom ~y=0.463 — clears the red line (top y=0.500) with ~0.04in margin. **Single-line only** at 24pt: a 2-line wrap drops the second baseline below y=0.500 and crosses the red line. Hard rule below.
- **Hard rule — no 2-line title wraps.** A content slide title MUST fit on a single line at 24pt inside the 9.234in title box. If the literal title would wrap, the implementer MUST split it: short head as the title, remainder as the subtitle. The subtitle exists precisely for this overflow. Practical character thresholds (single-line fit at 24pt Arial Bold in 9.234in): ~50 Cyrillic characters, ~60 Latin characters — beyond these counts a split is mandatory rather than discretionary.
- **Subtitle line** (optional, but mandatory whenever the title was split per the hard rule): x=0.750, y=0.550, w=9.00, h=0.220, 10pt regular `#666666`. Sits immediately under the red line (which ends at y=0.542) leaving a small visual gap; ends at y=0.770 leaving ~0.02in clearance above the content top.
- **Content area:** x=0.600, y=0.787, ends at y≈5.10 (4.31in usable). Per-slide content may start higher than y=0.787 (e.g., when no subtitle is rendered) but MUST NOT start lower.
- **Footer zone:** y=5.15–5.40, x=0.600, w=8.80, 8pt `#666666`

**ADR — why the title zone reverted from v0.7.0 to v0.2.0 anatomy (v0.9.0).** Between v0.4.x and v0.7.0 the title box was widened (h=0.626 → h=0.85) and the red line was pushed down (y=0.500 → y=0.850) so that 2-line title wraps could fit above the line. This treated the red line as a movable layout variable. It is not: the red line is a brand constant that sits directly under the page-badge, and moving it broke the visual signature of every content slide. The correct variable was always the **title text** — long titles must be split into title + subtitle (the subtitle exists for exactly this), not absorbed by growing the title zone. v0.9.0 reverts the geometry to v0.2.0 (red line y=0.500, title h=0.626 valign='middle', subtitle y=0.550, content y=0.787) and promotes "no 2-line wraps" from soft advice to a hard rule. Future iterations: if a title does not fit, split it — do NOT move the red line.

### Title Slide

- Background: `#F12D16` (brand red) fill. When a brand image overlay with geometric shapes is available, layer it on top.
- Main title: Roboto Condensed 52pt bold, `#F3F3F3`, left-aligned
  - Position: x=0.80, y=1.20, w=8.40, h=2.50, `lineSpacingMultiple: 0.90`
- Subtitle line (optional): 10pt regular `#666666`
  - Position: x=0.80, y=3.80, w=8.40, h=0.40
- Speaker info block: bottom-left, tab-separated labels/values, 15pt bold `#434343`
  - Position: x=0.80, y=4.30, w=5.00, h=0.80
- No page number badge, no red accent line
- Corporate logo watermark top-right (if available)

### Section Divider Slide

- Background: same as title slide — `#F12D16` (brand red) fill, with optional brand image overlay
- Section text: Roboto Condensed 40.5pt **Regular**, `#EFEFEF`, both horizontally and vertically centered
  - Position: x=0.80, y=2.30, w=8.40, h=1.00, anchor `ctr`, alignment `ctr`
- No page number badge
- No red accent line
- No subtitle, no speaker info

## Shape+Text Composition

The **combined form** — one pptxgenjs call that emits a shape AND its text in the same `<p:sp>` — is the default **only** when the block carries text in a **single typographic style**: one `fontFace`, one `fontSize`, one `bold`/weight, one `color`. A single label or a multi-line run in a uniform style both qualify. The overwhelming majority of components below (layer-block, distribution bar, badge, simple card, table-cell, decision-tree diamond, terminal, flow box, plain content box) fit this rule.

```javascript
// (i) Combined form OK — single-style label (one font/size/weight/color)
slide.addText("Layer A", {
  shape: pptxgen.ShapeType.roundRect,
  x: 0.60, y: 1.10, w: 2.80, h: 0.65,
  fill: { color: "DAEAF5" }, line: { color: "9CC3E5", width: 1 },
  rectRadius: 0.06,
  fontFace: "Arial", fontSize: 11, bold: true, color: "000000",
  align: "center", valign: "middle",
  margin: 0,
});
```

The **overlay form** — `slide.addShape(roundRect, {x,y,w,h,fill,line})` immediately followed by one or more `slide.addText(label, {x,y,w,h,...})` calls layered on top — is **required** in either of these cases:

1. **Multi-position labels.** The block carries 2+ labels at distinct positions (e.g., title top-left + footer-tag bottom-right, or a layer-block with a status badge overlaid in a corner).
2. **Mixed formatting in one positional cluster.** The block contains parts with different typographic styles even if they sit visually in sequence (heading + body, big-number + caption, header + footer-note, bold title + regular description). Combined form would collapse them into one text run with no typographic differentiation — the visual hierarchy would be lost.

When you use the overlay form, leave a one-line code comment naming **which** criterion justifies it:

```javascript
// (ii) Overlay justified: multi-position labels (title top-left + footer-tag bottom-right)
slide.addShape("rect", { x, y, w, h, fill: { color: "FFFFFF" }, line: { color: "E0E0E0", width: 0.75 } });
slide.addText("Card Title",    { x: x + 0.10, y: y + 0.05, w: w - 0.20, h: 0.30, fontFace: "Arial", fontSize: 13, bold: true });
slide.addText("status: active", { x: x + 0.10, y: y + h - 0.25, w: w - 0.20, h: 0.20, fontFace: "Arial", fontSize: 9, color: "666666", align: "right" });
```

```javascript
// (iii) Overlay justified: mixed formatting title+body in one positional cluster
slide.addShape("roundRect", { x, y, w, h, fill: { color: "FFF8E1" }, line: { color: "D6B656", width: 1 }, rectRadius: 0.06 });
slide.addText("Path B — fallback strategy", { x: x + 0.10, y: y + 0.08, w: w - 0.20, h: 0.32, fontFace: "Arial", fontSize: 13, bold: true,   color: "000000" });
slide.addText("Activate when primary route degrades below SLA. Owners: SRE + on-call.",
                                              { x: x + 0.10, y: y + 0.44, w: w - 0.20, h: h - 0.54, fontFace: "Arial", fontSize: 10, bold: false, color: "333333" });
```

Why combined form is the default for the single-style case:
- Half the shape count in the output `.pptx` — smaller file, faster open in PowerPoint / Keynote / LibreOffice, snappier in-editor edits.
- Text and container are a single node — coordinates cannot drift apart when the generator is later edited.
- `margin: 0` plus `align` / `valign` are properties of the same shape, so layout is enforced by the renderer, not by hand-synced sibling coordinates.

**Anti-pattern — do not use the pptxgenjs `text: [{text, options}, ...]` array form to fake mixed formatting inside a combined shape.** It bypasses overlay but (i) is cryptic to read, (ii) does not enforce title-vs-body layout (everything flows in one block), and (iii) is harder to maintain. If the content needs distinct title and body styles, use overlay.

**Legacy generators (consumer side)** that already use the overlay pattern everywhere are grandfathered — refactor recommended, not required. When touching a legacy generator, prefer flipping the touched components to combined form **only if they meet the single-style rule**; otherwise leave them as overlay.

## Component Styles

### Content Boxes (Rounded Rectangles)

Summary/callout boxes with semantic coloring:

```
Green (positive):
  Shape: roundRect, corner radius adj=5000
  Fill: #E8F5E9
  Border: 1.5pt solid #82B366
  Padding: L/R=0.100in, T/B=0.050in
  Title: 10pt bold #2E7D32
  Body: 10pt regular #333333

Amber (warning/planned):
  Shape: roundRect, corner radius adj=5000
  Fill: #FFF8E1
  Border: 1.5pt solid #D6B656
  Padding: same as green
  Title: 10pt bold #8D6E00
  Body: 10pt regular #333333
```

### Plain Content Boxes (No Border)

```
Green message box:
  Shape: rect (no rounded corners)
  Fill: #D9EAD3
  Border: none
  Padding: L/R=0.100in, T/B=0.050in

Gray footnote box:
  Shape: rect
  Fill: #D9D9D9
  Border: none
  Padding: 0.100in all sides
```

### Numbered Circles

Used for standalone ordered items outside content boxes:

```
Shape: oval
Size: 0.45in × 0.45in (diameter)
Fill: #C0392B
Border: none
Text: 14pt Arial Bold, white, anchor center, alignment center
```

### Red Highlight Markers

For annotating diagrams/screenshots:

```
Shape: roundRect, corner radius adj=9595
Fill: none
Border: 2.25pt solid #FF0000
```

### Category Cards with Left Accent

White cards with left-border accent:

```
Card:
  Shape: rect
  Fill: #FFFFFF
  Border: 0.75pt solid #E0E0E0   (EMU width 9525)
  No shadow

Left-border accent:
  Shape: rect, width 0.070in (5pt)
  Fill: #065A82 (same blue as table headers)
  Height: matches card height

Card title: 13pt Bold Arial #000000
Card subtitle: 11pt Regular Arial #666666
```

**Card layout positioning:**
- 3-across: w=2.80, gap=0.20, starting x=0.60 → cards at x=0.60, 3.60, 6.60
- 2-across: w=4.30, gap=0.20, starting x=0.60 → cards at x=0.60, 5.10
- Card height: **0.65** without subtitle, **0.70** with subtitle (binary by presence, not by length)
- y: first row at content area top (y=Y0=0.787), subsequent rows spaced by card height + 0.15

### Stat Callout Boxes (Funnel)

Large number callout boxes, decreasing in width (funnel effect):

```
Box 1 (largest):  fill #065A82 (blue), big number 32pt Arial Bold white, subtitle 12pt Arial #B0D0E8
Box 2 (medium):   fill #C0392B (red),  big number 28pt Arial Bold white, subtitle 12pt Arial #F0C0BC
Box 3 (smallest): fill #595959 (gray), big number 28pt Arial Bold white, subtitle 12pt Arial #B0B0B0

No shadow. No border.
Arrow annotations between boxes: 9pt Arial Regular #888888
```

**Funnel layout positioning:**
- Height: 0.90 for all boxes, rectRadius: 0.06
- Box 1: x=0.60, w=3.20 | Box 2: x=4.30, w=2.60 | Box 3: x=7.40, w=2.00
- Arrow text ("→") between boxes: 18pt `#666666`, centered in the gap
- Big number y-offset: +0.05 from top, h=0.50; subtitle y-offset: +0.55, h=0.30

### Group Headers + Category Rows

Category listing with group structure:

```
Group header bar:
  Shape: rect, height 0.40in
  Fill: #065A82 (Group A / primary) or #595959 (Group B / secondary)
  Text: 11pt Arial Bold white

Category row:
  Shape: rect, white fill, 0.5pt solid #E8E8E8 border, no shadow
  Numbered circle: oval 0.40in × 0.40in, 14pt Arial Bold white
  Circle colors gradient by group:
    Group A: #C0392B → #D44B3D → #E06B5E (dark red to light red)
    Group B: #595959 → #7A7A7A (dark gray to light gray)
  Row title: 12pt Arial Bold #333333
  Count:     11pt Arial Bold #065A82
  Metric:    10pt Arial Regular #888888

Totals line: 12pt Arial Bold #065A82

Footnote boxes:
  Shape: roundRect adj=5000
  Fill: #F0F0F0
  Border: none
  Padding: 0.080in (external text shape offset, zero bodyPr insets)
  Text: 9pt Arial Regular #666666
  Asterisks in #FF0000
```

### Dashed Separator Line

```
Shape: line (straight connector)
Color: #21295C (dark navy)
Style: dashed
Width: 0.75pt (EMU 9525)
Position: x=0.60, w=8.80 (matches content area constants X0 and W)
```

## Table Styles

### Style A: Checklist / Agenda Table

```
Borders: 1.5pt solid #666666 (all cells)
Cell padding: 0.100in all sides
Vertical align: center

Column 1 (checkbox): fill #F3F3F3, Roboto Condensed 13pt bold, centered
Column 2+ (description): fill #D9D9D9, Roboto Condensed 10pt bold, centered
No alternating row colors
```

### Style B: Status Tracker Table

```
Cell padding: L/R=0.050in, T/B=0.020in
Font: Arial 9pt
Line spacing: 100% (dense)

Header row:
  Fill: #065A82 (dark teal-blue)
  Text: 9pt Arial Bold white, centered

Body rows (semantic, not alternating):
  Done:         fill #E8F5E9, status text #2E7D32 Bold
  Not verified: fill #F5F7FA, status text #999999 Regular
  Planned:      fill #FFF8E1, status text #8D6E00 Bold
  Default:      fill white, text #333333 Regular
```

### Style C: Data/Comparison Table

```
Font: Arial 10pt
Line spacing: 115% (sparse)

Header row:
  Fill: #D9EAD3 (light green)
  Text: 10pt Arial Bold #000000, centered

Body rows:
  Fill: white or #F3F3F3 alternating (white first row)
  Borders: 0.5pt solid #CCCCCC (EMU 6350)
```

## Diagram Conventions

### Flow / Chain Diagrams

Component boxes in a sequential flow:

```
Mandatory inline:    fill #DAEAF5 (light blue), border #9CC3E5 (1pt solid)
Optional offload:    fill #FFF2CC (light yellow), border #D6B656 (1pt, dashType: "dash")
Initiator/response:  fill #D9EAD3 (light green), border #82B366 (1pt solid)
```

**Box dimensions:** w=1.45, h=0.70, rectRadius: 0.06, gap between boxes: 0.18
- 5 boxes across: x starts at 0.60, each at x[i-1] + 1.45 + 0.18
- Text inside: component name (9pt Arial Bold) + description (8pt Arial Regular), padding 0.08 inset

**Arrow connectors:** line width 1pt, color `#595959`, `headEnd: { type: "triangle", w: "sm", len: "sm" }`
- Protocol labels: 7pt Arial Regular `#666666`, centered above the arrow in the gap between boxes (y = box_y - 0.18)

**Offload boxes** (below main flow): same width as the box they connect to, h=0.55, gap 0.50 below main row. Connected by vertical arrows (bidirectional for workers, unidirectional for others).

Labels below each box: component name (9pt Arial Bold) + function description (8pt Arial Regular).

### Decision Tree Diagrams

Decision-tree diagrams compose three node kinds (decision diamond → branch terminals / further decisions) wired with strictly orthogonal connectors. Diagonal lines, floating decision text, and lucky-stars fanouts all read as "broken graph" on a projector — this section pins the conventions so consumers can copy the snippet below verbatim.

```
Question diamonds (decision nodes):
  Shape: pptxgenjs "diamond" (prstGeom "diamond"); fallback: two-triangle composition
  Fill: #FFF2CC (light yellow — matches Optional offload)
  Border: 1pt solid #D6B656 (matches Optional offload)
  Text: 9pt Arial Bold #000000, centered (anchor ctr, align ctr)
  Typical size: w=2.20, h=0.90 (fits a short question without text overflow)
  Decision-text rule: every question MUST live INSIDE a diamond — never as a floating italic addText with no anchor shape. The diamond is the anchor; the text is its label.

Terminal rectangles (branch leaves):
  Shape: roundRect rectRadius: 0.06 (matches flow boxes)
  Fill: #DAEAF5 (blue terminal — neutral outcome) or #D9EAD3 (green terminal — positive outcome) or #FFE0E0 (red terminal — negative outcome, optional)
  Border: 1pt solid #9CC3E5 (blue) or #82B366 (green) or #C0392B (red, optional)
  Text: 9pt Arial Bold #000000, centered

Connectors (orthogonal L-bends only — no diagonals):
  Build every edge from 2-3 LINE shapes (pptxgenjs addShape("line", ...)) — each segment is either purely vertical (w=0, h>0) or purely horizontal (w>0, h=0). A single LINE with BOTH w>0 AND h>0 is a diagonal and is forbidden — the linter rule `decision-tree-connector-orthogonal` (warning) fires on it.
  Style: 1.0pt solid #595959, triangle arrowhead { type: "triangle", w: "sm", len: "sm" } on the final segment only.
  Two-segment L-bend (vertical then horizontal, or vice-versa) covers parent→child edges where the child is offset to a side.
  Three-segment Z (vertical-down → horizontal → vertical-down) covers parent→child where the child is below AND offset.

Direction semantics (mandatory — applies to every connector helper):
  Every connector carries an explicit semantic direction parent→child (or from→to). The arrowhead lives at the `to` end regardless of coordinate order — never at the higher-numbered coordinate by default.
  Helpers MUST take parameters as `(from, to)` or `(fromX/Y, toX/Y, withArrow)` — NEVER normalize via Math.min/Math.abs and then attach `endArrowType` blindly. With normalized x = min(from, to) and w = abs(to - from), the line's geometric "end" sits at (x + w) which is max(from, to); if semantic `to` is the smaller coordinate, attaching `endArrowType: "triangle"` puts the arrow on the wrong side.
  Correct pattern: detect `flip = to < from`; place the arrowhead on the appropriate end of the LINE shape — `beginArrowType: "triangle"` when flipped, `endArrowType: "triangle"` otherwise. Equivalent fallback: `flipH: true` (horizontal) or `flipV: true` (vertical) with `endArrowType` left as-is.
  Final-segment rule for L-bends / Z-bends: the arrowhead belongs on the segment whose `to` coincides with the child's anchor point — typically the last vertical drop into a child top, or the last horizontal run into a child side. Intermediate segments (bus, elbow) carry NO arrowhead.

Branch labels ("ДА" / "НЕТ" / "Yes" / "No"):
  Style: 9pt Arial Regular #666666, no fill.
  Position rule: anchor to the connector BEND, not the segment midpoint. For a two-segment L (down + right) the label sits just outside the corner: x ≈ corner_x + 0.05, y ≈ corner_y - 0.18 (above) or corner_y + 0.05 (below). Labels MUST NOT float in whitespace away from a bend.

T-junction pattern (fanout 1→N):
  When a decision/parent feeds N>2 children, do NOT draw N rays from a single point. Instead build a "shower head":
    1. vertical drop from parent bottom → shared bus_y (NO arrowhead — intermediate segment)
    2. horizontal bus from leftmost_child_x → rightmost_child_x at bus_y (single LINE, NO arrowhead — intermediate segment)
    3. N vertical drops from bus_y → each child top — EACH drop MUST carry an arrowhead at the child end (`endArrowType: "triangle"`, or `beginArrowType` if the drop direction is bottom→top)
  The bus carries N-1 visible T-junctions; the rendering is unambiguous and reads as a parallel fanout. Anti-pattern: 3+ LINE shapes sharing one endpoint, OR a fanout where the N child-drops are plain LINE shapes without arrowheads (the linter rule `decision-tree-connector-arrowhead-missing` (warning) fires on the latter).
```

**Canonical pptxgenjs snippet** (copy-paste; ~50 LOC). Renders a root decision with a two-branch outcome (NO → terminal) and a sub-decision (YES → another diamond → 3-way fanout via T-junction). Uses combined `addText({shape, fill, line, ...})` form per [[#Shape+Text Composition]] — diamonds and terminals each carry a single centered label, so the shape and text live in one node. Connector helpers take `(fromX, toX, ...)` / `(fromY, toY, ...)` — direction-aware so the arrowhead always lands at the semantic `to`.

```javascript
// Decision tree: root → (NO: terminal) / (YES: sub-decision → 3 outcomes)
// Palette: yellow diamond, blue/green terminals, gray L-bends (#595959).
const GRAY = "595959", YF = "FFF2CC", YB = "D6B656";
const BF = "DAEAF5", BB = "9CC3E5", GF = "D9EAD3", GB = "82B366";
const D = { w: 2.20, h: 0.90 }, T = { w: 1.80, h: 0.55 };

function diamond(s, x, y, text) {
  s.addText(text, { shape: "diamond", x, y, w: D.w, h: D.h,
    fill: { color: YF }, line: { color: YB, width: 1 },
    fontFace: "Arial", fontSize: 9, bold: true, color: "000000",
    align: "center", valign: "middle", margin: 0 });
}
function terminal(s, x, y, text, fill, border) {
  s.addText(text, { shape: "roundRect", x, y, w: T.w, h: T.h, rectRadius: 0.06,
    fill: { color: fill }, line: { color: border, width: 1 },
    fontFace: "Arial", fontSize: 9, bold: true, color: "000000",
    align: "center", valign: "middle", margin: 0 });
}
// Direction-aware connectors. (from, to) are SEMANTIC endpoints — arrowhead
// lands at `to` regardless of which is the smaller coordinate.
function vline(s, x, fromY, toY, withArrow) {
  const flip = toY < fromY;
  const arrowKey = withArrow ? (flip ? "beginArrowType" : "endArrowType") : null;
  const lineOpts = { color: GRAY, width: 1 };
  if (arrowKey) lineOpts[arrowKey] = "triangle";
  s.addShape("line", { x, y: Math.min(fromY, toY), w: 0, h: Math.abs(toY - fromY),
    line: lineOpts });
}
function hline(s, fromX, toX, y, withArrow) {
  const flip = toX < fromX;
  const arrowKey = withArrow ? (flip ? "beginArrowType" : "endArrowType") : null;
  const lineOpts = { color: GRAY, width: 1 };
  if (arrowKey) lineOpts[arrowKey] = "triangle";
  s.addShape("line", { x: Math.min(fromX, toX), y, w: Math.abs(toX - fromX), h: 0,
    line: lineOpts });
}
function label(s, x, y, text) {
  s.addText(text, { x, y, w: 0.40, h: 0.20, fontFace: "Arial", fontSize: 9,
    color: "666666", align: "left", valign: "middle" });
}

// Layout (root row 1 with NO terminal beside it, sub row 2, fanout row 3).
// All y values are inside content area (Y0=0.787, YE=5.10).
diamond(slide, 3.90, 1.20, "Условие А?");                                 // root spans x=[3.90,6.10]
// NO branch — straight horizontal arrow from diamond right edge → terminal left edge.
terminal(slide, 7.20, 1.38, "Terminal NO", BF, BB);
hline(slide, 6.10, 7.20, 1.65, true);  label(slide, 6.30, 1.40, "НЕТ");
// YES branch — straight vertical drop from diamond bottom → sub-decision top.
vline(slide, 5.00, 2.10, 2.40, true);  label(slide, 5.05, 2.15, "ДА");
diamond(slide, 3.90, 2.40, "Условие Б?");
// 3-way fanout from sub-diamond via T-junction (drop → bus → 3 drops with arrowheads).
vline(slide, 5.00, 3.30, 3.70, false);                   // bus drop, intermediate
hline(slide, 2.50, 7.50, 3.70, false);                   // bus, intermediate
vline(slide, 2.50, 3.70, 4.10, true);                    // final drop → child 1 (arrow)
vline(slide, 5.00, 3.70, 4.10, true);                    // final drop → child 2 (arrow)
vline(slide, 7.50, 3.70, 4.10, true);                    // final drop → child 3 (arrow)
terminal(slide, 1.60, 4.10, "Outcome 1", GF, GB);
terminal(slide, 4.10, 4.10, "Outcome 2", BF, BB);
terminal(slide, 6.60, 4.10, "Outcome 3", GF, GB);
```

**Optional helper file** (Path B). Consumers who want to skip the recipe-translation step can `require` the bundled helper instead of inlining the snippet above. The helper exposes a single function and takes the same direction-aware (from, to) semantics:

```javascript
const { drawDecisionTree } = require(
  '<plugin-root>/plugins/presentation/skills/pptx-arch-style/scripts/decision-tree.js'
);

drawDecisionTree(slide, {
  diamonds: [
    { x: 3.90, y: 1.20, text: "Условие А?" },
    { x: 3.90, y: 2.40, text: "Условие Б?" },
  ],
  terminals: [
    { x: 7.20, y: 1.38, text: "Terminal NO", color: "blue" },
    { x: 1.60, y: 4.10, text: "Outcome 1",   color: "green" },
    { x: 4.10, y: 4.10, text: "Outcome 2",   color: "blue" },
    { x: 6.60, y: 4.10, text: "Outcome 3",   color: "green" },
  ],
  connectors: [
    { kind: "h", fromX: 6.10, toX: 7.20, y: 1.65, withArrow: true,  label: { text: "НЕТ", x: 6.30, y: 1.40 } },
    { kind: "v", x: 5.00, fromY: 2.10, toY: 2.40, withArrow: true,  label: { text: "ДА",  x: 5.05, y: 2.15 } },
    { kind: "v", x: 5.00, fromY: 3.30, toY: 3.70, withArrow: false },   // bus drop
    { kind: "h", fromX: 2.50, toX: 7.50, y: 3.70, withArrow: false },   // bus
    { kind: "v", x: 2.50, fromY: 3.70, toY: 4.10, withArrow: true  },   // final drop → child 1
    { kind: "v", x: 5.00, fromY: 3.70, toY: 4.10, withArrow: true  },   // final drop → child 2
    { kind: "v", x: 7.50, fromY: 3.70, toY: 4.10, withArrow: true  },   // final drop → child 3
  ],
});
```

The helper is self-contained (no pptxgenjs dependency at require-time — it calls `slide.addText` / `slide.addShape` on the passed `slide` object). Use it if you want a single import; use the recipe inline if you need to tweak palette/sizes per slide.

**Common defect classes** (linter `decision-tree-connector-orthogonal` (warning) catches class 1; `decision-tree-connector-arrowhead-missing` (warning) catches class 5; classes 2-4 and 6 are caught by visual review):

1. **Diagonal connector** — one LINE shape with `w=x2-x1, h=y2-y1` (both ≠ 0) drawn from a parent to an offset child. Fix: split into two LINE shapes (vertical + horizontal). Linter rule fires at severity `warning`.
2. **Fanout-as-rays** — N>2 separate LINE shapes diverging from one parent point. Fix: rewrite as T-junction (drop + bus + N drops).
3. **Decision text without shape** — italic `addText` "Условие?" with no diamond/roundRect anchor underneath. Fix: wrap in a `diamond` shape.
4. **Floating branch labels** — `addText("НЕТ")` positioned in whitespace away from any connector bend. Fix: re-anchor to the corner (`x = corner_x + 0.05`).
5. **Arrowhead-missing terminal connector** — a gray (#595959) LINE shape that targets a child anchor but carries neither `beginArrowType` nor `endArrowType`. Manifests as plain sticks instead of arrows on T-junction final drops. Fix: add `endArrowType: "triangle"` (or `beginArrowType` when the drop is bottom-up). Linter rule fires at severity `warning`.
6. **Reversed connector direction** — a connector helper normalizes coordinates with `Math.min`/`Math.abs` and pins `endArrowType` to the geometric end; when semantic `to` is the smaller coordinate the arrowhead points back at the parent instead of forward at the child. Fix: use the direction-aware `(from, to)` helpers above, OR `flipH`/`flipV` to swap visual direction.

## Dynamic Layout Formulas

All component positions are computed from the content area bounds. Hardcoded examples in the sections above are for the most common case — use these formulas for any count.

### Content Area Constants

```
X0     = 0.60        // left margin
XE     = 9.40        // right edge (10.00 - 0.60)
W      = 8.80        // content width (XE - X0)
Y0     = 0.787       // content top (below subtitle line at y=0.55 h=0.22; v0.7.0..v0.8.x used 1.10)
YE     = 5.10        // content bottom (above footer zone)
GAP    = 0.20        // standard horizontal gap
VGAP   = 0.15        // standard vertical gap between rows
```

### N Elements in a Row (equal width)

Cards, flow boxes, or any equal-width elements:

```
itemW  = (W - (n - 1) * GAP) / n
itemX[i] = X0 + i * (itemW + GAP)       // i = 0..n-1
```

### N Elements in a Row (custom ratio)

When elements have different proportional widths (e.g., funnel, split blocks):

```
Given ratios r[0..n-1] that sum to 1.0:
totalGap = (n - 1) * GAP
availW   = W - totalGap
itemW[i] = availW * r[i]
itemX[0] = X0
itemX[i] = itemX[i-1] + itemW[i-1] + GAP   // i = 1..n-1
```

**Funnel shortcut** (decreasing widths for stat callouts):
```
ratios for n boxes: r[i] = (n - i) / sum(1..n)
Example n=3: r = [3/6, 2/6, 1/6] = [0.50, 0.33, 0.17]
Example n=4: r = [4/10, 3/10, 2/10, 1/10] = [0.40, 0.30, 0.20, 0.10]
```

### Two-Box Summary Layout (green + amber)

For any width split ratio `r` (default 0.488 / 0.512 — reproduces Rule #9 widths exactly given W=8.80 and GAP=0.20):

```
greenW = W * r - GAP / 2
amberW = W * (1 - r) - GAP / 2
greenX = X0
amberX = X0 + greenW + GAP
```

### Table Column Widths

Column widths should sum to content width `W`:

```
Given relative weights w[0..c-1]:
totalW  = sum(w)
colW[i] = W * w[i] / totalW
```

Row heights: header **0.28** (all styles); data rows **0.28** for Style A / Style B (dense), **0.36** for Style C (sparse).

### Vertical Stacking

For vertically stacked elements (blocks, cards across multiple rows):

```
itemY[0] = Y0
itemY[i] = itemY[i-1] + itemH[i-1] + VGAP   // i = 1..n-1
```

Check: last element bottom `itemY[n-1] + itemH[n-1]` must be ≤ `YE`.

## EMU Reference

1 inch = 914400 EMU. Common conversions for this template:
- 0.042" = 38405 EMU (red accent line height)
- 0.050" = 45720 EMU (box top/bottom padding)
- 0.070" = 64008 EMU (left accent border width)
- 0.100" = 91440 EMU (box left/right padding)
- 0.400" = 365760 EMU (group header bar height)
- 0.450" = 411480 EMU (numbered circle diameter)
- 0.496" = 453542 EMU (page number badge width)
- 0.500" = 457200 EMU (red accent line y-position — brand constant under page badge)
- 0.518" = 473659 EMU (page number badge height)
- 0.550" = 502920 EMU (subtitle y-position — under red line)
- 0.600" = 548640 EMU (content area left margin)
- 0.626" ≈ 572414 EMU (title text box height — single-line 24pt valign:middle)
- 0.700" = 640080 EMU (category card / accent height)
- 0.750" = 685800 EMU (title text box x-start)
- 0.787" ≈ 719633 EMU (content area top — below subtitle slot)
- 0.850" = 777240 EMU (title text box height — withdrawn v0.7.0..v0.8.x experiment; do not use)
- 0.900" = 822960 EMU (subtitle y-position — withdrawn v0.7.0..v0.8.x experiment; do not use)
- 1.100" = 1005840 EMU (content area top — withdrawn v0.7.0..v0.8.x experiment; do not use)
- 5.625" = 5143500 EMU (slide height)
- 9.234" ≈ 8443570 EMU (title text box width)
- 10.000" = 9144000 EMU (slide width)

## Rules

1. **Always** use the page number badge + red accent line on content slides
2. **Never** use the page number badge on title or section divider slides
3. **Red accent line** is always at x=0, y=0.500, w=10.00 (full slide width, no side margins). The line is a brand constant sitting flush under the page-number badge — do not move it. v0.7.0..v0.8.x experimentally pushed it down to y=0.850 to absorb 2-line title wraps; v0.9.0 reverts because the line is brand-level, not layout-level. Long titles MUST be split into title + subtitle (see [[#Content Slide Anatomy]] hard rule).
4. **Left-align** all body text; center only slide titles on section slides
5. **No underlines** under titles — use the red accent line as the separator
6. **Footer/source** text goes near the bottom in 8pt `#666666`
7. **Numbered circles** (red) for standalone items outside boxes; text "1. 2. 3." for lists inside a content box
8. **Use semantic colors** for status — green=done, amber=planned, gray=unverified — never arbitrary colors
9. **Two-box layout** (green + amber side by side) for summary/takeaway slides. Layout: green x=0.60 w=4.20, amber x=5.00 w=4.40, same y, h=0.85. Use below a dashed separator line
10. **Content area** starts at 0.787in from top (below the subtitle slot), uses 0.600in left margin. v0.7.0..v0.8.x pushed this to 1.100in to accommodate a downward-shifted red line; v0.9.0 reverts.
11. **No shadows** on any shapes or text — all elements are flat. The slide background MUST carry `<a:effectLst/>` inside `<p:bgPr>` to override theme-inherited shadows (this is sufficient — per-shape effectLst overrides are NOT required, since the theme used by this template defines no shape-level shadows that would propagate). **pptxgenjs (v4.0.1) does not emit `<a:effectLst/>` for `slide.background = { color: ... }`** — run `scripts/postprocess-effectlst.py` after generation to inject it (see [[#Validation]] for the full pipeline)
12. **Orthogonal LINE shapes only** on content slides: every `addShape("line", ...)` MUST be either purely horizontal (`h=0, w>0`) or purely vertical (`w=0, h>0`). Diagonal LINE shapes (both `w>0` and `h>0`) are forbidden regardless of context — connectors, separators, dividers, callouts. The linter rule `decision-tree-connector-orthogonal` (warning) fires on any violation. This generalizes the decision-tree-specific orthogonality requirement in Diagram Conventions to the whole slide vocabulary.

## Validation

After every generation or edit of an arch-style `.pptx`, gate the deck through the linter **before** any visual review:

1. **Inject `<a:effectLst/>` overrides** (only required when the generator is pptxgenjs):
   ```
   uv run plugins/presentation/skills/pptx-arch-style/scripts/postprocess-effectlst.py <deck.pptx>
   ```
   The script rewrites the deck in place, adding an empty `<a:effectLst/>` sibling to every `<p:bgPr>` that is missing one. Skip this step for python-pptx or hand-authored decks that already emit the override. See Rule #11 above for the upstream gap that makes this step necessary.

2. Run the linter:
   ```
   uv run plugins/presentation/skills/pptx-arch-style/scripts/lint.py <deck.pptx>
   ```
   Add `--json` for machine-readable output. Add `--rules <path>` to override the rules file.

3. **Exit code ≠ 0 → fix violations, regenerate, repeat.** Each violation prints the failing rule id, the expected vs actual value, and the `spec_ref` line in this file that defines the rule. Exit codes: `0` clean, `1` at least one error (or untagged slide), `2` warnings only.

4. **Only after a green linter → proceed to visual QA** (render → PDF → JPEG → subagent inspection). The linter catches mechanical violations (coordinates, colors, fonts, mandatory/forbidden elements, shadow overrides); visual QA catches everything else.

5. **Every slide MUST carry a classification tag in speaker notes:**
   - Title slide → `<!--arch-style:title-->`
   - Section divider → `<!--arch-style:section-->`
   - Content slide → `<!--arch-style:content-->`

   Untagged slides are a hard error — the linter cannot pick rules without knowing the slide kind, and heuristic classification was rejected as fragile.

Rule definitions live in `references/rules.yaml` (hand-editable, separate from code). Fixture decks under `scripts/tests/fixtures/` are regenerable via `node scripts/tests/gen_fixtures.js`.
