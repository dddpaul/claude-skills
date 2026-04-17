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
- Divider: vertical line at x=6.20, from y=0.88 to y=6.98
- Left column: x=0.40, w=5.60
- Right column: x=6.45, w=6.45

### Content Area
- Top: y=0.78 (section titles)
- First content block: y=1.18
- Bottom margin: y=7.10 max (0.40" from slide edge)
- Available height: ~5.9"

## Component Styles

### Content Blocks
- Full-width block: x=0.40 w=5.60
- Split blocks (two categories side by side):
  - Primary: w=3.85 (70%)
  - Secondary: w=1.65 (30%)
  - Gap: 0.10" between blocks
- Badge: w=1.55 h=0.24, positioned at top-right corner of block
  - Contrast rule: badge color must contrast with block color (ORANGE badge on BLUE block, NAVY badge on ORANGE/STEEL block)
- Block title: ABOVE the block (not inside), numbered, DARK_GRAY on white
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
- Headline: 14pt bold WHITE
- Formula / key statement: 11pt bold WHITE
- Subtitle: 9pt regular WHITE
- Distribution bar (optional): BLUE segment + ORANGE segment, h=0.30"
- Legend: colored squares 0.22x0.22" with labels, sz=9pt WHITE

### Category Descriptions
- Text blocks, each with:
  - Line 1: **Name** (bold) + description (regular), DARK_GRAY
  - Line 2: Details (bold), colored per category (see Category-Colored Emphasis)
- Spacing between blocks: ~0.55" per block

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
10. **Footnotes** are italic MUTED_GRAY, positioned at the bottom of the content area (y ≤ 7.10 in)
11. **No shadows** on any shapes — all elements are flat. Add empty `<a:effectLst/>` to `spPr` to override theme-inherited shadows
