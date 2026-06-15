---
id: TASK-19
title: Match PDF heading anchors to Obsidian-style exact-text link fragments
status: Done
assignee: []
created_date: '2026-06-15 13:21'
updated_date: '2026-06-15 15:04'
labels: []
dependencies: []
priority: medium
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Why

A user of the reading:books skill (currently v0.2.8) authors docs whose primary review environment is Obsidian via the offdesk skill. Obsidian's heading-link semantics require the URL fragment to be the exact heading text (case-insensitive), not a GitHub-style kebab slug. The user just migrated a real-world doc (`doc-6` in their stacks project) from kebab anchors like `#32-camunda--соседняя-ис-вне-периметра-пф` to Obsidian-compatible anchors like `#3.2 Camunda — соседняя ИС вне периметра ПФ`. Side-effect: PDF anchor navigation via reading:books broke — Python-markdown's default `toc` slugify produces ASCII-stripping kebab IDs that no longer match these fragments. Goal: make heading IDs and link-fragment URLs converge on the same Obsidian-style canonical form so docs that navigate in Obsidian also navigate in the rendered PDF.

## Scope

In scope:
- Add a custom slugify to the `toc` extension that produces HTML IDs from heading text using the SAME canonical form that link fragments use (Obsidian convention: case-insensitive, preserve Cyrillic / dots / em-dashes / slashes; collapse whitespace runs to a single hyphen so the result is valid in HTML5 id).
- Preprocess raw markdown link fragments with the same slugify so `<a href="#X">` and `<h3 id="X">` end up character-equal.
- Document the new anchor convention in SKILL.md (PDF layout section or a new 'Anchors' subsection).
- Bump plugin version 0.2.8 → 0.2.9 (patch — internal behavior change, no user-facing API change).
- Add a small test fixture + pytest verifying that for a markdown doc with Cyrillic / em-dash / dot / slash bearing headings, every `#fragment` in the rendered HTML resolves to an existing `id` in the same document.

Out of scope:
- Changing `references/styles.css` (no visual change required by this task).
- Changing the rendering engine (stay on weasyprint).
- Adding a configuration knob for the user to pick between slugify schemes — this is a single-convention change.
- Supporting arbitrary link types other than in-document heading anchors (external URLs, wikilinks, image refs are untouched).

## Implementation hint (NOT prescriptive)

Approach A (recommended): custom slugify + raw-markdown link-fragment preprocess.

```python
def obsidian_slugify(value: str, sep: str = '-') -> str:
    # case-insensitive; preserve Cyrillic, dots, em-dashes, slashes;
    # collapse whitespace runs to sep so HTML5 id is valid
    return re.sub(r'\s+', sep, value.strip().lower())

# 1. Configure toc with this slugify:
md = markdown.Markdown(
    extensions=['fenced_code', 'tables', 'toc'],
    extension_configs={'toc': {'toc_depth': '1-3', 'slugify': obsidian_slugify}},
)

# 2. Preprocess raw markdown link fragments BEFORE conversion so href matches id:
def _normalize_fragment(m):
    return f'{m.group(1)}(#{obsidian_slugify(m.group(2))})'

raw = re.sub(r'(\[[^\]]+\])\(#([^)]+)\)', _normalize_fragment, raw)
```

Approach B (rejected): require authors to add explicit `{#id}` to every heading via `attr_list` — defeats the 'Obsidian-style just works' goal.

## Test corpus

The canonical real-world test markdown is `/Users/paul/Private/Alfa/Projects/standard/stacks/backlog/docs/doc-6 - Camunda-8-in-Russian-software-registry.md` (read-only, do NOT modify). It contains 8 unique heading anchors covering Cyrillic, em-dash, dot-bearing slug (`#4. Plan B: если Путь 1 не получится`), slash-bearing slug (`#4.2 Сводка путей 2/3/4`), and ASCII-mixed (`#3.2 Camunda — соседняя ИС вне периметра ПФ`). After the change, rendering this doc should produce a PDF where every `§N.M` cross-ref navigates to the correct page in Apple Books / Acrobat. Automated test should use a small fixture markdown that covers these character classes — does not need to include the full doc.

## Files

- `plugins/reading/skills/books/scripts/md-to-pdf.py` (exists) — add `obsidian_slugify` + the link-fragment preprocess + wire slugify into `toc` extension config.
- `plugins/reading/skills/books/SKILL.md` (exists) — document the Obsidian-style heading anchor convention.
- `plugins/reading/.claude-plugin/plugin.json` (exists) — bump version 0.2.8 → 0.2.9.
- `plugins/reading/skills/books/tests/test_anchors.py` (to-create) — pytest verifying href↔id convergence on a fixture md doc.
- `plugins/reading/skills/books/tests/fixtures/anchors.md` (to-create) — fixture markdown with Cyrillic / em-dash / dot / slash anchors.

## Source

Source: /Users/paul/Private/Alfa/Projects/standard/stacks@c34015bae375
Source change that triggered this task: TASK-40 in stacks ('Convert doc-6 cross-refs to Obsidian-compatible heading-text anchors'), commit c34015b.

## Before starting (destination Claude validation checklist)

Before running this task, verify:
1. All `(exists)` file paths in the Files section still exist in this repo.
2. Each AC is objectively pass/fail (a grep, test invocation, build command, or visible behavior — not 'works correctly').
3. All dependencies in the task's frontmatter are status=Done.
4. Out-of-scope items are not accidentally pulled in by ambiguous AC.

