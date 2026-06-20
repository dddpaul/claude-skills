# pptx-arch-style — spec audit

Companion to `design/pptx-arch-style-validation-brainstorm.md` and TASK-21.

Each row = one gap in `plugins/presentation/skills/pptx-arch-style/SKILL.md`. Columns:
- **Where** — section in SKILL.md
- **Gap** — the ambiguous formulation or missing attribute
- **Proposal** — concrete value(s)
- **Source** — why this value (spec pattern, deck evidence, judgment)
- **Bucket** — `auto-fill` / `from-deck` / `ask-user`

Status legend after Pass A only. Pass B (deck cross-reference) and the ask-user batch happen after this initial pass.

---

## Section: Slide Dimensions

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 1 | Corner radius mapping | Only `adj=5000 → 0.08` and `adj=9595 → 0.15` documented. No general formula for arbitrary `adj` values. | Document interpolation: `rectRadius ≈ adj × 0.0000156` (5000→0.078, 9595→0.150). Mark the two named values as canonical; do not introduce intermediate ones. | The two named map to ratio 0.08/5000 ≈ 0.000016 and 0.15/9595 ≈ 0.0000156; linear interpolation is the standard pptxgenjs behavior. | auto-fill |

## Section: Color Palette → Semantic Status Colors

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 2 | All 4 status rows | Shape type unstated (rect or roundRect?). | Status boxes use `roundRect, adj=5000 (rectRadius: 0.08)` — same as Content Boxes (Rounded Rectangles) section, since semantic statuses appear as those boxes. | Consistency with the only place semantic colors are used as fills. | auto-fill |
| 3 | "Not verified" / "Red / Negative" rows | Border width: "Not verified" has `—` (none); "Red / Negative" has `2.25pt` but no shadow override stated. | Add explicit "no border" for Not verified; restate Rule #11 effect override applies to all (no per-shape exception). | Rule #11 is global. | auto-fill |

## Section: Color Palette → Content Box Colors

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 4 | All 4 rows | No shape type, border, font, padding stated. Just fill colors. | Cross-link to Component Styles section: Key message → Plain Content Box (green message box); Context/footnote → Plain Content Box (gray); Table header → Table Style B header row; Checklist checkbox cells → Table Style A column 1. | These colors are reused in named component specs that already specify the rest. | auto-fill |

## Section: Typography → Font Pairing

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 5 | "Titles (content slides)" — fallback is `—` | No fallback chain stated. | Add fallback: `Arial, Helvetica, sans-serif`. | Standard sans-serif fallback; matches PowerPoint default behavior. | auto-fill |
| 6 | "Roboto Condensed" rows — Cyrillic coverage | Roboto Condensed has limited Cyrillic glyphs in some weights. Behavior on missing glyphs undefined. | Add note: on Cyrillic-heavy text, PowerPoint will fall back per `eastAsia` / `cs` font properties. Set `eastAsia="Arial Narrow"` as the explicit Cyrillic fallback so behavior is deterministic. | Real Alfa decks are Russian-language; this is the actual encountered scenario. | from-deck (verify in Pass B) |

## Section: Typography → Size Scale

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 7 | "Table body text: 9-10pt" | Range. | Pin to **9pt** for dense status tables (Style B), **10pt** for sparse data tables (Style C). Style A is already explicit at 13pt/10pt. | Style B (status tracker) is dense by design; Style C (data/comparison) has more breathing room. | auto-fill |
| 8 | "Table header text: 9-10pt" | Range. | Match body row size in same table (9pt for Style B, 10pt for Style C). | Header should not be smaller than body. | auto-fill |

## Section: Typography → Paragraph Spacing

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 9 | "Table cells: 100-115%" | Range. | **100%** for dense tables (Style A, Style B); **115%** for sparse (Style C). | Same density logic as text size. | auto-fill |

## Section: Layout System → Section Divider Slide

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 10 | Section text positioning | "centered" — no x/y/w/h. | Position: `x=0.80, y=2.30, w=8.40, h=1.00`, vertical alignment center, horizontal alignment center. Same x-band as Title Slide main title; vertically centered between top and bottom of slide. | Parallel to Title Slide structure; vertical center of slide is `(0+5.625)/2 = 2.8125`, block centered → y ≈ 2.30 with h=1.00. | auto-fill |
| 11 | Section text weight | 40.5pt size given, no weight. | **Regular**, per Size Scale ("Section divider text: 40.5pt Regular"). | Already explicit in Size Scale; just restate here for completeness. | auto-fill |

