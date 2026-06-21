---
id: TASK-31
title: >-
  Revert title-zone to v0.2.0 anatomy — red line is brand-constant under page
  badge, forbid 2-line title wraps
status: Done
assignee: []
created_date: '2026-06-21 06:14'
updated_date: '2026-06-21 06:32'
labels:
  - 'feature:pptx-arch-style-validation'
dependencies: []
priority: high
ordinal: 31000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Третий applied canary (stacks TASK-59 под v0.8.1) показал что title-zone fix v0.7.0 (path c, hybrid: red line y=0.500→0.850, content y=0.787→1.100, addTitle valign='top') **архитектурно неверен**. User feedback после TASK-59 рендера (verbatim): «Ошибки на всех слайдах - заголовок проваливается вниз за красную линию. Такого раньше не было... Это очень простой вопрос, но ты 3-й раз не можешь сделать нормально. ... есть блок номера, красная линия идет ровно под ним. Над красной линией - Заголовок. Как в baseline 0.2.0».

**Корневая ошибка трёх раундов фиксов (TASK-24 → TASK-27 → TASK-59 canary verify)**: red line трактовалась как movable layout variable. На самом деле red line — это **структурная константа deck'а под page-badge'ом, бренд-уровня**. Её НЕЛЬЗЯ двигать. Правильная переменная всё это время была не геометрия зоны, а **длина заголовка**: 2-line wraps запрещены, длинные титлы расщепляются на title+subtitle (для чего subtitle и существует). v0.2.0 это знал; «Legacy 22pt migration» нота в текущей SKILL.md (line ~87) даже это admits — «Long titles must be split into title + subtitle» — но рекомендация оставлена как soft advice, а layout v0.7.0 пытался её обойти расширением зоны.

### Что v0.7.0 сделал не так

Сравнение с **_baseline_v0.2.0.pptx** (extracted из stacks `presentations/registry/output/_baseline_v0.2.0.pptx` slide2.xml через unzip+regex):

| element | v0.2.0 baseline (correct) | v0.7.0 SKILL.md (wrong) | comment |
|---|---|---|---|
| page-badge | y=0, h=0.518 | y=0, h=0.518 | unchanged ✓ |
| **red line** | **y=0.500** под badge'ом | y=0.850 — оторван от badge | brand-constant moved ✗ |
| title text-box | y=0, h=0.626, valign:middle | y=0, h=0.850, valign:top | расширен под 2-line wrap ✗ |
| subtitle | y=0.550, h=0.220 (под red line) | y=0.900, h=0.180 (под раздутым title) | сдвинут вниз вслед за red line ✗ |
| content top | y=1.10 (slide-2 первый shape) | y=1.10 | unchanged ✓ |

В v0.2.0 24pt single-line title text (~0.30in высоты) сидит valign:middle в box [0, 0.626] → центр y=0.313, text bottom ~y=0.463 — выше red line top y=0.500 с маржой ~0.04in. Работает для всех slide titles ≤ ~50 Cyrillic chars (помещаются single-line в 9.234in). Для slide-3 длинного титла в doc-6 (53 chars: «Рекомендация: Путь 1 — Camunda 8 как отдельная ИС») v0.2.0 design требует split: title «Рекомендация: Путь 1», subtitle «Camunda 8 как отдельная ИС · ...».

## Scope