If anything is unclear or any check fails: STOP and ask the user. Do NOT start work blindly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 md-to-pdf.py defines an obsidian_slugify function (case-insensitive, preserves Cyrillic/dots/em-dashes/slashes, collapses whitespace runs to a single hyphen) and wires it into the toc extension's slugify config
- [x] #2 md-to-pdf.py preprocesses raw markdown link fragments with the same obsidian_slugify before conversion, so every '[text](#X)' has its X normalized identically to the matching heading id
- [x] #3 Rendering the fixture markdown produces an HTML where every internal '#fragment' value is also present as an 'id=fragment' attribute on some heading (verified by the new test)
- [x] #4 New pytest at plugins/reading/skills/books/tests/test_anchors.py covers: Cyrillic-only heading, em-dash heading, dot-bearing heading, slash-bearing heading, ASCII heading — all anchor href values resolve to existing ids
- [x] #5 SKILL.md documents the Obsidian-style heading anchor convention (where heading id and link fragment both pass through the same canonical form)
- [x] #6 .claude-plugin/plugin.json version bumped from 0.2.8 to 0.2.9
- [x] #7 uv run ruff check . and uv run pytest both pass from repo root
- [ ] #8 Manual verification recorded in task notes: re-render /Users/paul/Private/Alfa/Projects/standard/stacks/backlog/docs/doc-6 - Camunda-8-in-Russian-software-registry.md via the new skill version and click §3.2 / §4.2 / §4.4 cross-refs in the PDF, observe correct in-document navigation
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**Update (after source TASK-41 in stacks landed):** doc-6 now uses CommonMark angle-bracket form for anchors with whitespace:

```markdown
[§3.2](<#3.2 Camunda — соседняя ИС вне периметра ПФ>)
```

Implementation hint update — the raw-markdown link-fragment preprocess regex should match both forms (bare `(#frag)` and angle-bracketed `(<#frag>)`):

```python
def _normalize_fragment(m):
    return f'{m.group(1)}(<#{obsidian_slugify(m.group(2))}>)'

raw = re.sub(r'(\[[^\]]+\])\(<?#([^>)]+)>?\)', _normalize_fragment, raw)
```

After preprocessing, both forms normalize to angle-bracket — Python-markdown then strips the brackets during HTML conversion, producing `<a href="#normalized-fragment">`. The toc extension's slugify must produce the SAME normalized fragment for heading IDs so href↔id match.

Source ref updated: /Users/paul/Private/Alfa/Projects/standard/stacks@5ae1ae6 (TASK-41 merged on top of TASK-40).

Plan: (1) add obsidian_slugify(value, sep='-') in md-to-pdf.py that lowercases, strips, collapses whitespace runs to sep, preserves Cyrillic/dots/em-dashes/slashes. (2) Wire into toc extension config. (3) Add raw-md regex preprocess matching both bare and angle-bracket fragment forms: r'(\[[^\]]+\])\(<?#([^>)]+)>?\)' -> normalize the fragment via the same function. (4) Create tests/fixtures/anchors.md covering Cyrillic-only, em-dash, dot, slash, ASCII headings. (5) Create tests/test_anchors.py using bs4-free regex extraction (or stdlib html.parser) that runs the script end-to-end on the fixture, asserts every href #frag has a matching id. (6) Add pytest to dev deps via uv add --dev. (7) Document the Obsidian anchor convention in SKILL.md under a new ## Anchors section. (8) Bump plugin.json 0.2.8 -> 0.2.9.

AC #8 (manual verification of doc-6 cross-refs in Apple Books / Acrobat) is deferred to the user — the source doc-6 lives on the user's laptop at /Users/paul/Private/Alfa/Projects/standard/stacks/backlog/docs/ and is not reachable from this container. Automated equivalent: tests/test_anchors.py exercises Cyrillic / em-dash / dot / slash / ASCII heading classes against the production md_to_html pipeline; all 4 pass. End-to-end PDF render of the fixture also succeeded.

Commit: `2922a6f` - task-19: converge heading IDs and link fragments on a single Obsidian-style canonical form. md-to-pdf.py + obsidian_slugify (case-folded, whitespace runs -> single '-', preserves Cyrillic/dots/em-dashes/slashes) wired into toc extension's slugify config; _normalize_fragments rewrites raw markdown link fragments through the same function before conversion, matching both bare and angle-bracket forms (CommonMark whitespace-in-fragment spelling). md_to_html extracted as the testable entry point. SKILL.md gains an Anchors section. tests/ adds an anchors.md fixture covering Cyrillic / em-dash / dot / slash / ASCII heading classes and test_anchors.py asserting every internal href fragment resolves to a heading id. pytest added as a dev dep. plugin 0.2.8 -> 0.2.9.

Implementation: obsidian_slugify(value, sep='-') lowercases + collapses whitespace runs to sep (preserves Cyrillic/dots/em-dashes/slashes via regex-passthrough). Wired into toc extension's slugify config. _normalize_fragments rewrites raw markdown link fragments through the same function before md.convert(), matching both bare '(#X)' and angle-bracket '(<#X>)' CommonMark spellings (output is always angle-bracket; python-markdown then strips brackets, yielding href=fragment that character-matches the heading id). main() refactored to delegate the strip+normalize+convert sequence to md_to_html, which the new test imports. Test fixture covers ASCII / Cyrillic-only / em-dash / dot / slash heading classes; 4 pytest cases (4/4 pass). uv run ruff check . and uv run pytest both green. plugin 0.2.8 -> 0.2.9. task-reviewer agent: APPROVED.
<!-- SECTION:NOTES:END -->
