---
id: TASK-25
title: Add decision-tree component recipe to pptx-arch-style
status: Done
assignee: []
created_date: '2026-06-20 16:13'
updated_date: '2026-06-20 17:12'
labels:
  - 'feature:pptx-arch-style-validation'
dependencies: []
priority: medium
ordinal: 25000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Consumer-проект stacks при canary-регенерации `doc-6-registry-ak.pptx` (TASK-57 в stacks) хэнд-роллил собственное «дерево решений» на slide 4 — получилось визуально сломано: диагональные линии вместо ортогональных L-bend'ов, decision-точки заданы italic-текстом без анкор-фигуры, fanout «План Б → 3 пути» нарисован как лучи из одной точки, НЕТ/ДА — плавающие подписи. Это типичная задача архитектурной презы (decision-tree — стандартный component рядом с layer-block'ом, distribution bar'ом, badge'ом, table'ом), но в pptx-arch-style этого component'а нет.

Линтер v0.4.0 этот дефект не поймал: правила проверяют шрифты / палитру / page badge / theme placeholders, но не топологию графа (orthogonal-ность connector'ов, наличие фигуры для decision-точек, T-junction для fanout'ов). Visual subagent в TASK-57 тоже пропустил — сравнивал с baseline, а baseline (TASK-55 в stacks) имел тот же дефект. Surfaced только на ручном ревью.

Цель: добавить canonical decision-tree component в pptx-arch-style чтобы consumers (stacks и будущие) не катали broken drawings заново. Это новый component-уровень spec, не clarification — поэтому отдельный handoff (sibling к TASK-24, не AC внутри).

## Scope

In scope:
- Добавить секцию «Decision tree» в SKILL.md (component recipe + canonical pptxgenjs snippet).
- Опционально: ship helper-скрипт `decision-tree.js` с auto-routing API.
- Опционально: добавить lint rule (severity: warning) ловящий 1+ из 4 defect-классов.
- Если helper или lint rule — то и фикстуры в `scripts/tests/` + тест.
- Version bump per SemVer.

Out of scope:
- Re-running canary в stacks. Consumer запустит свой regenerate slide-4 task самостоятельно после shipping.
- Полный auto-layout для произвольных графов. Только conventions + опционально simple helper для линейных деревьев (root → branches → leaves).
- Поддержка не-decision диаграмм (sequence, ER, swimlane и т.п.) — это другой component-cycle.
- Любые правки в других секциях SKILL.md за пределами «Decision tree».

## Path options (implementer chooses)

- (a) **Минимум — recipe в SKILL.md:** новая секция «Decision tree» рядом с layer-block / distribution bar. Описывает: какой shape для decision (рекомендую DIAMOND), какие fills/borders (вписать в существующую палитру), как рисовать connector'ы (только orthogonal L-bend'ы из 2-3 LINE shapes), как позиционировать НЕТ/ДА (на изломе). + canonical pptxgenjs snippet 30-50 LOC.
- (b) **Лучше — shipped helper:** скрипт `plugins/presentation/skills/pptx-arch-style/scripts/decision-tree.js` экспортирующий `drawDecisionTree(slide, nodes, edges, opts)` с auto-routing. Consumers вызывают вместо хэнд-роллинга.
- (c) **Дополнительно — lint rule:** новое правило в `rules.yaml` (severity: warning) которое ловит хотя бы один defect-класс из reference: (i) LINE shape с одновременно ненулевыми `w` И `h` (диагональ — `abs(w) > eps && abs(h) > eps`), (ii) fanout-from-single-point pattern (3+ LINE shapes начинаются из одной точки), (iii) decision-text-without-shape (italic addText без соседнего DIAMOND/ROUND_RECT shape).

Path (a) обязателен. (b) и (c) — на усмотрение, decision и обоснование в task notes.

## Reference: 4 класса defects в stacks slide 4 (для дизайна fixtures)

