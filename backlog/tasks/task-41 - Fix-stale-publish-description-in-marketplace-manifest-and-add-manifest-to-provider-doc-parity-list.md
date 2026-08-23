---
id: TASK-41
title: >-
  Fix stale publish description in marketplace manifest and add manifest to
  provider doc-parity list
status: Done
assignee: []
created_date: '2026-08-23 06:44'
updated_date: '2026-08-23 06:56'
labels: []
dependencies: []
ordinal: 41000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The `publish` plugin entry in `.claude-plugin/marketplace.json` still describes v1 behaviour: "Publish a markdown file as a PDF and optionally drop it on a transport provider ... publish layers the icloud transport on top (v1 ships icloud only)." The plugin actually shipped v1.4.0 with three transport providers (icloud, google-drive, onedrive) plus passthrough copy for ready-made artifacts (.pdf/.pptx/.key/.docx). Every other surface is current — plugin.json, the publish SKILL.md frontmatter, references/providers.md, and the README publish section all say v1.4 / three providers. Only the marketplace manifest drifted.

Root cause: the project doc-parity rule "publish plugin - provider doc-parity Files list" in `.claude/brainstorm-rules.md` enumerates seven surfaces and omits the marketplace manifest, so the provider tasks (33, 36, 37) and the passthrough task (40) each updated `plugins/publish/.claude-plugin/plugin.json` but never the marketplace entry. Fixing only the text would let the next provider re-introduce the same drift.

Scope is text-only. No code changes, no version bump: publish stays at 1.4.0 because no behaviour changes.

Files:
- `.claude-plugin/marketplace.json` (exists) - rewrite the publish entry description so it matches the plugin.json 1.4.0 description: three providers named, passthrough mentioned, no "v1 ships icloud only" claim.
- `.claude/brainstorm-rules.md` (exists) - add the marketplace manifest as an additional bullet in the provider doc-parity Files list, so future provider tasks enumerate it.

Out of scope: the architect / presentation / obsidian marketplace entries (their descriptions are accurate); bumping the publish plugin version; any change to provider behaviour or trigger phrases.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The publish entry description in .claude-plugin/marketplace.json names all three providers: grep -c "icloud" and "google-drive" and "onedrive" each return a hit within the publish entry
- [x] #2 The string "v1 ships icloud only" no longer appears anywhere in .claude-plugin/marketplace.json
- [x] #3 The publish entry description mentions passthrough for ready-made artifacts (.pdf/.pptx/.key/.docx)
- [x] #4 marketplace.json still parses as valid JSON: python3 -m json.tool .claude-plugin/marketplace.json exits 0
- [x] #5 The provider doc-parity Files list in .claude/brainstorm-rules.md contains a bullet for .claude-plugin/marketplace.json
- [x] #6 plugins/publish/.claude-plugin/plugin.json version is still 1.4.0 (no bump)
- [x] #7 uv run ruff check . passes and uv run pytest shows no new failures beyond the pre-existing environment failure test_helper_renders_canonical_decision_tree (missing vendored node_modules)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: (1) Replace the publish entry description in .claude-plugin/marketplace.json with the plugin.json 1.4.0 description verbatim — this gives byte-exact parity between the two manifests, names all three providers (icloud/google-drive/onedrive), states passthrough for ready-made artifacts, and drops the stale 'v1 ships icloud only' claim. (2) Add a '.claude-plugin/marketplace.json (publish entry description — provider list + version claim)' bullet to the provider doc-parity Files list in .claude/brainstorm-rules.md, and update the bullet-count references in that rule ('all four' / 'seven-bullet list') so they match the enumerated list. (3) Verify: python3 -m json.tool on the manifest, greps per AC, plugin.json version untouched at 1.4.0, uv run ruff check . and uv run pytest against a pre-change baseline. Text-only, no version bump.

Commit: `ccdfec8` - task-41: sync publish marketplace description with plugin.json 1.4.0 and add the manifest to the provider doc-parity Files list

Implemented (2 commits on task-41): (1) ccdfec8 — the publish entry description in .claude-plugin/marketplace.json now carries the plugins/publish/.claude-plugin/plugin.json 1.4.0 description **byte-identical** (324 chars): three providers named (icloud, google-drive, onedrive), passthrough for ready-made artifacts (.pdf/.pptx/.key/.docx) stated, stale 'v1 ships icloud only' claim gone. Byte-identical parity was chosen over a paraphrase so future drift is a one-line diff to spot. The manifest's original formatting is preserved (single changed line; two-space indent, key order, compact owner line, raw UTF-8 em-dash and arrow, trailing newline all intact). Also added the eighth bullet to the 'publish plugin — provider doc-parity Files list' rule in .claude/brainstorm-rules.md and corrected the two bullet-count references the new bullet invalidated ('all four' → 'all eight', 'seven-bullet list' → 'eight-bullet list'; 'four' was already wrong against the pre-existing seven bullets). (2) 4239eca — corrected the rationale sentence after a blocking-adjacent review finding: the first draft claimed the rule's incomplete list caused TASK-33/36/37 to omit the manifest, but 'git merge-base --is-ancestor f1b98b4 <commit>' proves the rule commit f1b98b4 (2026-06-23) is NOT an ancestor of 2bff035/18f91bb/b56aba3/93ff96b — only of 0256b28 (TASK-40). Rewritten to say the manifest was never in the list and had already been missed before the list existed, so all five post-split bumps (TASK-33, 34, 36, 37, 40) left the entry stale; TASK-34 (previously uncited, 1.1.0→1.2.0) is now included.

Verification: AC#1 icloud/google-drive/onedrive each 1 hit inside the publish entry; AC#2 grep -c 'v1 ships icloud only' → 0; AC#3 'passthrough' + '.pdf/.pptx/.key/.docx' present; AC#4 python3 -m json.tool exit 0; AC#5 bullet at .claude/brainstorm-rules.md:130; AC#6 plugin.json still 1.4.0 and 'git diff master..HEAD --name-only -- plugins/**' is EMPTY, so no version bump is owed under the plugin-layout rule; AC#7 'uv run ruff check .' → All checks passed, 'uv run pytest' → 1 failed / 106 passed, identical to the pre-change baseline taken on this branch, the sole failure being the pre-existing environment failure test_helper_renders_canonical_decision_tree (tests/node_modules genuinely absent on disk; diff touches zero .py files).

Environment gotcha: the python3 on PATH is a broken 3.14 build that dies with a GLIBC_2.38 error; AC#4's literal command needs a 'PATH=/usr/bin:$PATH' prefix to reach the working 3.11.2.

Review: the lifecycle-mandated 'task-reviewer' agent is UNREGISTERED in this checkout (no .claude/agents/ directory and no .claude/task-reviewer-rules.md), so per the documented fallback an independent reviewer agent was spawned carrying the same charter. Verdict APPROVED on the initial pass with one LOW finding (the causality error above), then re-run on the two-commit HEAD after the fix: final verdict APPROVED, finding resolved, ancestry independently reproduced, no regressions.

Follow-up worth a task (out of scope here, raised by the reviewer as INFO): nothing mechanically enforces the new 'byte-identical' instruction — a small parity assertion comparing the marketplace publish description to plugin.json's, in the style of TASK-40's doc-assertion test, would prevent the next provider from re-drifting.
<!-- SECTION:NOTES:END -->
