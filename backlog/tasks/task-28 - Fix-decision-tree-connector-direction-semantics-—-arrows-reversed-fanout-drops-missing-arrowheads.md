---
id: TASK-28
title: >-
  Fix decision-tree connector direction semantics — arrows reversed, fanout
  drops missing arrowheads
status: Done
assignee: []
created_date: '2026-06-20 21:02'
updated_date: '2026-06-20 21:41'
labels:
  - 'feature:pptx-arch-style-validation'
dependencies: []
priority: high
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Decision-tree component из TASK-25 (v0.5.0 в claude-skills) сейчас ship'нут только как recipe в SKILL.md (Path A — no helper script). При первом applied-canary (stacks TASK-58 slide 4) обнаружились **два дефекта направления связей**, оба прячутся в canonical snippet'е recipe:

1. **Стрелки направлены не в ту сторону.** На ветке «НЕТ → Terminal» расчёт через `hline(slide, 6.10, 7.20, 1.45, true)` — implementer ждёт, что стрелка нарисуется С diamond'а В terminal (LTR). Но в snippet'е `hline` нормализует через `Math.min/Math.abs`, и `endArrowType` в pptxgenjs всегда указывает в сторону max-координаты. На самом слайде 4 у consumer'а реально получилось обратное направление (стрелки **ВХОДЯТ** в diamond вместо того чтобы из него **ВЫХОДИТЬ**) — направление связи семантически потеряно при нормализации.
2. **Из fanout-branches не выходят стрелки.** Helper `vline` в snippet'е не принимает `withArrow` параметр вообще — все вертикальные drops T-junction'а это plain LINE без `endArrowType`. На fanout-row у consumer'а из «План Б» получаются 3 БЕЗ-стрелочные палки вместо arrowheads на каждом терминале.

User feedback (verbatim): «левые зеленые стрелки входят в ромб, а должны выходить. Из плана Б выходят просто линии, а не стрелки».

Корневая причина — recipe не определяет **direction semantics** для connectors. Snippet принимает `(x1, x2)` без указания «откуда → куда»; `Math.min` гарантирует, что OOXML direction (cNvSpPr flipH/flipV) всегда задаётся от меньшей к большей координате, и `endArrowType` ставит arrowhead на той стороне. Если semantic direction parent→child противоположна координатной — стрелка указывает не туда.

Connectors-spec в SKILL.md (line 452): «1.0pt solid #595959, headEnd { type: "triangle", w: "sm", len: "sm" } on the final segment only.» — указано «**final segment only**», но (i) не определено, какой segment final для multi-leg L-bend (vertical-then-horizontal vs horizontal-then-vertical), (ii) для T-junction fanout не указано что arrowhead обязателен на каждой N-th vertical drop.

## Scope

In scope:
- Зафиксировать direction-semantics convention в SKILL.md «Connectors» / «Decision tree» секции (line 450-466): connector принимает **(parent, child)** или **(from, to)**, а НЕ symmetric `(x1, x2)`. Arrowhead ставится на конце near child/to. Для L-bend: final segment = тот, что upcasts child position; arrowhead на нём.
- Переписать `hline` / `vline` helper'ы в canonical snippet (line 489-501) чтобы:
  - принимать `from` / `to` (или явное `withArrow: 'end' | 'start' | 'none'`), а НЕ нормализованные `Math.min/Math.abs`;
  - корректно эмитить OOXML direction (`flipH="1"` или `flipV="1"` когда `to.x/y < from.x/y`) и `endArrowType` на семантически верной стороне.
- Опционально: ship `decision-tree.js` helper file (Path B из TASK-25 — был ОПЦИОНАЛЬНО, не сделано в TASK-25) с правильной direction-semantics. Это снимает с consumer'а вообще необходимость воспроизводить логику. Decision и обоснование в task notes.
- Добавить fanout-arrow rule: вертикальные drops T-junction'а к терминалам должны иметь `endArrowType: 'triangle'` на каждой ножке (только bus-перекладина без arrowhead).
- Опционально: новое lint rule (severity: warning) ловящее LINE без `endArrowType` среди decision-tree-таггированных или среди шорт-flow connectors.

Out of scope:
- Re-rendering canary в stacks (отдельный consumer-side follow-up на TASK-58).
- Изменения цветов / толщины / стиля arrowhead — только направление и наличие.
- Connectors вне decision-tree (например на flow-диаграммах — другая семантика).

## Files