1. **Диагональные connector'ы вместо ортогональных L-bend'ов:** `drawArrow(x1,y1,x2,y2)` в stacks рисует ОДИН LINE shape с `w=x2-x1, h=y2-y1` — на развилках НЕТ/ДА это slash от центра к боковому листу.
2. **Fanout «План Б → 3 пути» как лучи:** 3 отдельных LINE shape, каждый из центральной точки своего веера — нужна T-junction (вниз → горизонтальная шина → 3 вертикали вниз).
3. **Decision-точки = просто italic addText:** без анкор-фигуры (DIAMOND / ROUND_RECT pill). Текст «Минцифры оспорила трактовку?» висит в воздухе.
4. **НЕТ/ДА — плавающие подписи:** addText с произвольными офсетами, не привязаны к изломам connector'ов.

## Files

- `plugins/presentation/skills/pptx-arch-style/SKILL.md` (exists) — добавить секцию «Decision tree» (AC #1, обязательно)
- `plugins/presentation/skills/pptx-arch-style/scripts/decision-tree.js` (to-create) — для path (b), опционально (AC #2)
- `plugins/presentation/skills/pptx-arch-style/references/rules.yaml` (exists) — для path (c), опционально (AC #3)
- `plugins/presentation/skills/pptx-arch-style/scripts/lint.py` (exists) — добавить handler нового правила если path (c)
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/` (exists) — violator fixture + test (AC #4, если path b или c)
- `plugins/presentation/.claude-plugin/plugin.json` (exists) — version bump (AC #5)

## Source

Source: /Users/paul/Private/Alfa/Projects/standard/stacks@8c6f4b88b7bb
Reference broken implementation: stacks repo `presentations/registry/generate-doc-6-registry.js` lines 384-567 (SLIDE 4 block); output slide 4 of `presentations/registry/output/doc-6-registry-ak.pptx`. JPEG preview можно собрать через `soffice --headless --convert-to pdf` + `pdftoppm -f 4 -l 4 -r 120 -jpeg`. Связанные handoff'ы в claude-skills: TASK-23 (Done, validation follow-ups), TASK-24 (canary spec clarifications).

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
- [x] #1 SKILL.md contains a new 'Decision tree' section describing: shape for decision nodes (DIAMOND recommended) with palette-conformant fill/border; convention for orthogonal connectors built from 2-3 LINE shapes (no diagonals); positioning rule for НЕТ/ДА labels at connector bends; T-junction pattern for fanouts (down → horizontal bus → vertical drops). Section includes a canonical 30-50 LOC pptxgenjs snippet that consumers can copy
- [x] #2 Path (b) decision: if shipped, plugins/presentation/skills/pptx-arch-style/scripts/decision-tree.js exists and exports drawDecisionTree(slide, nodes, edges, opts) with auto-routing; SKILL.md references it as recommended usage; covered by a test in scripts/tests/. If skipped, decision and rationale recorded in task notes
- [x] #3 Path (c) decision: if shipped, rules.yaml contains a new rule (severity: warning) catching at least one defect class: diagonal connector (LINE with both abs(w) > eps AND abs(h) > eps), fanout-from-single-point (3+ LINE shapes starting from one point), or decision-text-without-shape (italic addText with no adjacent DIAMOND/ROUND_RECT). Chosen class(es) and rationale recorded in task notes. If skipped entirely, rationale recorded in task notes
- [x] #4 If path (b) or (c) shipped: scripts/tests/ includes a violator fixture reproducing at least one defect class from the reference; lint.py emits a warning (exit 2) on it; a canonical clean fixture (generated via decision-tree.js or hand-built per SKILL.md recipe) exits 0
- [x] #5 plugins/presentation/.claude-plugin/plugin.json version bumped per SemVer: patch (0.4.0 → 0.4.1) if only SKILL.md recipe shipped; minor (0.4.0 → 0.5.0) if helper script OR new lint rule shipped. Decision recorded in task notes
- [x] #6 task-reviewer agent run on git diff master..HEAD returns APPROVED before merge
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: (a) extend SKILL.md Decision Tree section with shape (DIAMOND), orthogonal connectors, T-junction, branch labels, + 30-50 LOC pptxgenjs snippet. (b) SKIP helper script — skill ships specs not runtime libs. (c) SHIP orthogonality lint rule (LINE shape with both w>0.05in AND h>0.05in = diagonal, warning). Add shape_type match key + is_line_shape helper to lint.py. Add violator (diagonal LINE) + clean (orthogonal LINE) fixtures. Version 0.5.0 → 0.6.0 (minor, new rule).

Path decisions:

(a) RECIPE — shipped. SKILL.md → Diagram Conventions → Decision Tree Diagrams now describes: DIAMOND shape with #FFF2CC/#D6B656 palette (already in spec), orthogonal-only connectors (each LINE segment purely vertical w=0 OR purely horizontal h=0), T-junction fanout pattern (drop → bus → N drops, not N rays), branch label anchoring at connector bends (НЕТ/ДА at corner_x+0.05). Includes ~45 LOC canonical pptxgenjs snippet covering root decision + L-bend + sub-decision + T-junction fanout to 3 terminals.

(b) HELPER SCRIPT — SKIPPED. Reason: the skill ships specs not runtime libraries (gen_fixtures.js is a test-only script, not a consumer-facing API). A shipped drawDecisionTree() helper would expand the skill's responsibility scope to library maintenance and force a Node runtime on every consumer. The SKILL.md snippet is a 45-LOC copy-paste that consumers can adapt — that's the right altitude. Reconsider if 2+ consumers report the snippet is too rigid for their layouts.

(c) LINT RULE — shipped. decision-tree-connector-orthogonal (severity: warning) catches defect class #1 from the stacks reference (diagonal LINE connector with w=x2-x1, h=y2-y1). Implementation: new shape_match key shape_type=line (matches prstGeom 'line') combined with w_min=0.05 AND h_min=0.05 (both axes non-trivial → diagonal). Classes #2/#3/#4 (fanout-rays, decision-text-without-shape, floating labels) need cross-shape topology analysis (point-clustering / sibling-shape proximity) that's beyond the current flat-shape matcher; they remain visual-review responsibilities, documented in SKILL.md.

Version bump: 0.5.0 → 0.6.0 (minor — new lint rule shipped, per AC#5).

Files changed:
- plugins/presentation/skills/pptx-arch-style/SKILL.md (expanded Decision Tree section + 45-LOC snippet + defect-class list)
- plugins/presentation/skills/pptx-arch-style/references/rules.yaml (new rule, doc shape_type key)
- plugins/presentation/skills/pptx-arch-style/scripts/lint.py (shape_preset_geom helper + shape_type matcher)
- plugins/presentation/skills/pptx-arch-style/scripts/tests/gen_fixtures.js (violator + clean fixtures)
- plugins/presentation/skills/pptx-arch-style/scripts/tests/test_lint.py (2 new tests)
- plugins/presentation/skills/pptx-arch-style/scripts/tests/fixtures/{violators,edge}/decision-tree-*.pptx (regenerated)
- plugins/presentation/.claude-plugin/plugin.json (0.5.0 → 0.6.0)

Validation: 28 tests pass (20 lint + 3 postprocess + 4 books, prior suite intact), ruff clean. Violator exits 2 with the warning; clean fixture exits 0; golden fixture still exits 0.

task-reviewer (Round 1) returned APPROVED with one non-blocking nit: in the canonical snippet, the NO-branch had a degenerate vline (y1==y2) and the hline started at x=5.00 which is inside the root diamond (spans x=[3.90,6.10]). Fixed: dropped the dead vline, made NO branch a straight horizontal arrow from root's right edge (6.10) to NO terminal's left edge (7.20) at y=1.45, with comment clarifying that coplanar shapes need no L-bend (rule forbids diagonals, not straight runs). Also relabeled YES/NO sides for clarity and tightened consts (YELLOW_FILL→YF etc) — snippet went 47→45 LOC, still within 30-50 range. Tests + ruff still green (28 passed).

All AC met; tests green (28 passed); ruff clean; version 0.6.0; task-reviewer APPROVED Round 1 with non-blocking snippet-geometry nit which was fixed in follow-up edit (degenerate vline removed, NO branch simplified to coplanar horizontal arrow).
<!-- SECTION:NOTES:END -->
