---
id: TASK-27
title: >-
  Fix title-zone regression — title sinks below red line, subtitle overlaps
  content
status: Done
assignee: []
created_date: '2026-06-20 20:54'
updated_date: '2026-06-20 21:23'
labels:
  - 'feature:pptx-arch-style-validation'
dependencies: []
priority: high
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

TASK-24 ship'нул title-zone fix (h 0.626→0.85, subtitle y 0.55→0.78), но spec в SKILL.md «Content Slide Anatomy» получился **внутренне противоречивым** — title box и subtitle box перекрывают red line и content area соответственно. После применения consumer'ом (stacks TASK-58, applied canary под v0.6.1) визуально на ВСЕХ content-слайдах:

- Заголовок проваливается ниже красной линии (24pt текст vertically centered в 0.85in зоне с default `valign: middle` опускается ниже y=0.5 — bottom baseline даже однострочного заголовка на ~y=0.575, у двухстрочного — на ~y=0.725).
- Subtitle на y=0.78 (h=0.22) занимает y-диапазон [0.78, 1.00] — а content area начинается с y=0.787 → subtitle буквально оверлапит content.

Это **регрессия**: до TASK-24 при h=0.626 + subtitle y=0.55 заголовок умещался В пределах red line (y<0.5), subtitle сидел сразу под красной линией (y=0.55-0.77), content начинался с y=0.787 без пересечений.

Spec в SKILL.md одновременно говорит:
- «red line at y=0.500in» (line 142, line 153)
- «Title text box: x=0.750, y=0, w=9.234, h=0.85» (line 154) ← перекрывает red line на 0.35in
- «Subtitle line: x=0.750, y=0.78, w=9.00, h=0.22» (line 155) ← [0.78, 1.00]
- «Content area: x=0.600, y=0.787, ends at y≈5.10» (line 156) ← [0.787, 5.10]

Subtitle range [0.78, 1.00] и content [0.787, 5.10] перекрываются — это уже на бумаге, без рендера.

User feedback (verbatim): «Ошибки на всех слайдах - заголовок проваливается вниз за красную линию. Такого раньше не было. От этого и подзаголовок ниже и наезжает на контент. Это грубый баг».

## Scope

In scope:
- Привести «Content Slide Anatomy» в SKILL.md к внутренне непротиворечивому виду. Любой из трёх path'ов ниже допустим — implementer выбирает, обоснование в task notes.
- Обновить и ASCII-диаграмму на line 140-149 чтобы координаты совпадали с цифрами строк 152-156.
- Если выбран path (a) или (b) — patch version bump (0.6.x → 0.6.x+1). Если path (c) — minor (0.7.0), потому что breaking-change для consumer-генераторов, которые могли уже мигрировать на y=0.78 subtitle.
- Обновить пример если есть в SKILL.md (Title Slide / Section Divider не трогать — они отдельные, без red line).

Out of scope:
- Re-rendering canary в stacks. Consumer (stacks TASK-58 follow-up) сделает regenerate уже под фиксованной v0.6.x+1.
- Изменения в шрифтах / типографике — только геометрия Y-зон.
- Изменения content-area размеров (y=5.10 bottom) — только верхняя часть.
- Title Slide / Section Divider layouts.

## Path options (implementer chooses)

