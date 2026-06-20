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

Approved sizes (pt): **8, 9, 10, 10.5, 11, 12, 13, 14, 15, 16, 20, 24, 36, 40.5, 52**. Any size outside this set = violation. **5pt and smaller are forbidden** (unreadable on projection).

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
│[##]  Slide Title (24pt bold Arial)              │ <- title zone (0-0.626in)
│═══════════════════════════════════════════════════│ <- red line at y=0.500in
│                                                 │
│  Content area                                   │ <- from 0.787in to 5.10in
│  (body, tables, diagrams, images)               │
│                                                 │
│                                                 │
│  Source: ... (8pt, #666666)                     │ <- footer, near bottom
└─────────────────────────────────────────────────┘
```

- **Page number badge:** top-left corner (0, 0), 0.496in x 0.518in, `#595959` fill, white 15pt centered text
- **Red accent line:** x=0, y=0.500, w=10.00, h=0.042 (full width, no margin), color `#F12D16`
- **Title text box:** x=0.750, y=0, w=9.234, h=0.626
- **Subtitle line** (optional): x=0.750, y=0.55, w=9.00, h=0.22, 10pt regular `#666666`
- **Content area:** x=0.600, y=0.787, ends at y≈5.10
- **Footer zone:** y=5.15–5.40, x=0.600, w=8.80, 8pt `#666666`

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
- y: first row at content area top (y=0.87), subsequent rows spaced by card height + 0.15

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

```
Question diamonds:
  Shape: triangle/diamond (use prstGeom "diamond" or two-triangle composition)
  Fill: #FFF2CC (light yellow — matches Optional offload)
  Border: 1pt solid #D6B656 (matches Optional offload)
  Text: 9pt Arial Bold #000000, centered

Terminal rectangles:
  Shape: roundRect rectRadius: 0.06 (matches flow boxes)
  Fill: #DAEAF5 (blue terminal) or #D9EAD3 (green terminal)
  Border: 1pt solid #9CC3E5 (blue) or #82B366 (green)
  Text: 9pt Arial Bold #000000, centered

Connectors:
  Line: 1.0pt solid #595959 (parity with flow arrows)
  Branch labels ("Yes"/"No"): 9pt Arial Regular #666666, near the branch midpoint
```

## Dynamic Layout Formulas

All component positions are computed from the content area bounds. Hardcoded examples in the sections above are for the most common case — use these formulas for any count.

### Content Area Constants

```
X0     = 0.60        // left margin
XE     = 9.40        // right edge (10.00 - 0.60)
W      = 8.80        // content width (XE - X0)
Y0     = 0.87        // content top (below subtitle line)
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

For any width split ratio `r` (default 0.48 / 0.52):

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
- 0.500" = 457200 EMU (red accent line y-position)
- 0.518" = 473659 EMU (page number badge height)
- 0.600" = 548640 EMU (content area left margin)
- 0.626" ≈ 572414 EMU (title text box height)
- 0.700" = 640080 EMU (category card / accent height)
- 0.750" = 685800 EMU (title text box x-start)
- 0.787" ≈ 719633 EMU (content area top)
- 5.625" = 5143500 EMU (slide height)
- 9.234" ≈ 8443570 EMU (title text box width)
- 10.000" = 9144000 EMU (slide width)

## Rules

1. **Always** use the page number badge + red accent line on content slides
2. **Never** use the page number badge on title or section divider slides
3. **Red accent line** is always at x=0, y=0.500, w=10.00 (full slide width, no side margins)
4. **Left-align** all body text; center only slide titles on title/section slides
5. **No underlines** under titles — use the red accent line as the separator
6. **Footer/source** text goes near the bottom in 8pt `#666666`
7. **Numbered circles** (red) for standalone items outside boxes; text "1. 2. 3." for lists inside a content box
8. **Use semantic colors** for status — green=done, amber=planned, gray=unverified — never arbitrary colors
9. **Two-box layout** (green + amber side by side) for summary/takeaway slides. Layout: green x=0.60 w=4.20, amber x=5.00 w=4.40, same y, h=0.85. Use below a dashed separator line
10. **Content area** starts at 0.787in from top, uses 0.600in left margin
11. **No shadows** on any shapes or text — all elements are flat. The slide background MUST carry `<a:effectLst/>` inside `<p:bgPr>` to override theme-inherited shadows (this is sufficient — per-shape effectLst overrides are NOT required, since the theme used by this template defines no shape-level shadows that would propagate)

## Validation

After every generation or edit of an arch-style `.pptx`, gate the deck through the linter **before** any visual review:

1. Run the linter:
   ```
   uv run plugins/presentation/skills/pptx-arch-style/scripts/lint.py <deck.pptx>
   ```
   Add `--json` for machine-readable output. Add `--rules <path>` to override the rules file.

2. **Exit code ≠ 0 → fix violations, regenerate, repeat.** Each violation prints the failing rule id, the expected vs actual value, and the `spec_ref` line in this file that defines the rule. Exit codes: `0` clean, `1` at least one error (or untagged slide), `2` warnings only.

3. **Only after a green linter → proceed to visual QA** (render → PDF → JPEG → subagent inspection). The linter catches mechanical violations (coordinates, colors, fonts, mandatory/forbidden elements, shadow overrides); visual QA catches everything else.

4. **Every slide MUST carry a classification tag in speaker notes:**
   - Title slide → `<!--arch-style:title-->`
   - Section divider → `<!--arch-style:section-->`
   - Content slide → `<!--arch-style:content-->`

   Untagged slides are a hard error — the linter cannot pick rules without knowing the slide kind, and heuristic classification was rejected as fragile.

Rule definitions live in `references/rules.yaml` (hand-editable, separate from code). Fixture decks under `scripts/tests/fixtures/` are regenerable via `node scripts/tests/gen_fixtures.js`.