## Section: Component Styles → Numbered Circles

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 12 | "Size: ~0.45in diameter" | Tilde. | Pin to **0.45in** exactly (also matches the EMU table entry at 411480). | EMU table already commits to 0.450"; remove the tilde. | auto-fill |
| 13 | "Text: ~14pt" | Tilde + no font face. | Pin to **14pt Arial Bold**, white. | Consistency with all other 14pt usages (card titles use 14pt Bold Arial). | auto-fill |
| 14 | Fill alternatives | "#C0392B (dark red) or similar brand red" — vague alternative. | Pin to **#C0392B** as canonical; remove "or similar brand red". | Removes invention vector. | auto-fill |

## Section: Component Styles → Category Cards with Left Accent

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 15 | "Border: thin #E0E0E0" | "thin" is fuzzy. | Pin to **0.5pt solid #E0E0E0**. | "thin" in pptxgenjs convention = 0.5pt; matches Table Style C "thin #CCCCCC" (same disambiguation needed there). | auto-fill |
| 16 | "Card height: 0.65–0.70 (adjust for subtitle length)" | Range with vague condition. | Pin: **0.65** without subtitle, **0.70** with subtitle. Compute by presence of subtitle text, not by length. | Simple binary discriminator; eliminates per-card visual drift. | auto-fill |

## Section: Component Styles → Stat Callout Boxes (Funnel)

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 17 | Big number font face | "big number 32pt bold white" — no face. | **Arial**, all three boxes. | Numerals in the brand stack are Arial; Roboto Condensed is for narrative text. | auto-fill |
| 18 | Subtitle font face | "subtitle 12pt #B0D0E8" etc. — no face. | **Arial**, all three boxes. | Same as #17. | auto-fill |
| 19 | Arrow annotations font face | "9pt #888888" — no face. | **Arial Regular**. | Same. | auto-fill |