- (a) **Shift everything DOWN to accommodate h=0.85 title:** red line y=0.5 → y=0.95 (или 0.90 + gap), subtitle y=0.78 → y=0.97, content y=0.787 → y=1.20. Сохраняет «title fits 2-line wraps» от TASK-24, но теряет ~0.4in content высоты (5.10-1.20 = 3.90in vs 5.10-0.787 = 4.31in). Trade-off acceptable если 2-line wraps реально нужны.
- (b) **Revert title h back to 0.626** и forbid 2-line wraps в spec: title MUST be single-line; если не вмещается — обязательно split на title+subtitle (subtitle же существует именно для этого). Восстанавливает старую геометрию (red line 0.5, subtitle 0.55, content 0.787). TASK-24 title-zone fix откатывается частично — остаётся только Size Scale clarification и shipping postprocess-effectlst.py.
- (c) **Hybrid:** title h=0.85 + `valign: 'top'` (title прижат к верху box'а, для коротких заголовков сидит над red line), red line перемещается DOWN до y=0.85, subtitle y=0.87, content y=1.10. Visually consistent для 1-line и 2-line wraps.

Recommendation: **(c)** — наиболее гибкая и соответствует исходному намерению TASK-24 (поддержать 2-line wraps), без жертвы content area. Но implementer может выбрать (b) если решит что 2-line wraps — анти-паттерн и spec должен принудить к title+subtitle split.

## Files

- `plugins/presentation/skills/pptx-arch-style/SKILL.md` (exists) — секция «Content Slide Anatomy» line ~135-158: цифры, ASCII диаграмма, текстовые «<- title zone» / «<- red line» аннотации, recipe для addTitle helper (AC #1, #2, #3, #4)
- `plugins/presentation/.claude-plugin/plugin.json` (exists) — version bump per chosen path (AC #5)
- `plugins/presentation/skills/pptx-arch-style/references/rules.yaml` (exists) — опционально: добавить soft warning rule «title-text-bottom-below-red-line» (AC #6, опц.)
- `plugins/presentation/skills/pptx-arch-style/scripts/lint.py` (exists) — handler для нового правила если AC #6 (опц.)

## Source

Source: /Users/paul/Private/Alfa/Projects/standard/stacks@ac76f0f7bd1a
Visual reproduction: stacks repo, `presentations/registry/output/doc-6-registry-ak.pptx` (post-TASK-58, под v0.6.1) — все 9 content slides показывают bug на slide 3 особенно очевидно (восстановленный длинный заголовок). Source task: TASK-58 в stacks (Done, commit `ac76f0f`). Related: TASK-24 в claude-skills (Done, commit `d3f8179`) — внёс регрессию.

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
- [x] #1 SKILL.md «Content Slide Anatomy» section внутренне согласован: title text (1-line И 2-line wraps) не выходит за вертикальную границу red line; subtitle Y-range не пересекается с content area Y-range — проверяется арифметически по цифрам в строках секции и визуально на fixture
- [x] #2 Один из 3 path'ов (a/b/c) выбран и реализован, decision и обоснование выбора зафиксированы в task notes
- [x] #3 ASCII диаграмма на строках ~140-149 обновлена чтобы Y-координаты в диаграмме (title zone, red line position, content area) совпадали с числовыми спецификациями в строках ~152-156
- [x] #4 Visual smoke-test fixture: deck с 1-line И 2-line титлами создан под новым recipe, rendered через soffice → pdftoppm → JPEG; проверено что bottom y координата title text не пересекает red line position И top y subtitle не пересекает top y content area
- [x] #5 plugins/presentation/.claude-plugin/plugin.json version bumped per SemVer (patch если (a) или (b); minor если (c) потому что breaking-change для consumer-генераторов мигрировавших на y=0.78 subtitle)
- [x] #6 task-reviewer agent на git diff master..HEAD возвращает APPROVED перед merge
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Decisions locked before Ralph run

- **Path:** (c) Hybrid — title h=0.85 with valign=top, red line moves to y=0.85, subtitle y=0.87 h=0.20, content y=1.10..5.10. Trade-off: short titles sit above red line; 2-line wraps still fit; lose ~0.31in content height (3.90in vs 4.31in original). 2-line wrap support from TASK-24 is preserved, which was the original intent.
- **SemVer:** minor bump 0.6.1 → 0.7.0 (breaking change for consumers already on y=0.78 subtitle).
- **ASCII diagram (line ~140-149):** must show new red line position at y=0.85, content area starting y=1.10.
- **Smoke-test fixture (AC#4):** verify bottom-y of title text (1-line AND 2-line cases) does not cross red line y=0.85; top-y of subtitle text not above red line; top-y of content area not above y=1.10.

Plan (per locked decisions): path (c) Hybrid — title h=0.85 valign=top, red line y=0.85, subtitle y=0.87 h=0.20, content y=1.10..5.10. Minor bump 0.6.1→0.7.0 (breaking). Update SKILL.md Anatomy section (ASCII + numeric specs), Y0 constant in formulas, EMU reference. Build smoke-test fixture deck via python-pptx (1-line + 2-line titles); render to PDF/PNG and assert bottom-y of title < red line y=0.85 and top-y of content > subtitle bottom-y. Skip optional AC#6 rule add (task body marks it опц.; AC list's #6 is task-reviewer approval gate).

Commit: `fb3e169` - task-27: shift title zone for 2-line wraps (path c, v0.7.0)

Commit: `7ebb132` - task-27: fix combined-form snippet y-coord to new content top

Implemented path (c) Hybrid per locked decisions. SKILL.md Anatomy now: title h=0.85 valign=top (y=0..0.85), red line y=0.85 h=0.042 (ends 0.892), subtitle y=0.90 h=0.18 (ends 1.08), content y=1.10..5.10. Y0 constant in formulas bumped 0.87→1.10. Decision-tree and combined-form snippets shifted to fit new Y0. Updated rules.yaml: red-accent-line-coords y=0.85, mandatory/forbid red-line y-band [0.80, 0.90]. Regenerated all fixtures from updated gen_fixtures.js (addRedLine default y=0.85, addContentTitle h=0.85 valign=top, addContentBody y=1.10). Added edge/title-zone-smoke-test.pptx with 1-line+2-line Cyrillic titles. Added test_title_zone_smoke_test_v070_geometry pytest that asserts title bottom ≤ red top, subtitle top ≥ red bottom, subtitle bottom ≤ content top. plugin.json 0.6.1→0.7.0. Reviewer flagged y=0.87 stale in Combined-form snippet line 188; fixed to y=1.10 in commit 7ebb132. APPROVED. uv run pytest → 29 passed. uv run ruff check . → clean.

Commit: `37568b5` - task-27: mark Done after reviewer APPROVED
<!-- SECTION:NOTES:END -->