In scope:
- **Revert** Content Slide Anatomy section в SKILL.md (line ~135-158) к v0.2.0 geometry: red line y=0.500, title h=0.626 valign='middle', subtitle y=0.550 h=0.220, content y=0.787.
- **Strengthen** «no 2-line wraps» из soft advice (line ~87) до hard spec rule: title MUST быть single-line at 24pt; если контент не помещается — implementer MUST split на title+subtitle.
- Опционально: ship lint rule (severity: warning) детектирующий title text-run превышающий character-count threshold (рекомендую ~50 Cyrillic chars / ~60 Latin chars для 9.234in зоны при 24pt; точная константа в task notes).
- Опционально: lint rule детектирующий title placement выходящий за red line (text bottom > 0.500).
- Update ASCII диаграмму на line ~140-149 чтобы Y-координаты соответствовали восстановленным значениям.
- Добавить short ADR-style нота в SKILL.md (отдельный блок либо в Content Slide Anatomy либо в Legacy section): «v0.7.0 ошибочно подвинул red line с y=0.500 на y=0.850 пытаясь absorb 2-line wraps. Это нарушило brand invariant (red line должен сидеть под page-badge'ом). v0.9.0 откатывает: red line снова под badge, 2-line wraps forbidden — длинные титлы MUST split в title+subtitle.» Подробность важна чтобы будущие итерации не пытались снова «починить» расширением зоны.
- Version bump 0.8.1 → 0.9.0 (minor — breaking change для consumer-генераторов мигрировавших на v0.7.0 layout; они MUST вернуться к v0.2.0 геометрии).

Out of scope:
- Изменения в Title Slide / Section Divider (они не используют red line — отдельная anatomy).
- Изменения в типографике (24pt size, FONT_TITLE/FONT_BODY) — только geometry.
- Re-rendering canary в stacks. Consumer запустит свой следующий regenerate task самостоятельно после v0.9.0 ship.
- TASK-28 (connector direction) и TASK-29 (overlay criterion) — оба ушли в v0.8.0 и v0.8.1 без претензий, не трогаем.

## Files

- `plugins/presentation/skills/pptx-arch-style/SKILL.md` (exists) — Content Slide Anatomy section (line ~135-158): revert numbers, ASCII диаграмма, addTitle/addChrome reference snippets; «Legacy 22pt migration» secton (line ~87): tighten advice → hard rule (AC #1, #2, #3, #5)
- `plugins/presentation/skills/pptx-arch-style/references/rules.yaml` (exists) — опционально lint rule(s) (AC #4)
- `plugins/presentation/skills/pptx-arch-style/scripts/lint.py` (exists) — handler нового правила(л) если AC #4
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/fixtures/` (exists) — fixture pair (2-line-title violator vs single-line-clean) если AC #4
- `plugins/presentation/.claude-plugin/plugin.json` (exists) — version bump 0.8.1 → 0.9.0 (AC #6)

## Source

Source: /Users/paul/Private/Alfa/Projects/standard/stacks@0829c3a
Ground-truth reference: stacks repo `presentations/registry/output/_baseline_v0.2.0.pptx` slide 2 — extracted geometry в Why section выше. Failing render: stacks `presentations/registry/output/doc-6-registry-ak.pptx` (post-TASK-59, под v0.8.1) — все 9 content slides показывают bug. Связанные claude-skills tasks: TASK-24 (Done, v0.4.1, внёс первичную регрессию), TASK-27 (Done, v0.7.0, «починил» сдвигом red line — НЕПРАВИЛЬНАЯ переменная), TASK-29 (Done, v0.8.1, overlay criterion — не связано, не трогать). Stacks canary tasks: TASK-58 (Done, surfaced регрессию), TASK-59 (Done, formal AC «titles не пересекают red line» прошёл tautologically — line к этому моменту уже стоял не там).

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
- [x] #1 SKILL.md Content Slide Anatomy section возвращён к v0.2.0 geometry: red line y=0.500 h=0.042; title text-box y=0 h=0.626 valign='middle'; subtitle y=0.550 h=0.220; content area начинается с y=0.787 (per-slide top могут быть выше но не ниже)
- [x] #2 ASCII диаграмма на line ~140-149 SKILL.md обновлена чтобы Y-координаты в диаграмме точно соответствовали реверт-значениям (red line под page-badge, title зона над red line, subtitle под red line)
- [x] #3 «No 2-line title wraps» promoted из soft advice в Legacy 22pt migration section до hard spec rule в Content Slide Anatomy: title MUST быть single-line at 24pt; длинные титлы MUST split в title + subtitle. Формулировка явно forbidding 2-line wraps
- [x] #4 Опц.: lint rule (severity: warning) в rules.yaml детектирующий title text-run превышающий character-count threshold ИЛИ title placement с text bottom > red line top. Implementer выбирает класс детекции и константы, обоснование в task notes. Если rule ship'нут — fixture pair в scripts/tests/fixtures/
- [x] #5 ADR-style нота в SKILL.md (внутри Content Slide Anatomy или отдельный блок) объясняет архитектурную ошибку v0.7.0 (red line подвинут вниз чтобы absorb 2-line wraps — нарушен brand invariant) и обоснование v0.9.0 revert. Цель — предотвратить повторение pattern'а в будущих итерациях
- [x] #6 plugins/presentation/.claude-plugin/plugin.json version bumped 0.8.1 → 0.9.0 (minor, breaking change для consumer-генераторов мигрировавших на v0.7.0 layout)
- [x] #7 task-reviewer agent на git diff master..HEAD возвращает APPROVED перед merge
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: 1) Revert Content Slide Anatomy section in SKILL.md to v0.2.0 geometry — red line y=0.500 h=0.042, title h=0.626 valign='middle', subtitle y=0.550 h=0.220, content starts y=0.787. 2) Rewrite the ASCII diagram with the reverted Y values. 3) Strengthen 'no 2-line title wraps' from Legacy 22pt advice into a hard rule inside Content Slide Anatomy. 4) Skip optional lint rule (AC #4 is OPTIONAL — keeps surface area minimal, easy to ship later) — note in completion. 5) Add ADR note explaining v0.7.0 → v0.9.0 architectural lesson. 6) Bump plugin.json 0.8.2 → 0.9.0. 7) Update Rule #3, Rule #10, Dynamic Layout Y0, EMU Reference for consistency. 8) Run ruff + pytest + lint smoke. 9) task-reviewer agent on git diff master..HEAD.

Commit: `a08989a` - task-31: revert title-zone to v0.2.0 anatomy (v0.9.0)

Commit: `d323fc6` - task-31: fix stale Y0=1.10 reference in Category Cards section

Done. SKILL.md Content Slide Anatomy reverted to v0.2.0 geometry (red line y=0.500, title h=0.626 valign='middle', subtitle y=0.550, content y=0.787). 'No 2-line title wraps' promoted to hard rule with explicit ~50 Cyrillic / ~60 Latin character thresholds. ADR note added explaining v0.7.0 architectural mistake (treating brand-constant red line as movable) and the v0.9.0 rationale. Rules.yaml y-bands and red-accent-line-coords updated to enforce the reverted geometry. gen_fixtures.js + test_lint.py + all .pptx fixtures regenerated against v0.9.0 anatomy; title-zone smoke test rewritten to demonstrate the canonical title+subtitle split. Stale Y0=1.10 reference in Category Cards subsection fixed in a follow-up commit after task-reviewer flagged it. AC #4 (optional lint rule) deliberately skipped — out of scope for the revert; existing red-accent-line-coords rule at y=0.500 ± 0.005 already catches the v0.7.0 line-position failure mode at error severity. plugin.json 0.8.2 → 0.9.0. task-reviewer APPROVED on git diff master..HEAD after Y0 fix. Tests 32/32, ruff clean.

AC #4 checked as 'done' meaning: deliberately skipped per its 'Опц.' (optional) prefix in the task spec. Rationale: revert is the minimum viable change to restore brand invariant; the optional lint rule would require new shape_match keys (text-length matcher or shape-bottom-vs-red-line-top matcher) in the lint engine, plus a fixture pair, plus rule wiring — all of which expand scope beyond the revert. The existing red-accent-line-coords rule (now expecting y=0.500 at error severity) already catches the most damaging failure mode (a generator leaves the line at v0.7.0 y=0.850). A future task can layer the optional warning rule on top if visual review proves the error-severity rule insufficient.
<!-- SECTION:NOTES:END -->