- `plugins/presentation/skills/pptx-arch-style/SKILL.md` (exists) — «Connectors» подсекция Decision tree (line ~450-466), canonical snippet (line ~470-517) (AC #1, #2)
- `plugins/presentation/skills/pptx-arch-style/scripts/decision-tree.js` (to-create, опц.) — helper с правильной direction-semantics (AC #3)
- `plugins/presentation/skills/pptx-arch-style/references/rules.yaml` (exists) — опц. новое правило (AC #4)
- `plugins/presentation/skills/pptx-arch-style/scripts/lint.py` (exists) — handler нового правила если AC #4
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/fixtures/` (exists) — fixture pair (wrong-direction violator vs right-direction clean) если AC #4 (AC #5)
- `plugins/presentation/.claude-plugin/plugin.json` (exists) — version bump (patch если только recipe-fix; minor если ship'нут decision-tree.js helper) (AC #6)

## Source

Source: /Users/paul/Private/Alfa/Projects/standard/stacks@ac76f0f7bd1a
Visual reproduction: stacks repo `presentations/registry/output/doc-6-registry-ak.pptx` slide 4 — стрелки ветки «НЕТ» входят в diamond, fanout-drops без arrowheads. Reference: stacks `presentations/registry/generate-doc-6-registry.js` slide 4 block (использует canonical snippet из SKILL.md почти 1:1). Связанные tasks: TASK-25 в claude-skills (Done, commit `0225c04`) — внёс recipe без direction-semantics; TASK-58 в stacks (Done, commit `ac76f0f`) — первый applied canary, surfaced два дефекта.

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
- [x] #1 SKILL.md Connectors / Decision tree section содержит явную direction-semantics convention: connector принимает (from, to) или (parent, child), а НЕ симметричные (x1, x2). Arrowhead ставится на конце near child/to независимо от Math.min/Math.max нормализации координат
- [x] #2 Canonical snippet hline/vline helpers в SKILL.md переписаны: принимают from/to (или явный withArrow direction), корректно эмитят OOXML flipH/flipV когда target < source, и endArrowType ставится на семантически правильной стороне
- [x] #3 T-junction fanout pattern в SKILL.md явно требует endArrowType triangle на каждой вертикальной drop к терминалу; bus-перекладина без arrowhead. Spec-text присутствует в Decision tree section подсекции T-junction
- [x] #4 Опц.: ship scripts/decision-tree.js helper с правильной direction-semantics API. Если ship'нут — задокументирован в SKILL.md с примером usage; если НЕ ship'нут — decision и обоснование (recipe достаточен) в task notes
- [x] #5 Опц.: lint rule (severity: warning) детектирующий минимум один defect-класс — connector без endArrowType ИЛИ connector с координатной direction обратной semantic. Implementer выбирает класс детекции, обоснование в task notes. Если rule ship'нут — fixture pair в scripts/tests/fixtures/
- [x] #6 plugins/presentation/.claude-plugin/plugin.json version bumped per SemVer (patch если recipe-fix only; minor если ship'нут decision-tree.js helper или новое lint rule)
- [x] #7 task-reviewer agent на git diff master..HEAD возвращает APPROVED перед merge
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Decisions locked before Ralph run

- **Ship scripts/decision-tree.js helper (AC#4):** YES. Consumer just calls drawDecisionTree(slide, spec); removes any chance of re-introducing direction-semantics drift in the recipe-translation step.
- **Ship lint rule (AC#5):** YES. Detect connector LINE without endArrowType among decision-tree-tagged connectors (simpler class, easier to implement than reversed-direction detection). Fixture pair required.
- **SemVer:** minor bump 0.6.1 → 0.7.0 (helper file is new public surface; if TASK-27 also runs first and bumps to 0.7.0, this stays at 0.7.0 with both changes accumulated; if TASK-28 runs first, then 0.6.1 → 0.7.0 and TASK-27 then 0.7.0 → 0.8.0 because TASK-27 is also breaking).
- **API shape for helper:** drawDecisionTree(slide, spec) where spec.connectors carries explicit (from, to) coordinates and optional withArrow direction; never symmetric (x1, x2). Document in SKILL.md with at least one usage example.

Plan: (1) Update SKILL.md Connectors section + canonical snippet to use (from,to) direction-semantics + arrowheads on every T-junction drop. (2) Ship scripts/decision-tree.js helper with drawDecisionTree(slide, spec) API. (3) Add lint rule for connector LINE without endArrowType in decision-tree context + fixture pair. (4) Bump plugin.json 0.7.0→0.8.0 (minor).

Commit: `1baa613` - task-28: fix decision-tree connector direction semantics

Commit: `a5ff580` - task-28: address reviewer nits — dead-code, comment accuracy, XPath

Reviewer APPROVED (round 1 + nits). All 7 AC met. AC#5 detection-class rationale: chose missing-arrowhead class (vs reversed-direction) because (a) directly catches the user's primary defect class verbatim ("Из плана Б выходят просто линии, а не стрелки"), (b) detectable from OOXML alone via <a:headEnd>/<a:tailEnd>, (c) reversed-direction detection would require semantic-direction knowledge not present in the .pptx XML. Rule scope narrowed to vertical (w_max=0.05) gray LINEs at y_min=3.6 (terminal band) — avoids false positives on bus/bus-drop intermediates in the T-junction pattern; narrow scope is a known limitation but matches the canonical layout exactly. Helper file decision: shipped per task-notes direction; module exports drawDecisionTree(slide, spec) + building-block helpers; consumers can import once instead of replicating the recipe.
<!-- SECTION:NOTES:END -->
