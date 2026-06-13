---
name: pptx-core-style
description: "Corporate presentation style guide for core principles architecture slides. Use this skill alongside pptx when creating or editing any architectural presentation. Provides the canonical color palette, typography, layout grid, and component styles (badges, layer blocks, tables, distribution bars). Trigger when a task references 'pptx-core-style' or 'core-style' in its description."
---

# Core Style — Core Architecture Presentations

Canonical visual style for architectural slides. Use alongside the `pptx` skill.

## Slide Format

- Layout: `LAYOUT_WIDE` (13.3 x 7.5 inches, 16:9)
- Font: Arial (all elements)
- Corners: roundRect with `adj=4246` for content blocks, `adj=50000` for badges
- PptxGenJS `rectRadius` mapping: `adj=4246` → `rectRadius: 0.08`, `adj=50000` → `rectRadius: 0.12`

## Color Palette

| Token | Hex | Role |
|-------|-----|------|
| NAVY | `#1B2A4A` | Primary dark — header bar, key insight blocks, table header, badges on accent blocks |
| BLUE | `#4A6FA5` | Primary category — content blocks for the dominant category, distribution bar |
| ORANGE | `#E8792B` | Secondary category — content blocks for the secondary category, badges on primary blocks, arrows |
| STEEL | `#7B8794` | Neutral — legacy or out-of-scope items |
| WHITE | `#FFFFFF` | Text on colored blocks, default table row background |
| DARK_GRAY | `#363636` | Text on white background (titles, labels, descriptions) |
| LIGHT_ORANGE | `#FFF5ED` | Accent table rows (rows belonging to the secondary category) |
| LIGHT_GRAY | `#F5F7FA` | Alternating table rows |
| MUTED_GRAY | `#666666` | Footnotes (italic) |
| BORDER_GRAY | `#D0D0D0` | Table cell borders |

## Typography Scale

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Header bar title | 24pt | bold | WHITE |
| Section title | 14pt | bold | DARK_GRAY |
| Block title (numbered, above block) | 12pt | bold | DARK_GRAY |
| Badge label | 9pt | bold | WHITE |
| Content text inside blocks | 8pt | regular | WHITE |
| Table header | 7.5pt | bold | WHITE |
| Table body | 7.5pt | regular | DARK_GRAY |
| Category name | 9pt | bold | DARK_GRAY |
| Category description | 9pt | regular | DARK_GRAY |
| Category-colored emphasis | 9pt | bold | *category color* (see below) |
| Key formula / headline | 11pt | bold | WHITE |
| Subtitle text | 9pt | regular | WHITE |
| Footnote | 7.5pt | italic | MUTED_GRAY |

## Category-Colored Emphasis

When listing details under a category (e.g., technologies, tools, metrics), use bold text colored to match the category's block color. This creates a visual link between the description and its category.

| Category role | Color token | Emphasis color |
|---------------|-------------|----------------|
| Primary | BLUE | `#4A6FA5` |
| Secondary | ORANGE | `#E8792B` |
| Tertiary / other | NAVY | `#1B2A4A` |

## Layout Grid

### Slide Anatomy

```
┌──────────────────────────────────────────────────────────┐
│  NAVY bar  │  "Slide Title" 24pt bold WHITE              │ ← 0 – 0.70 in
├────────────┬────┬────────────────────────────────────────┤
│ Left col   │ ▏  │ Right col                              │ ← 0.78 in
│ x=0.40     │ ▏  │ x=6.45                                 │
│ w=5.60     │ ▏  │ w=6.45                                 │
│            │ ▏  │                                        │
│ Blocks +   │ ▏  │ Table / Key Insight /                  │
│ badges +   │ ▏  │ category descriptions                  │
│ ↓ arrows   │ ▏  │                                        │
│            │ ▏  │                                        │
│ Footnote   │ ▏  │ Footnote                               │ ← 7.10 in max
└────────────┴────┴────────────────────────────────────────┘
              ↑ divider x=6.20
```