## Section: Component Styles → Group Headers + Category Rows

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 20 | Numbered circle text font face | "14pt bold white" — no face. | **Arial Bold** (consistent with #13). | Same Numbered Circles rule. | auto-fill |
| 21 | Row title / Count / Metric / Totals — font face | None stated. | **Arial** for all (Bold/Regular per current spec). | Tables and standalone labels in this section all use Arial per Font Pairing "Tables: Arial". | auto-fill |
| 22 | Footnote boxes | "roundRect, fill #F0F0F0, 9pt text" — no border, no font face, no text color. | Add: `border: none`, font `Arial Regular 9pt #666666`, padding `0.080in`. | Footnote semantics match Plain Content Box (gray); inherit those defaults. | auto-fill |

## Section: Component Styles → Dashed Separator Line

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 23 | "Width: ~0.75pt" | Tilde. | Pin to **0.75pt**. | Tilde is just spec drift. | auto-fill |
| 24 | "Full width of content area (~9.3in)" | Tilde + wrong reference (content area is 8.80, not 9.3). | Pin to **x=0.60, w=8.80** (matches `X0` and `W` constants). | Aligns with Dynamic Layout constants. | auto-fill |

## Section: Table Styles

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 25 | Style B header row | Text size unstated; "white, bold" only. | **9pt** (matches body 9pt per #8). | Headers should not be smaller than body. | auto-fill |
| 26 | Style C "Borders: thin #CCCCCC" | "thin" is fuzzy. | **0.5pt solid #CCCCCC**. | Same disambiguation as #15. | auto-fill |
| 27 | Style C — header text size, weight, color | Not stated beyond "bold, centered". | **10pt Arial Bold #000000** (matches sparse-table 10pt body size). | Header parity with body density. | auto-fill |

## Section: Diagram Conventions → Flow / Chain Diagrams

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 28 | Text inside boxes — font face | "component name (bold 9pt) + description (regular 8pt)" — no face. | **Arial** for both. | Matches diagram convention; non-narrative. | auto-fill |
| 29 | Protocol labels — font face | "7pt #666666" — no face. | **Arial Regular**. | Same. | auto-fill |
| 30 | Labels below boxes | "8-9pt" — range, no face. | **9pt Arial Bold** for component name, **8pt Arial Regular** for function description. | Splits the range by semantic role. | auto-fill |

## Section: Diagram Conventions → Decision Tree Diagrams

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 31 | Question diamonds | "fill light yellow, border golden" — color names, no hex. | Fill **#FFF2CC** (matches Mandatory inline-flow "Optional offload" light yellow), border **#D6B656 1pt solid** (matches Optional offload border). | Reuse existing palette colors; no new shades introduced. | auto-fill |
| 32 | Terminal rectangles | "fill light blue (#DAEAF5) or light green (#D9EAD3)" — color OK but no border, no shadow, no shape geometry. | Add: shape `rect`, border `1pt solid` matching fill family (`#9CC3E5` for blue, `#82B366` for green), rectRadius 0.06 (matches flow boxes). | Mirrors Flow/Chain diagram conventions. | auto-fill |
| 33 | Connectors | "thin lines with 'Yes'/'No' labels" — thin (fuzzy), no font, no color. | Lines **0.75pt solid #595959** (matches Flow connectors 1pt but lighter for decision branches); labels **9pt Arial Regular #666666**. | Decision tree branches should read as secondary to flow arrows. | ask-user (weight choice 0.75 vs 1.0) |

---

---

## Pass B — deck cross-reference

**Sampled:** 2 of 7 decks. Saturation **NOT reached** — each deck introduces new patterns. Sampling halted at 2 decks because patterns observed are sufficient to drive ask-user decisions; further sampling would just enumerate more individual violations of the same categories.

### Deck #1: `channels/presentations/doc-2/output/channels-definition-arch.pptx`

7 slides, 69 shapes total. All Cyrillic content.

- **Colors:** 20 unique hex values, **all in spec palette** ✓
- **Fonts:** Arial + Roboto Condensed only ✓
- **Page badge at (0,0)** present on every slide ✓
- **Red line at (0, 0.500, 10.00, 0.042)** present on every slide ✓
- **`effectLst` override on individual shapes:** **0 of 69** (zero). Only present in `<p:bgPr>` per slide. **Rule #11 is not enforced at the shape level.**
- **`rectRadius adj` values used:** 6154, 8421, 9412, 10909, 15000, 17143, 23077 — **none match documented 5000/9595**.
- **Card title size:** 13pt in deck vs 14pt in spec (mismatch).
- **Card border width:** 0.75pt in deck (`<a:ln w="9525">`), spec says "thin" → Pass A #15 proposed 0.5pt — **override to 0.75pt from deck**.
- **Padding inside boxes:** achieved via external text shape offset (separate `<p:sp>` for text positioned at box+inset), not via `bodyPr` insets (`lIns="0" tIns="0"`). Spec phrasing "Padding L/R=0.100in" describes a layout convention, not an XML attribute.

### Deck #4: `equation/core/presentations/doc-3/output/doc-3-presentation.pptx`

15 slides, mixed content (one slide has 171 shapes — complex diagram).

- **NEW theme-font usage:** `<a:latin typeface="+mj-lt"/>` (major Latin theme font placeholder) — resolves to Calibri in PowerPoint, NOT to Arial. **Real violation of font_spec.**
- **NEW unknown colors (Material Design palette):**
  - `2196F3` (MD blue), `4CAF50` (MD green), `9C27B0` (MD purple), `FF9800` (MD orange)
  - `FFEBEE` (MD light red bg)
  - `FFF8E0` (light yellow — note: differs from spec's `FFF8E1` by 1 hex digit — likely typo in generator)
  - Intermediate grays not in spec: `404040`, `B8B8B8`, `BFBFBF`, `C8C8C8`
- **NEW font sizes outside spec scale:** **5pt**, 8.5pt, 11pt, **14pt**, **16pt**, **20pt**, **36pt** (bold = outside spec scale; 11pt and 14pt are in spec but were absent from deck #1 — they're in scale, just less common).
- **`effectLst` mixed enforcement:** slide 3 has 10 of 21 shapes with effectLst override; slide 1 has 0 of 2; slide 14 has 0 of 171. **Partial compliance**, not all-or-nothing.
- **NEW rectRadius adj values:** 8571, 10000, 11111, 13333. Combined with deck #1 → 11 distinct values across 2 decks, spanning roughly 6%–23% of shape size. No two-value mapping (5000/9595) can capture this.

### Cross-deck conclusions

| Finding | Deck #1 | Deck #4 | Implication |
|---|---|---|---|
| Colors strictly from spec palette | ✓ | ✗ (Material Design intrusions) | Spec needs to either: forbid all colors outside palette (strict — TASK-22 linter would fail many slides), allow named alternates, or expand palette to include MD ramp. |
| Fonts strictly Arial/Roboto Condensed | ✓ | ✗ (`+mj-lt` theme font) | Generator must explicitly set typeface; never rely on theme-major/minor placeholders. |
| Font sizes from spec scale | ✓ (except 13pt mentioned below) | ✗ (5pt, 16pt, 20pt, 36pt) | Either extend scale or treat as violations. |
| Card title 14pt | ✗ (13pt) | n/a (no cards) | Spec or deck wrong — pick canonical. |
| Rule #11 effectLst on every shape | ✗ (0/69) | ✗ (mixed) | Rule #11 unrealistic as written. |
| rectRadius mapping (5000/9595 only) | ✗ (7 other values) | ✗ (4 other values) | Spec mapping is too narrow; need formula or wider table. |
| Page badge + red line on every content slide | ✓ | ✓ | Rules 1+3 are well-enforced. |
| Title text at x=0.750, y=0, w=9.234, h=0.626 | ✓ | n/a | Layout constants for content slides are well-followed. |

### New audit rows from Pass B

| # | Where | Gap | Proposal | Source | Bucket |
|---|---|---|---|---|---|
| 34 | Rule #11 — effectLst on every shape | Not enforced in any sampled deck (0/69 in deck #1; mixed in deck #4). | Three options for user (see ask-user batch). | Deck reality. | **ask-user** |
| 35 | Slide Dimensions → Corner radius mapping | Only 2 values documented (5000, 9595); decks use 11+ values from 6154 to 23077. | Replace table with formula: `adj = round((target_radius_inches / min(w_in, h_in)) × 100000)` capped at 50000. Document the two named values as "common references" not "the only allowed values". | Math derivation from XML observations. | auto-fill |
| 36 | Color Palette — coverage scope | Decks contain Material Design colors not in spec; some are likely accidental from generator. | Add policy: linter flags any color not in spec palette as `warning` (not error). Generator should map MD colors to closest spec equivalent (e.g., MD blue → `#065A82`, MD green → `#82B366`, MD orange → `#D6B656`, MD purple → flag for review). | Compromise between strictness and existing-deck tolerance. | **ask-user** |
| 37 | Typography → font_spec | Decks use `<a:latin typeface="+mj-lt"/>` (theme-font placeholder) which resolves to Calibri, not Arial. | Add policy: linter forbids `+mj-lt`, `+mn-lt`, `+mj-ea`, `+mn-ea`, `+mj-cs`, `+mn-cs` theme placeholders; generator must always set explicit `Arial` or `Roboto Condensed`. | Real defect pattern observed. | auto-fill |
| 38 | Typography → Size Scale | Spec scale 8/9/10/10.5/11/12/14/15/24/40.5/52pt; decks use additional 5pt, 13pt, 16pt, 20pt, 36pt. | Either: (a) extend scale to include 13/16/20/36, treat 5pt as forbidden; (b) keep current scale strict, treat all extras as violations. | Trade-off between flexibility and discipline. | **ask-user** |
| 39 | Card title size | Spec 14pt vs deck 13pt. | Pin canonical to **13pt** (matches actual usage); update spec. | Deck-confirmed reality. Overrides Pass A implicit assumption. | from-deck |
| 40 | Card border width (Pass A #15 override) | Pass A proposed 0.5pt; deck uses 0.75pt (`<a:ln w="9525">`). | Override #15 → **0.75pt**. | Deck-confirmed. | from-deck |
| 41 | Padding inside content boxes | Spec phrasing "Padding L/R=0.100in" looks like a `bodyPr` insets attribute but real decks implement it via external text-shape offset. | Clarify in spec: "Padding is achieved by positioning the text-bearing shape offset from the container by the stated amount; do NOT set `bodyPr` insets (`lIns`, `rIns`, `tIns`, `bIns`)." | Deck-confirmed convention. | auto-fill |

---

## Ask-user batch — RESOLVED (2026-06-20)

User decisions captured verbatim:

1. **Rule #11 enforcement** (gap #34): **Weakened** — `<a:effectLst/>` required only in `<p:bgPr>` (slide background). Per-shape ignored. Matches deck #1 reality.
2. **Material Design / palette extras** (gap #36): **Warn + remap** — linter emits warning on any non-palette hex; generator must map MD colors to closest spec equivalent (MD blue → `#065A82`, MD green → `#82B366`, MD orange → `#D6B656`; MD purple → flag for review).
3. **Font size scale** (gap #38): **Extend** — add 13, 16, 20, 36pt to approved scale. 5pt remains forbidden as violation.
4. **Decision tree connector weight** (gap #33): **1.0pt** — parity with Flow connectors.

Pass A row #6 (Cyrillic fallback verification) confirmed by Pass B — pin `eastAsia="Arial Narrow"` as auto-fill.

---

## Bucket summary (Pass A + Pass B)

- **auto-fill**: 36 (Pass A #1-5, #7-32 + Pass B #35, #37, #41; Pass A #6 promoted from from-deck via Pass B confirmation)
- **from-deck**: 3 (Pass B #39, #40; Pass A #15 superseded by Pass B #40 → moved to from-deck)
- **ask-user**: 4 (Pass A #33; Pass B #34, #36, #38)

Total: 41 findings (33 Pass A + 8 Pass B).
