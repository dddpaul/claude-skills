# Feature Review: publish-plugin-split (incremental delta: TASK-36 onedrive)

**Verdict: Partial**

**Passes run:** 3, 5 (brainstorm-only feature; no PRD)
**Passes skipped:** 1 (no PRD — no formal User Stories / Functional Requirements list), 2 (no PRD Non-Goals section; brainstorm Scope Cuts evaluated under Pass 3 instead), 4 (no PRD Success Metrics section)

This run anchors on TASK-36 (onedrive provider, v1.3.0) as the incremental delta on top of the prior cumulative review (`design/publish-plugin-split-review-2026-06-21.md`, verdict Aligned, covering TASK-32/33/34). Prior intents are cross-checked but not re-enumerated in full.

---

## Intent → Implementation Matrix

The original brainstorm explicitly listed OneDrive as a deferred scope cut: "No OneDrive in v1 — explicitly deferred; same shape as `google-drive` when added later." TASK-36 lifts that deferral; its own description / Provider definition becomes the de-facto contract for this delta. The brainstorm-level intents that the delta touches:

| ID | Intent (source) | Status | Evidence |
|----|-----------------|--------|----------|
| BR-OD1 | OneDrive added with the same shape as `google-drive` (glob-rooted Provider, multi-account hard-fail) | Delivered | `plugins/publish/skills/publish/scripts/providers.py:79-91` — `ONEDRIVE = Provider(name="onedrive", env_var="PUBLISH_ONEDRIVE_DIR", default_root_glob="~/Library/CloudStorage/OneDrive-*", triggers=(6 phrases))`; registered in `PROVIDERS` dict; reuses the same `_resolve_from_glob` 0/1/>1 logic |
| BR-OD2 | Plugin SemVer minor bump for additive provider | Delivered | `plugins/publish/.claude-plugin/plugin.json` → `"version": "1.3.0"` (1.2.0 → 1.3.0); description updated to "v1.3 ships icloud, google-drive, and onedrive" |
| BR-OD3 | Trigger phrase routing for all new EN+RU phrases | Delivered | `plugins/publish/skills/publish/tests/test_providers.py:150-160` — `test_each_onedrive_trigger_resolves_to_onedrive` + case-insensitive variant, parameterized over all six `ONEDRIVE_TRIGGERS` |
| BR-OD4 | Env-var override beats glob default | Delivered | `test_publish_onedrive_dir_overrides_default_root`, `test_publish_onedrive_dir_strips_trailing_slash`, `test_onedrive_env_override_skips_glob_entirely` |
| BR-OD5 | Glob 0 / 1 / >1 behavior parallels google-drive | Delivered | `test_onedrive_glob_exactly_one_match_resolves`, `test_onedrive_glob_zero_matches_hard_fails`, `test_onedrive_glob_multi_account_hard_fails` — error message names `PUBLISH_ONEDRIVE_DIR` in both failure modes |
| BR-OD6 | SKILL.md surface reflects the new provider (frontmatter triggers, body trigger list, version mention, push-procedure step 5 branch) | Delivered | `plugins/publish/skills/publish/SKILL.md` frontmatter lists all 11 EN + 10 RU phrases (8 icloud + 7 gdrive + 6 onedrive = 21 total); body has `onedrive triggers:` section; step 5 of push procedure adds an `onedrive` branch with the glob and hard-fail wording; "Out of scope (v1.3)" line for onedrive multi-account explicitly added; "No OneDrive" cut removed |
| BR-OD7 | `references/providers.md` reflects the new provider | **Missing** | File still shows only 2 rows (icloud + google-drive); "v1-scope trigger mapping" still labelled with old phrase counts and lists only the two original providers. No `onedrive` row, no `PUBLISH_ONEDRIVE_DIR` entry |
| BR-OD8 | `references/onedrive.md` per-provider deep-dive (the brainstorm's pattern: each provider gets its own `references/<provider>.md` — see `icloud.md`, `google-drive.md`) | **Missing** | No `references/onedrive.md` exists. Pattern symmetry broken: the `[[onedrive]]` wikilink target referenced in SKILL.md "Providers" paragraph (line "[[icloud]], [[google-drive]]") was simply omitted rather than authored |
| BR-OD9 | Root README "### publish" section mentions onedrive | **Missing** | `README.md:114` still reads "v1.1 ships two providers: `icloud` … and `google-drive` …"; example trigger block still omits all 6 onedrive phrases. No `PUBLISH_ONEDRIVE_DIR` mention anywhere in README |

Prior-delta cross-check (BR-1 through BR-15 from the prior review): all still hold. The Provider-XOR invariant (`default_root` xor `default_root_glob`) accommodates `ONEDRIVE` cleanly; existing icloud/google-drive tests are not regressed; the SKILL.md push procedure preserves the brainstorm-prescribed 8-step ordering and now branches on three providers in step 5 instead of two.

---

## Non-Goal Violations

Pass 2 skipped (no PRD with explicit Non-Goals section).

---

## Scope Cut Violations

Re-checking the brainstorm's eleven scope cuts against the v1.3 delta:

| Scope cut | Status |
|-----------|--------|
| No EPUB output | Respected |
| No rclone / headless upload | Respected — onedrive is also mount-only via `~/Library/CloudStorage/OneDrive-*`; no rclone path introduced |
| No PDF / non-`.md` input | Respected |
| No syntax highlighting | Respected |
| No multi-file batching | Respected |
| No cleanup of old PDFs | Respected |
| No annotation pull-back | Respected — onedrive doc surface inherits push-only stance |
| No GDrive multi-account auto-pick | Respected; onedrive mirrors it correctly (hard-fail with env-var hint) |
| No `READING_ICLOUD_DIR` deprecation grace | Respected |
| **No OneDrive in v1** | **Intentionally lifted** by TASK-36 (which itself bumps the plugin to v1.3.0) — not a violation; this is the scope-cut being deliberately retired per a new task, not silently shipped. The brainstorm itself anticipated this ("same shape as `google-drive` when added later") |
| No skill-to-skill invocation via Skill tool | Respected — `publish/SKILL.md` step 7 still shells out to the `pdf` script directly |

**None detected.** The OneDrive deferral was lifted through a formal task with its own Why/Scope block, which is the legitimate path for retiring a brainstorm-era cut.

---

## Drift List (publish-plugin-split surface only)

Pass 5 — scan publish-surface hunks against either the brainstorm, TASK-36's locked Provider definition, or a prior-task AC.

1. **`plugins/publish/skills/publish/references/providers.md` — stale.** The "single source of truth for the provider table" (brainstorm's words) ships v1.3 still describing v1.1: only two rows, no onedrive entry, no `PUBLISH_ONEDRIVE_DIR`. The trigger-mapping section is similarly two-provider. This contradicts the brainstorm's own framing — the brainstorm explicitly designates `references/providers.md` as the canonical table that other docs cite. Code (`providers.py` `PROVIDERS` dict) now exceeds the table.

2. **`plugins/publish/skills/publish/references/onedrive.md` — absent.** Brainstorm-established pattern: each provider gets a `references/<provider>.md` deep-dive (`icloud.md`, `google-drive.md` exist; `onedrive.md` missing). SKILL.md "Providers" paragraph reads "transport notes live in dedicated reference files (`[[icloud]]`, `[[google-drive]]`)" — the `[[onedrive]]` wikilink is conspicuously absent rather than dangling, which suggests the omission was conscious and deliberately not patched.

3. **Root `README.md` ### publish section — stale.** Still says "v1.1 ships two providers"; example trigger fence omits all six onedrive phrases; no `PUBLISH_ONEDRIVE_DIR` mention. TASK-36's "Files" list did not include `README.md`, but the prior TASK-32 AC explicitly required README to mirror the publish surface — leaving onedrive out introduces user-facing documentation drift.

TASK-36's implementation notes acknowledge items 1 and 2 explicitly: *"Follow-up recommended (out of scope here): update references/providers.md and add references/onedrive.md for full doc parity."* That is honest scope-management, but for a feature-level cumulative review the doc-parity gap still has to be flagged as drift between code and design intent — the brainstorm makes `providers.md` authoritative.

No other drift on the publish-plugin-split surface. The code itself is clean, tests mirror the google-drive structure exactly, SKILL.md is fully updated, plugin.json bumped per SemVer, marketplace.json untouched (correct — no plugin-level surface change beyond version).

---

## Reviewer Notes

1. **Out-of-scope changes flagged once and not re-listed as drift, per the prompt:** the diff range also contains TASK-35 (Ralph infrastructure upgrade — `.claude/hooks/*-guard.sh`, `.claude/brainstorm-rules.md`, `.devcontainer/devcontainer.json`, `ralph.sh`) and the prior `design/publish-plugin-split-review-2026-06-21.md` doc. These are not publish-plugin-split concerns and are not evaluated. Of note: TASK-35 also reset the devcontainer port label from "Claude Skills app" back to "Some application" — TASK-35's notes flag this as an accepted regression to re-personalize later. Mentioning here once for orientation only.

2. **Test-suite growth is healthy.** Prior cumulative review counted ~46 tests (post-TASK-33). TASK-34 brought it to 79 (regression test for Defect 1). TASK-36 adds 18 more, taking it to 97. The onedrive test set is a near-perfect mirror of the google-drive set (parametrized triggers, case-insensitive variant, env override, trailing-slash strip, glob 0/1/>1) — pattern reuse is exactly what the brainstorm's "same shape as google-drive when added later" anticipated.

3. **Provider abstraction held under extension.** The `Provider` class's XOR invariant (`(default_root is None) == (default_root_glob is None)`) accepted the third provider without modification. `resolve_root` and `_resolve_from_glob` did not need to change. This is a positive signal that the shape established in TASK-32/33 was the right factoring.

4. **TASK-34's "drop trailing /Reading from defaults" decision propagated correctly.** Both the icloud literal default and the google-drive glob default are bare-mount-root paths now; onedrive followed the same convention (`~/Library/CloudStorage/OneDrive-*` is the mount root, not the Reading subfolder). The shared push procedure's `<root>/Reading/<project>/<slug>.pdf` layout therefore yields a single `Reading/` segment for all three providers — symmetry preserved.

5. **SemVer rationale for 1.2.0 → 1.3.0 is correct.** Additive provider, no breaking change for existing icloud/google-drive users. Minor bump per the repo's stated SemVer policy.

6. **Recommended follow-up (single concise task, not a blocker):** create a small TASK to (a) add the `onedrive` row to `providers.md` and refresh the trigger-mapping section, (b) add `references/onedrive.md` mirroring `google-drive.md` (mount-only, multi-account hard-fail, default-root section, push-only, slug collision, macOS prerequisites — Personal vs. Work/School naming is the one onedrive-specific note worth capturing), and (c) bump the README "### publish" section to "v1.3 ships three providers …" with `PUBLISH_ONEDRIVE_DIR` and at least three example onedrive triggers. SemVer for that follow-up is a patch (doc-only). This would move the verdict from Partial to Aligned.

**Verdict rationale:** code, tests, SKILL.md, and `plugin.json` for onedrive are all in place and consistent with the brainstorm's "same shape as google-drive when added later" framing; but the brainstorm explicitly designates `references/providers.md` as the canonical provider table and the per-provider `references/<provider>.md` deep-dive as the documented pattern, neither of which was updated for onedrive — plus the root README still markets the plugin as v1.1 with two providers. The gap is squarely in user-facing docs, not in behavior, so Partial rather than Drifted; not Aligned because the brainstorm-anchored doc surface is materially incomplete for the new provider.

Relevant absolute paths:
- /Users/paul/Private/Projects/ai/claude-skills/plugins/publish/skills/publish/scripts/providers.py
- /Users/paul/Private/Projects/ai/claude-skills/plugins/publish/skills/publish/tests/test_providers.py
- /Users/paul/Private/Projects/ai/claude-skills/plugins/publish/skills/publish/SKILL.md
- /Users/paul/Private/Projects/ai/claude-skills/plugins/publish/skills/publish/references/providers.md (stale — v1.1 surface)
- /Users/paul/Private/Projects/ai/claude-skills/plugins/publish/skills/publish/references/icloud.md
- /Users/paul/Private/Projects/ai/claude-skills/plugins/publish/skills/publish/references/google-drive.md
- /Users/paul/Private/Projects/ai/claude-skills/plugins/publish/skills/publish/references/onedrive.md (missing)
- /Users/paul/Private/Projects/ai/claude-skills/plugins/publish/.claude-plugin/plugin.json
- /Users/paul/Private/Projects/ai/claude-skills/README.md (### publish section stale — line 114)
- /Users/paul/Private/Projects/ai/claude-skills/design/publish-plugin-split-brainstorm.md
- /Users/paul/Private/Projects/ai/claude-skills/design/publish-plugin-split-review-2026-06-21.md (prior cumulative review carry-forward)
