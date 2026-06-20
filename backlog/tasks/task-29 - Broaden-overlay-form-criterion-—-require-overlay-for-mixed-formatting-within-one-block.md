---
id: TASK-29
title: >-
  Broaden overlay-form criterion — require overlay for mixed formatting within
  one block
status: In Progress
assignee: []
created_date: '2026-06-20 21:03'
updated_date: '2026-06-20 21:45'
labels:
  - 'feature:pptx-arch-style-validation'
dependencies: []
priority: medium
ordinal: 29000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

TASK-26 (v0.6.0/0.6.1) ship'нул convention «combined shape+text default, overlay only when 2+ labels at distinct positions». При applied-canary (stacks TASK-58) consumer применил convention к slide 7 «План Б: 4 пути» — 4 жёлтых под-блока, каждый с **заголовком + body-text разного форматирования внутри одного визуального блока**. Consumer честно использовал combined `addText({shape:...})` — получился ОДИН text run с конкатенированным контентом, без типографической дифференциации title vs body. Визуально слайд деградировал.

User feedback (verbatim): «На слайде 7 - желтые подблоки, внутри надписи разного дизайна, они должны быт отдельными надписями накладываться, как на слайде 8. Встроенная надпись блока используется только в простых случаях - последовательная надпись без разного форматирования. Если появляется заголовок - то надпись должна быть отдельным объектом».

Сейчас в SKILL.md (line 197):
> The legacy overlay form ... is permitted **only** when one block carries TWO OR MORE labels at distinct positions

Это **слишком узкий критерий**. Spec'у нужно расширить условие overlay'я на ситуации с **разным форматированием** в одном блоке, даже если визуально labels стоят последовательно (заголовок + body). Combined form подходит ТОЛЬКО когда:
- одна текстовая строка, либо
- многострочный run с ОДНИМ типографическим стилем (один font/size/weight/color).

Reference паттерн как надо — slide 8 в `doc-6-registry-ak.pptx` (Farzoom/Cinimex cards): card body = `addShape` + 2-3 `addText` (title bold + body regular + footer note). У consumer'а на slide 8 это сделано правильно (overlay, с inline justification). А slide 7 question-cards сделаны combined под текущий слишком узкий spec.

pptxgenjs technically поддерживает mixed-format в одном shape через `text: [{text:'Title', options:{bold:true,fontSize:13}}, {text:'\n', options:{}}, {text:'body', options:{fontSize:10}}]` — но это (i) криптично, (ii) не enforce'ит правильный layout (нет «title рядом» / «body снизу» — всё в одном flow), (iii) трудно мейнтейнить. Overlay чище.

## Scope

In scope:
- Переписать критерий выбора combined vs overlay в SKILL.md «Shape+Text Composition» section (line ~180-211): combined form — default ТОЛЬКО для single-style text (один font/size/weight/color, без heading+body разделения). Overlay form — required когда блок содержит:
  - 2+ labels at distinct positions (как сейчас в spec), ИЛИ
  - один блок с разным форматированием частей (title+body, big-number+caption, header+footer и т.п.), даже если labels visually последовательны.
- Привести 2-3 canonical examples в SKILL.md показывающих:
  - (i) когда combined OK (просто label на блоке, без heading);
  - (ii) когда overlay required из-за multi-position (текущий пример с title+footer-tag);
  - (iii) когда overlay required из-за multi-format в одном position (новый пример: card с bold title + regular body снизу).
- Обновить inline-justification comment template: текущий «// Overlay justified: 2+ labels at distinct positions» расширить до «// Overlay justified: 2+ labels OR mixed formatting (title+body)» — указать который критерий.
- Опционально: lint rule (severity: info) детектирующий блок с combined form содержащий `\n` + признаки mixed-format (например: `text` с `\n` И `fontSize` указан И блок широкий → потенциальный candidate на overlay-refactor).
- Опционально: refactor canonical snippets в SKILL.md (если есть question-card / stat-callout / любые блоки с heading+body) на overlay form.

Out of scope:
- Re-rendering canary в stacks (consumer follow-up).
- Refactor combined→overlay в legacy consumer-генераторах (grandfathered per текущий «refactor recommended not required»).
- Поддержка mixed-format через pptxgenjs `text:[...]` array form — explicit anti-pattern, не рекомендовать.

## Reference

Right pattern (overlay because mixed-format): smb_8 Farzoom/Cinimex cards в `doc-6-registry-ak.pptx` slide 8 — outer roundRect + bold title addText (top) + regular body addText (middle) + small footer-tag addText (bottom).

Wrong pattern (combined because spec слишком узкий): smb_8 question-cards на slide 7 — `addText({shape: ROUND_RECT, text: "Title\nbody line 1\nbody line 2", ...})` — всё в одном run, без типографической дифференциации. На рендере: монолитный текст без визуальной иерархии «заголовок vs пояснение».