### Header
- Bar: x=0 y=0 w=13.30 h=0.70 fill=NAVY
- Text: x=0.50 y=0 w=12.50 h=0.70

### Two-Column Layout
- Divider: vertical line at x=6.20, from y=0.88 to y=6.98, color=BORDER_GRAY, width=1pt, solid
- Left column: x=0.40, w=5.60
- Right column: x=6.45, w=6.45

### Single-Column Layout
- Full-width content: x=0.40, w=12.50
- Use for slides with a single large table, diagram, or full-width key insight block
- Same header bar and content area y-positions apply

### Content Area
- Top: y=0.78 (section titles)
- First content block: y=1.18
- Bottom margin: y=7.10 max (0.40" from slide edge)
- Available height: ~5.9"

### Title Slide
- Background: fill=NAVY (full slide)
- Main title: 44pt bold WHITE, centered horizontally, y≈2.30 (optically centered)
- Subtitle: 28pt regular BLUE, centered, directly below title
- Decorative accent: horizontal line, w≈5.00", color=ORANGE, width=2.5pt, centered at slide midpoint
- Tagline (optional): 14pt regular WHITE, centered, below accent line
- No header bar, no divider, no footnote

## Component Styles

### Content Blocks
- Full-width block: x=0.40 w=5.60
- Split blocks (two categories side by side):
  - Primary: x=0.40, w=3.85 (70%)
  - Secondary: x=4.35, w=1.65 (30%)
  - Gap: 0.10" between blocks
- Block height: ~0.30" per item + 0.10" total vertical padding (e.g., 3 items → h≈1.00", 4 items → h≈1.30")
- Badge: w=1.55 h=0.24, inset 0.10" from block right edge and 0.02" below block top edge
  - Contrast rule: badge color must contrast with block color (ORANGE badge on BLUE block, NAVY badge on ORANGE/STEEL block)
  - **Badge clearance (narrow blocks):** when a narrow (30%) block has a badge, push ALL content 0.26" below the block top — the badge spans most of the width.
  - **Badge clearance (wide blocks):** when a full-width or primary (70%) block has a badge, shorten the FIRST content item width by 1.85" (badge + inset + gap) so text wraps before the badge. Do NOT push text down — this wastes vertical space on wide blocks.
- Block title: ABOVE the block (not inside), numbered, DARK_GRAY on white
- Content item padding: left/right 0.12" inset from block edges
- Items inside blocks: separated by white horizontal lines (9525 width, 60% alpha)
- Arrows between blocks: downArrow, fill=ORANGE, cx=0.25" cy=0.20"

### Table
- Header row: fill=NAVY, text=WHITE bold
- Data rows alternate: WHITE / LIGHT_GRAY
- Accent rows (secondary category): fill=LIGHT_ORANGE
- Cell borders: BORDER_GRAY, w=6350 EMU
- Cell padding: marL=50800 marR=50800 marT=25400 marB=25400

### Key Insight Block
- fill=NAVY, full column width
- Internal padding: left/right 0.25", top 0.15"
- Headline: 14pt bold WHITE, 0.15" from top
- Formula / key statement: 11pt bold WHITE, 0.45" below headline top
- Subtitle: 9pt regular WHITE, 0.40" below formula
- Distribution bar (optional): BLUE segment + ORANGE segment, h=0.30", 0.55" below subtitle
- Legend: colored squares 0.22x0.22" with labels, sz=9pt WHITE, 0.45" below bar top

### Category Descriptions
- Text blocks, each with:
  - Line 1: **Name** (bold) + description (regular), DARK_GRAY
  - Line 2: Details (bold), colored per category (see Category-Colored Emphasis)
- Spacing between blocks: ~0.55" per block

## Dynamic Layout Formulas

All component positions are computed from column bounds. Hardcoded examples above are for the most common case — use these formulas for any count or ratio.

### Content Area Constants

```
// Two-column mode
L_X0   = 0.40        // left column start
L_W    = 5.60        // left column width
R_X0   = 6.45        // right column start
R_W    = 6.45        // right column width
// Single-column mode
F_X0   = 0.40        // full-width start
F_W    = 12.50       // full-width
// Vertical
Y0     = 1.18        // first content block top
YE     = 7.10        // max bottom
GAP    = 0.10        // standard horizontal gap (split blocks)
VGAP   = 0.08        // vertical gap between block title and block
ARROW_H = 0.20       // arrow height
ARROW_GAP = 0.08     // space above/below arrow
```

### Split Blocks (any ratio)

For any primary/secondary width split within a column of width `COL_W` starting at `COL_X`:

```
Given ratio r (0.0–1.0, primary share):
primaryW   = COL_W * r - GAP / 2
secondaryW = COL_W * (1 - r) - GAP / 2
primaryX   = COL_X
secondaryX = COL_X + primaryW + GAP
```

Default ratio: `r = 0.70` → primary w=3.85, secondary w=1.65 (in left column).

### Block Height (any item count)

```
h = items * 0.30 + 0.10
```

When a badge is present on a narrow block, add 0.26 for badge clearance:
```
h = items * 0.30 + 0.10 + 0.26
```

### N Blocks Vertically Stacked with Arrows

```
blockTitleH = 0.26
blockY[0]   = Y0
blockTopY[0] = Y0 + blockTitleH + VGAP

For i = 1..n-1:
  arrowY[i]    = blockTopY[i-1] + blockH[i-1] + ARROW_GAP
  blockY[i]    = arrowY[i] + ARROW_H + ARROW_GAP
  blockTopY[i] = blockY[i] + blockTitleH + VGAP

Check: blockTopY[n-1] + blockH[n-1] ≤ YE
```

### Distribution Bar (any segment count)

For N segments with ratios r[0..n-1] summing to 1.0:

```
barX    = ix              // bar left edge (inside Key Insight block)
barW    = available width
segW[i] = barW * r[i]
segX[0] = barX
segX[i] = segX[i-1] + segW[i-1]    // i = 1..n-1
```

Default: 2 segments (BLUE + ORANGE). For 3+, cycle through: BLUE, ORANGE, STEEL.

### Table Column Widths

Column widths should sum to the container width (`L_W`, `R_W`, or `F_W`):

```
Given relative weights w[0..c-1]:
totalW  = sum(w)
colW[i] = containerW * w[i] / totalW
```

Row heights: header 0.32, data rows 0.36. Reduce to 0.28/0.30 for dense tables (8+ rows).

## EMU Reference

1 inch = 914400 EMU. Common conversions:
- 0.04" gap = 36576 EMU
- 0.10" gap = 91440 EMU
- 0.24" badge height = 219456 EMU
- 0.25" = 228600 EMU
- 0.30" = 274320 EMU
- 0.55" = 502920 EMU
- 6.45" = 5897880 EMU
- 13.30" = 12161520 EMU

## Rules

1. **Always** render the NAVY header bar at the top of every slide
2. **Badge contrast:** ORANGE badge on BLUE block, NAVY badge on ORANGE or STEEL block — never same color for badge and block
3. **Block titles** go ABOVE the block (numbered, DARK_GRAY on white), never inside the colored fill
4. **Items inside blocks** are separated by semi-transparent white lines (width 9525, `a:alpha val="60000"`), not solid borders
5. **Category assignment:** BLUE = primary / dominant category, ORANGE = secondary, STEEL = legacy / out-of-scope
6. **Arrows** between vertically stacked blocks: ORANGE `downArrow`, 0.25 × 0.20 in
7. **Table header** is always NAVY fill with WHITE bold text
8. **Accent rows** use LIGHT_ORANGE fill to mark items of the secondary (ORANGE) category
9. **Distribution bar** segments use only category colors (BLUE + ORANGE)
10. **Footnotes** are italic MUTED_GRAY, positioned 0.20–0.30" below the last content element (never floating with a large gap). Maximum y ≤ 7.10 in
11. **No shadows** on any shapes — all elements are flat. Add empty `<a:effectLst/>` to `spPr` to override theme-inherited shadows
