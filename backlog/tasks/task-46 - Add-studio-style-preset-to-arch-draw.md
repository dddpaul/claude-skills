---
id: TASK-46
title: Add studio style preset to arch-draw
status: To Do
assignee: []
created_date: '2026-10-09 05:38'
updated_date: '2026-10-09 06:09'
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

## Scope

In scope:
- A `studio` preset reference: palette, fonts and an mxGraph style string for every element kind in the Style spec
  below.
- A "Style presets" section in SKILL.md. It names the default (the existing palettes, unchanged) and says when to use
  `studio` (the user asks for "studio style" or "studio preset"). It links the reference. The frontmatter description
  mentions the preset.
- An example `.drawio` that redraws the "Who reads what" diagram (Example section) in the preset.
- One line about the preset in README's arch-draw section, the two new files added to README's Project Structure
  tree, and the architect plugin's version bumped from 0.1.1 to 0.2.0 (broadened trigger).

Out of scope:
- Changing the existing default palettes, the Complete Example, the checklist, cheatsheet.md or agent-prompt.md.
- Dark mode or adaptive colours. The dark palette below is recorded for a later task only and stays out of the
  preset files.
- pptx or any other output format, and the presentation plugin.
- Python generators, linters or tests for the preset.

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
- Corner radius: use `absoluteArcSize=1` with `arcSize`, and check by rendering which value gives 10px and 6px.
- Fractional stroke widths (1.2, 1.5, 1.6) are fine in `strokeWidth`.

Dark palette, recorded only (out of scope): bg #11151b, fg #e2e7ee, muted #98a3b2, line #394351, panel #19202a,
ext #172130, int #15241b, repo #221f19, deny #f0776b, gate #e5a347, ok #62c08a.

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
the artifact, and add the result to the task notes.

## Files

- `plugins/architect/skills/arch-draw/references/style-studio.md` (to-create): the preset. It holds the palette, fonts,
  one style string per element kind, the translation choices and a short usage note.
- `plugins/architect/skills/arch-draw/assets/studio-example.drawio` (to-create): the "Who reads what" example.
- `plugins/architect/skills/arch-draw/SKILL.md` (exists): a "Style presets" section, a Quick Reference link and the
  description mention.
- `README.md` (exists): one line in the arch-draw section, and the Project Structure tree lists
  `references/style-studio.md` and `assets/studio-example.drawio` under arch-draw.
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
- [ ] #2 Every hex colour in style-studio.md and assets/studio-example.drawio is one of the eleven light-palette values in the task's Style spec: grep -ohi '#[0-9a-f]\{6\}' over both files, lowercased and deduplicated, lists nothing else
- [ ] #3 Preset text styles use fontFamily IBM Plex Sans or IBM Plex Mono with a fontSource Google Fonts URL; every cell with IBM Plex Mono text (including the code line of Config with credentials, which is a text cell of its own) declares the IBM Plex Mono fontSource; and grep finds no Helvetica or Courier New in the two preset files
- [ ] #4 assets/studio-example.drawio parses (uv run python -c "import xml.etree.ElementTree as E; E.parse('plugins/architect/skills/arch-draw/assets/studio-example.drawio')"), has the 4 zones, 9 boxes, 7 edges and the free note from the Example section, and every x, y, width and height is a multiple of 10
- [ ] #5 SKILL.md has a 'Style presets' section naming the default palettes and studio (used when the user asks for studio style), linking references/style-studio.md, and its frontmatter description mentions the studio preset
- [ ] #6 git diff master shows no change to references/cheatsheet.md or references/agent-prompt.md, and the only removed line in SKILL.md is the old frontmatter description
- [ ] #7 README's arch-draw section mentions the studio preset and its Project Structure tree lists references/style-studio.md and assets/studio-example.drawio; plugins/architect/.claude-plugin/plugin.json has version 0.2.0; uv run ruff check . passes; and uv run pytest has no failures other than test_helper_renders_canonical_decision_tree, which already fails on master
<!-- AC:END -->
