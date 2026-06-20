---
id: TASK-24
title: Address pptx-arch-style v0.4.0 canary findings from doc-6 regeneration
status: Done
assignee: []
created_date: '2026-06-20 15:59'
updated_date: '2026-06-20 16:43'
labels:
  - 'feature:pptx-arch-style-validation'
dependencies: []
priority: medium
ordinal: 24000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

Consumer проект stacks прогнал canary-регенерацию существующего deck'а `doc-6-registry-ak.pptx` под `pptx-arch-style` v0.4.0 (после релиза TASK-21 + TASK-22). Линтер сошёлся за 2 итерации (exit 0, 511/0/0), но за время реализации всплыли 3 spec/tooling-гэпа, которые consumer вынужден был обходить локально. TASK-23 закрыл часть post-validation drift'ов (palette-warn, package.json placement, size-scale extension с 7/28/32pt), но эти 3 — отдельные, не пересекающиеся с TASK-23. Они и есть полезный output canary-теста, ради которого validation-фича затевалась — следующая итерация skill'а.

## Scope

In scope:
- Зафиксировать в SKILL.md решение по title-zone height для длинных заголовков на 24pt (finding #1).
- Зафиксировать решение по `<a:effectLst/>` post-processing'у (finding #2) — либо ship canonical script, либо upstream-PR с трекингом.
- Зафиксировать решение по 22pt в Size Scale (finding #3) — либо вернуть в approved scale, либо явная migration note для legacy-decков.
- Bump version (если есть material changes) и обновить CHANGELOG (если файл есть).

Out of scope:
- Slide-8 Cinimex badge overlap — pre-existing в baseline deck'е consumer'а, не связан с v0.4.0; consumer-side defect (исправляется в stacks, не в skill).
- Re-prosecution canary в stacks — после shipping новой версии consumer запустит canary самостоятельно при необходимости (то есть НЕ блокирует merge этой задачи).
- Любые другие spec-edits за пределами трёх описанных findings.

## Findings (detail)

### Finding #1 — Title-zone height не вмещает 2-строчные 24pt русские заголовки

Reference recipe в SKILL.md задаёт title `h=0.626in`, subtitle `y=0.55`. При min 24pt длинные русские заголовки (пример: «Рекомендация: Путь 1 — Camunda 8 как отдельная ИС») оборачиваются на 2 строки (~0.72in) и наезжают на subtitle.

Fix-варианты (на выбор имплементера, обоснование в task notes):
- (a) фиксированная `h=0.85in` + subtitle `y=0.78`;
- (b) soft lint warning с эвристикой (`text_length × avg_char_width vs zone_width`), без принудительного изменения зоны.

### Finding #2 — Rule #11 (`<a:effectLst/>` в каждом `<p:bgPr>`) требует обязательного post-processing'а

pptxgenjs v4.0.1 не эмитит `<a:effectLst/>` для `slide.background = { color: ... }`. Каждый consumer обязан написать post-process скрипт. В stacks написали ~30-строчный PEP 723 inline-скрипт (python-pptx + lxml) и зашили его в pipeline как `node generate-*.js && uv run postprocess-effectlst.py output.pptx`.

Fix-варианты:
- (a) shipping canonical `postprocess-effectlst.py` внутри `plugins/presentation/skills/pptx-arch-style/scripts/` (или JSZip JS-эквивалент);
- (b) upstream PR в pptxgenjs c опцией типа `slide.background.effectOverride: true` — линк на PR в task notes.

Reference implementation от consumer: `presentations/registry/postprocess-effectlst.py` в исходном репо stacks (commit a919ea9).

### Finding #3 — 22pt отсутствует в approved font-size scale, но это de-facto baseline legacy-декое

Approved scale в `rules.yaml` (после TASK-23): `7,8,9,10,10.5,11,12,13,14,15,16,20,24,28,32,36,40.5,52`. Legacy generator в stacks (предшествующий TASK-55) использовал 22pt для content-slide titles — fires `text-runs-use-approved-font-and-size` на каждом title-run. SKILL.md не содержит migration note.

Fix-варианты:
- (a) вернуть 22pt в approved scale (минимум `rules.yaml` + SKILL.md Size Scale row);
- (b) явная нота в SKILL.md → Typography → Size Scale: «Content slide titles must be 24pt, not legacy 22pt; long titles must be split title+subtitle to avoid 2-line wrap» (см. finding #1 связку).

## Files

- `plugins/presentation/skills/pptx-arch-style/SKILL.md` (exists) — для findings #1 (title-zone), #2 (post-processing note или ссылка на ship'нутый скрипт), #3 (22pt migration note)
- `plugins/presentation/skills/pptx-arch-style/references/rules.yaml` (exists) — для finding #3 (22pt re-add), опционально для finding #1 (soft warning rule)
- `plugins/presentation/skills/pptx-arch-style/scripts/lint.py` (exists) — опционально для finding #1 (новая soft warning rule), опционально для finding #3 (если migration note + grandfathering 22pt по условию)
- `plugins/presentation/skills/pptx-arch-style/scripts/postprocess-effectlst.py` (to-create) — для finding #2 если выбран shipping path (а)
- `plugins/presentation/.claude-plugin/plugin.json` (exists) — version bump (0.4.0 → 0.4.1 patch если только clarifications; → 0.5.0 minor если new feature like ship'нутый script)
- `CHANGELOG.md` (check existence) — если есть, добавить запись

## Source

Source: /Users/paul/Private/Alfa/Projects/standard/stacks@8c6f4b88b7bb
Source task in stacks: TASK-57 — "Regenerate doc-6 deck with upgraded pptx-arch-style + linter (canary test)" (Done, commit a919ea9). Полные findings и detail — в Implementation Notes секции `## Handoff candidates back to claude-skills` файла `backlog/tasks/task-57 - Regenerate-doc-6-deck-with-upgraded-pptx-arch-style-linter-canary-test.md` в исходном репо. 4-й finding (slide 8 Cinimex overlap) в этот handoff НЕ включён — он pre-existing и consumer-side.

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
- [x] #1 SKILL.md fixes finding #1: either documents title zone h=0.85in with subtitle y=0.78, OR rules.yaml adds soft warning rule with text-length heuristic for 2-line wrap risk on 24pt titles (choice + rationale documented in task notes)
- [x] #2 Finding #2 resolved: EITHER plugins/presentation/skills/pptx-arch-style/scripts/postprocess-effectlst.py exists and SKILL.md references it as the canonical post-process step, OR an upstream pptxgenjs PR is opened with URL recorded in task notes (and SKILL.md Rule #11 acknowledges the gap with a workaround pointer)
- [x] #3 Finding #3 resolved: EITHER rules.yaml font_spec.sizes_pt list includes 22 AND SKILL.md Size Scale row mentions 22pt, OR SKILL.md Typography section contains explicit migration note: 'Content slide titles must be 24pt, not legacy 22pt; long titles must be split title+subtitle to avoid 2-line wrap' (choice documented in task notes)
- [x] #4 plugins/presentation/.claude-plugin/plugin.json version bumped per SemVer (0.4.0 → 0.4.1 if SKILL.md clarifications only; → 0.5.0 if ship'нутый script or new rule type added); decision documented in task notes
- [x] #5 uv run pytest plugins/presentation/skills/pptx-arch-style/scripts/tests/ passes; uv run ruff check . passes
- [x] #6 task-reviewer agent run on git diff master..HEAD returns APPROVED before merge
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan:
- Finding #1 → option (a): update SKILL.md title-zone to h=0.85, subtitle y=0.78. Rationale: actually fixes the wrap, no spec ambiguity, and the lint heuristic in (b) would still need a manual override.
- Finding #2 → option (a): ship plugins/presentation/skills/pptx-arch-style/scripts/postprocess-effectlst.py (PEP 723 inline-deps python-pptx+lxml). Update SKILL.md Rule #11 and Validation to reference it as the canonical post-process step. Rationale: directly removes consumer copy-paste burden; upstream PR (b) ships value only after pptxgenjs release.
- Finding #3 → option (b): add migration note to SKILL.md Typography Size Scale. Rationale: re-adding 22pt would conflict with the 24pt content-title row and re-open the wrap problem that finding #1 addresses; explicit guidance is safer.
- Version: 0.4.0 → 0.5.0 (minor) — new shipped script counts as a feature.

Commit: `d61bcff` - task-24: pptx-arch-style v0.4.0 canary follow-ups

task-reviewer verdict: APPROVED (review session a00d1c48c540e8a86).
- Confirmed AC#1-5 satisfied via diff.
- Two non-blocking nits flagged and fixed in follow-up commit:
  (a) docstring usage example mentioned a non-implemented --in-place flag — line removed
  (b) redundant bg_pr.append(effect) after etree.SubElement already appends — extra call dropped
- Final tests: 22/22 pass; ruff clean.

Implementation complete. Final state:
- Files: plugins/presentation/skills/pptx-arch-style/SKILL.md (3 finding doc edits), plugins/presentation/skills/pptx-arch-style/scripts/postprocess-effectlst.py (new, ships canonical post-process), plugins/presentation/skills/pptx-arch-style/scripts/tests/test_postprocess_effectlst.py (new, 4 tests), plugins/presentation/.claude-plugin/plugin.json (0.4.0 → 0.5.0).
- Verification: pytest 22/22 passed; ruff check clean; task-reviewer APPROVED.
<!-- SECTION:NOTES:END -->