Reference source: `/Users/paul/Private/Alfa/Projects/standard/stacks/presentations/registry/generate-doc-6-registry.js` — slide 7 vs slide 8 implementations.

## Files

- `plugins/presentation/skills/pptx-arch-style/SKILL.md` (exists) — «Shape+Text Composition» section (line ~180-211): rewrite criterion, добавить 3-й example, обновить inline-justification template (AC #1, #2)
- `plugins/presentation/skills/pptx-arch-style/references/rules.yaml` (exists) — опц. lint rule (severity: info) для detection (AC #3)
- `plugins/presentation/skills/pptx-arch-style/scripts/lint.py` (exists) — handler нового правила если AC #3
- `plugins/presentation/skills/pptx-arch-style/scripts/tests/fixtures/` (exists) — fixture pair (mixed-format-as-combined violator vs mixed-format-as-overlay clean) если AC #3 (AC #4)
- `plugins/presentation/.claude-plugin/plugin.json` (exists) — version bump per SemVer (patch для clarification; minor если ship'нут lint rule) (AC #5)

## Source

Source: /Users/paul/Private/Alfa/Projects/standard/stacks@ac76f0f7bd1a
Visual reproduction: stacks repo `presentations/registry/output/doc-6-registry-ak.pptx` slide 7 (wrong: combined form on title+body cards) vs slide 8 (right: overlay on Farzoom/Cinimex cards). Reference source: `presentations/registry/generate-doc-6-registry.js` соответствующие slide-блоки. Связанные tasks: TASK-26 в claude-skills (Done, commit `fe29675`) — внёс слишком узкий критерий; TASK-58 в stacks (Done, commit `ac76f0f`) — surfaced под applied canary.

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
- [x] #1 SKILL.md «Shape+Text Composition» section переписан: combined form is default ТОЛЬКО когда блок содержит single-style text (один font/size/weight/color, без heading+body разделения). Overlay form required в ДВУХ случаях: (i) 2+ labels at distinct positions (как сейчас), ИЛИ (ii) mixed formatting в одном positional cluster (heading+body, big-number+caption, header+footer)
- [x] #2 SKILL.md содержит минимум 3 canonical examples с code-блоками: (i) combined-OK для simple single-style label, (ii) overlay для multi-position (текущий title+footer-tag пример), (iii) НОВЫЙ overlay-пример для mixed-format-в-одном-position (например card с bold title + regular body снизу)
- [x] #3 Inline-justification comment template обновлён: пример комментария указывает который критерий применён ('// Overlay justified: multi-position labels' ИЛИ '// Overlay justified: mixed formatting title+body')
- [ ] #4 Опц.: lint rule (severity: info) в rules.yaml детектирующий combined-form-в-блоке с признаками mixed-format (например text содержит \n И блок широкий И font-size>threshold). Implementer уточняет детекцию, обоснование в task notes
- [ ] #5 Если AC #4 ship'нут: fixture pair (mixed-format-as-combined violator vs mixed-format-as-overlay clean) в scripts/tests/fixtures/
- [x] #6 plugins/presentation/.claude-plugin/plugin.json version bumped per SemVer (patch для clarification; minor если ship'нут lint rule)
- [ ] #7 task-reviewer agent на git diff master..HEAD возвращает APPROVED перед merge
<!-- AC:END -->



## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Decisions locked before Ralph run

- **Ship lint rule (AC#4):** NO. Detection heuristic (text contains \n AND wide block AND font-size>threshold) is too fuzzy and would have high false-positive rate even at info severity. Spec rewrite + 3 canonical examples + updated inline-justification template is sufficient. AC#5 is therefore N/A.
- **SemVer:** patch bump (0.6.1 → 0.6.2 if run after TASK-27/28 minor bumps, the version will be whatever-the-current-minor + 0.0.1). Pure spec clarification, no new public surface.
- **Examples to include in SKILL.md (AC#2):** (i) combined-OK simple label, (ii) overlay multi-position (keep existing title+footer-tag), (iii) NEW overlay-for-mixed-format (card with bold title addText + regular body addText on shared roundRect — Farzoom/Cinimex card pattern from stacks doc-6 slide 8 reference).

Plan: rewrite Shape+Text Composition section to broaden overlay criterion (combined ONLY for single-style text; overlay required for multi-position OR mixed-format-in-one-position). Add 3rd canonical example (Farzoom/Cinimex bold-title + regular-body card). Update inline-justification comment template to name which criterion applies. Skip AC#4/#5 (lint rule) per locked decisions. Bump plugin.json 0.8.0→0.8.1 (patch — spec clarification).
<!-- SECTION:NOTES:END -->
