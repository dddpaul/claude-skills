---
name: pptx-arch-style
description: Architectural presentation style guide. Apply this style when creating or editing PPTX presentations for architecture committee reviews. Defines colors, fonts, layouts, tables, and visual patterns extracted from the approved presentation. Triggers on requests to create architectural slides, AK presentations, or when told to use "pptx-arch-style" or "arch-style".
---

# Alfa Architecture Presentation Style Guide

## Slide Dimensions

- **Size:** 10.000in x 5.625in (16:9 widescreen)
- **PptxGenJS:** `pres.layout = "LAYOUT_16x9"`
- **Corner radius mapping:** `adj=5000` → `rectRadius: 0.08`, `adj=9595` → `rectRadius: 0.15`
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

| Status | Fill | Border | Text |
|--------|------|--------|------|
| **Done / Positive** | `#E8F5E9` | `#82B366` (1.5pt) | `#2E7D32` |
| **Planned / Amber** | `#FFF8E1` | `#D6B656` (1.5pt) | `#8D6E00` |
| **Not verified** | `#F5F7FA` | — | `#999999` |
| **Red / Negative** | — | `#FF0000` (2.25pt) | `#FF0000` |

### Content Box Colors

| Purpose | Fill |
|---------|------|
| Key message (green) | `#D9EAD3` |
| Context / footnote / secondary | `#D9D9D9` |
| Table header row | `#065A82` (dark teal-blue) |
| Checklist checkbox cells | `#F3F3F3` |

## Typography

### Font Pairing

| Role | Font | Fallback |
|------|------|----------|
| **Titles (content slides)** | Arial | — |
| **Body text, lists** | Roboto Condensed | Arial Narrow |
| **Title slide main** | Roboto Condensed | Arial |
| **Tables** | Arial | — |

### Size Scale

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Title slide main title | 52pt | Bold | `#F3F3F3` |
| Section divider text | 40.5pt | Regular | `#EFEFEF` |
| Content slide title | 24pt | Bold | `#000000` |
| Page number | 15pt | Regular | `#FFFFFF` on `#595959` |
| Speaker info (title slide) | 15pt | Bold | `#434343` |
| Section header in box | 10.5pt | Bold | `#000000` |
| Body text | 10.5pt | Regular | `#000000` |
| Summary box title | 10pt | Bold | semantic color |
| Summary box body | 10pt | Regular | `#333333` |
| Table body text | 9-10pt | Regular | `#333333` |
| Table header text | 9-10pt | Bold | `#FFFFFF` |
| Footer / source | 8pt | Regular | `#666666` |
| Subtitle line | 10pt | Regular | `#666666` |

### Paragraph Spacing

| Context | Line spacing | Space after |
|---------|-------------|-------------|
| Title slide title | 90% | 0 |
| Body numbered list | 100% | 6pt |
| Table cells | 100-115% | 0 |
| Section divider | 90% | 0 |

## Layout System

### Content Slide Anatomy

Every content slide has these fixed elements:

```
┌─────────────────────────────────────────────────┐
│[##]  Slide Title (24pt bold Arial)              │ <- title zone (0-0.626in)
│═══════════════════════════════════════════════════│ <- red line at y=0.500in
│                                                 │
│  Content area                                   │ <- from ~0.787in to ~5.1in
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
- Section text: centered, Roboto Condensed 40.5pt, `#EFEFEF`
- No page number badge
- No red accent line

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
Size: ~0.45in diameter
Fill: #C0392B (dark red) or similar brand red
Text: white, bold, centered, ~14pt
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
  Border: thin #E0E0E0
  No shadow

Left-border accent:
  Shape: rect, width 0.070in (5pt)
  Fill: #065A82 (same blue as table headers)
  Height: matches card height (0.70in)

Card title: 14pt bold #000000, Arial
Card subtitle: 11pt regular #666666, Arial
```

**Card layout positioning:**
- 3-across: w=2.80, gap=0.20, starting x=0.60 → cards at x=0.60, 3.60, 6.60
- 2-across: w=4.30, gap=0.20, starting x=0.60 → cards at x=0.60, 5.10
- Card height: 0.65–0.70 (adjust for subtitle length)
- y: first row at content area top (y=0.87), subsequent rows spaced by card height + 0.15

### Stat Callout Boxes (Funnel)

Large number callout boxes, decreasing in width (funnel effect):

```
Box 1 (largest):  fill #065A82 (blue), big number 32pt bold white, subtitle 12pt #B0D0E8
Box 2 (medium):   fill #C0392B (red), big number 28pt bold white, subtitle 12pt #F0C0BC
Box 3 (smallest): fill #595959 (gray), big number 28pt bold white, subtitle 12pt #B0B0B0

No shadow. No border.
Arrow annotations between boxes: 9pt #888888
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
  Text: 11pt bold white, Arial

Category row:
  Shape: rect, white fill, thin #E8E8E8 border, no shadow
  Numbered circle: oval 0.40in, 14pt bold white
  Circle colors gradient by group:
    Group A: #C0392B → #D44B3D → #E06B5E (dark red to light red)
    Group B: #595959 → #7A7A7A (dark gray to light gray)
  Row title: 12pt bold #333333
  Count: 11pt bold #065A82
  Metric: 10pt regular #888888

Totals line: 12pt bold #065A82

Footnote boxes: roundRect, fill #F0F0F0, 9pt text
  Asterisks in #FF0000
```

### Dashed Separator Line

```
Shape: line (straight connector)
Color: #21295C (dark navy)
Style: dashed
Width: ~0.75pt
Full width of content area (~9.3in)
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

Header row:
  Fill: #065A82 (dark teal-blue)
  Text: white, bold

Body rows (semantic, not alternating):
  Done:         fill #E8F5E9, status text #2E7D32 bold
  Not verified: fill #F5F7FA, status text #999999
  Planned:      fill #FFF8E1, status text #8D6E00 bold
  Default:      fill white, text #333333
```

### Style C: Data/Comparison Table

```
Header row:
  Fill: #D9EAD3 (light green)
  Text: bold, centered

Body rows:
  Fill: white or #F3F3F3 alternating
  Borders: thin #CCCCCC
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
- Text inside: component name (bold 9pt) + description (regular 8pt), padding 0.08 inset

**Arrow connectors:** line width 1pt, color `#595959`, `headEnd: { type: "triangle", w: "sm", len: "sm" }`
- Protocol labels: 7pt `#666666`, centered above the arrow in the gap between boxes (y = box_y - 0.18)

**Offload boxes** (below main flow): same width as the box they connect to, h=0.55, gap 0.50 below main row. Connected by vertical arrows (bidirectional for workers, unidirectional for others).

Labels below each box: component name (bold) + function description (regular), 8-9pt.

### Decision Tree Diagrams

```
Question diamonds:   fill light yellow, border golden
Terminal rectangles: fill light blue (#DAEAF5) or light green (#D9EAD3)
Connectors:          thin lines with "Yes"/"No" labels
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

Row heights: header 0.28, data rows 0.28–0.36 depending on content density.

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
11. **No shadows** on any shapes or text — all elements are flat. Add empty `<a:effectLst/>` to `spPr` to override theme-inherited shadows
