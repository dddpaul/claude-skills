# Feature Review: publish-plugin-split

**Verdict: Aligned**

**Passes run:** 3, 5 (PRD-conditional passes 1, 2, 4 skipped — no PRD exists for this feature; only the brainstorm)
**Passes skipped:** 1 (no PRD), 2 (no PRD / no Non-Goals section), 4 (no PRD / no Success Metrics section)

The feature has a brainstorm but no PRD. Per the rubric, PRD-conditional passes (coverage, non-goal protection, success-metric realism) are skipped. The brainstorm's "Scope cuts" section anchors Pass 3, and Pass 5 cross-checks every changed hunk against either the brainstorm or one of the two task ACs.

---

## Intent → Implementation Matrix

The brainstorm enumerates ten design intents (rename, two sibling skills, providers-by-transport, env-var rename, two providers v1, push-flow shape, scope cuts, no-provider-matched UX, slug + atomic write, tests). Each is traced to its implementation below.

| ID | Brainstorm intent | Status | Evidence |
|----|-------------------|--------|----------|
| BR-1 | Plugin rename `reading` → `publish` as hard major bump v1.0.0 | Delivered | `.claude-plugin/marketplace.json` entry renamed (lines 9–14 of diff); `plugins/reading/.claude-plugin/plugin.json` deleted; `plugins/publish/.claude-plugin/plugin.json` new file with `"name": "publish"` and `"version": "1.1.0"` (1.0.0 at T1, bumped to 1.1.0 by T2) |
| BR-2 | `pdf` skill — standalone MD → PDF conversion, callable directly | Delivered | `plugins/publish/skills/pdf/SKILL.md` declares "Conversion-only — no upload, no transport"; bilingual triggers EN+RU in frontmatter description |
| BR-3 | `publish` skill — umbrella, shells out to `pdf` script (no skill-to-skill plumbing) | Delivered | `plugins/publish/skills/publish/SKILL.md` step 7 invokes `uv run plugins/publish/skills/pdf/scripts/md-to-pdf.py …` directly; no Skill-tool invocation present |
| BR-4 | `md-to-pdf.py` and `styles.css` preserved via `git mv` | Delivered | Diff headers show `similarity index 100%` for `styles.css` and `similarity index 88%` for `md-to-pdf.py` (the 12% delta is the documented optional-target-arg + .md hard-fail addition); both rename-detected, history preserved |
| BR-5 | Providers named by transport, not consumer device | Delivered | `providers.md` table uses `icloud` and `google-drive`; `icloud.md` contains the explicit "Apple Books on iPad is one consumer" sidebar; `google-drive.md` opens with "Google Drive is treated as a transport, not as a consumer device" |
| BR-6 | Env var `READING_ICLOUD_DIR` → `PUBLISH_ICLOUD_DIR` with NO fallback | Delivered | `scripts/providers.py` reads only `provider.env_var` (i.e. `PUBLISH_ICLOUD_DIR` or `PUBLISH_GOOGLE_DRIVE_DIR`); explicit `test_legacy_env_var_is_ignored` test in `test_providers.py`; `grep -rn READING_ICLOUD_DIR plugins/` returns 0 matches (confirmed against current tree); legacy var name in tests is assembled from string parts (`"READING_" + "ICLOUD_DIR"`) so the grep stays clean |
| BR-7 | Two providers v1: `icloud` (literal default) and `google-drive` (glob default) | Delivered | `ICLOUD` provider uses literal `default_root`; `GOOGLE_DRIVE` uses `default_root_glob`; `Provider.__init__` enforces exactly-one-of via assertion; `providers.md` table lists both with correct env vars and roots |
| BR-8 | Push flow: 8 steps in the order brainstorm specifies, with `git rev-parse --show-toplevel` + `dirname(source)` fallback | Delivered | `plugins/publish/skills/publish/SKILL.md` "Push procedure" enumerates steps 1–8 in the exact order: (1) identify provider, (2) resolve source + .md hard-fail, (3) compute slug + sha1[:6] collision rule, (4) `git rev-parse --show-toplevel` with `dirname(source)` fallback, (5) resolve provider root with icloud-literal vs google-drive-glob branching, (6) `mkdir -p`, (7) shell out to pdf script, (8) report path |
| BR-9 | No-provider-matched UX → ask user, return `NEEDS_DISAMBIGUATION` sentinel | Delivered | `scripts/providers.py:107` returns `NEEDS_DISAMBIGUATION` when no trigger matches; `SKILL.md` body: "If the user says something generic like 'publish this' or 'отправь это' with no provider implied, ask which provider before proceeding. Do not silently default to any provider."; `test_unmatched_phrase_returns_disambiguation_sentinel` covers 5 generic phrases including empty string |
| BR-10 | GDrive glob 0/1/>1 behavior, no auto-pick | Delivered | `_resolve_from_glob` in `providers.py` sorts matches, returns single match if `len == 1`, raises `ProviderResolutionError` naming `PUBLISH_GOOGLE_DRIVE_DIR` for 0 and >1; `test_google_drive_glob_zero_matches_hard_fails`, `test_google_drive_glob_multi_account_hard_fails`, `test_google_drive_glob_exactly_one_match_resolves`, `test_google_drive_env_override_skips_glob_entirely` all green |
| BR-11 | Subfolder layout symmetric: `<root>/Reading/<project>/<slug>.pdf` on both providers | Delivered | `SKILL.md` step 6 prescribes the symmetric layout; `providers.md` "Resolution order" step 5 reiterates it; `google-drive.md` "Slug collision" section explicitly says "Resolution is identical to the icloud provider" |
| BR-12 | Atomic write via `.tmp` + `os.replace` | Delivered | `md-to-pdf.py` carries over the pre-existing atomic-write logic (the unchanged-portion of the file at 88% similarity); `pdf/SKILL.md` documents "Write is atomic: the script renders to a hidden `.<target>.tmp` next to the final path, then `os.replace`s it into place" |
| BR-13 | Slug = `Path(source).stem`, sha1[:6] suffix on collision | Procedural (documented, not coded) | Documented in `publish/SKILL.md` step 3 and `icloud.md` / `google-drive.md` "Slug collision" sections. **No Python helper implements the collision check** — the rule is a procedural instruction for the agent at push time, not coded logic. This matches the pre-rename `books` skill, which also documented but did not implement the rule. Carryover, not a regression. |
| BR-14 | Tests: per-trigger routing, env-var precedence, GDrive glob (0/1/>1), no-provider-matched | Delivered | `test_providers.py` parameterizes all 8 icloud triggers and all 7 google-drive triggers (15 phrases); covers case-insensitivity + whitespace tolerance; env-var override + trailing-slash strip for both providers; legacy var ignored + override wins over legacy; all 4 GDrive glob scenarios |
| BR-15 | Trigger phrase counts: icloud 8, google-drive 7 | Delivered | `SKILL.md` frontmatter lists 8 icloud + 7 google-drive (15 total) phrases; `providers.md` "v1-scope trigger mapping" agrees; `providers.py` `ICLOUD.triggers` tuple has 8 entries, `GOOGLE_DRIVE.triggers` has 7; `test_providers.py` `ICLOUD_TRIGGERS` and `GOOGLE_DRIVE_TRIGGERS` constants match |

All 15 brainstorm intents are Delivered, except BR-13 which is Procedural-by-Design (documented rather than coded — the brainstorm itself describes slug collision as a procedural step in the push flow, not a coded function).

---

## Non-Goal Violations

Pass 2 skipped (no PRD with explicit Non-Goals section). Brainstorm "Scope cuts" are evaluated under Pass 3 below.

---

## Scope Cut Violations

Brainstorm "Scope cuts" enumerates eight cuts. Verified each against the diff:

| Scope cut | Status |
|-----------|--------|
| No EPUB output | Respected — no EPUB code or doc anywhere |
| No rclone / headless upload | Respected — `google-drive.md` "Mount-only — no rclone in v1" section explicitly documents the cut |
| No PDF / non-`.md` input | Respected — `md-to-pdf.py` adds explicit `sys.exit(f"source must be a .md file: {src}")` hard-fail; `SKILL.md` reiterates "Hard-fail if the extension is not `.md`" |
| No syntax highlighting | Respected — `pdf/SKILL.md` "Code: …, light-grey background. No syntax highlighting." |
| No multi-file batching | Respected — interface is single-file; documented as out-of-scope in `publish/SKILL.md` |
| No cleanup | Respected — documented as out-of-scope in `publish/SKILL.md` |
| No annotation pull-back | Respected — both `icloud.md` and `google-drive.md` have "Push-only — annotations stay" sections; `publish/SKILL.md` reiterates |
| No GDrive multi-account auto-pick | Respected — `_resolve_from_glob` raises on `len(matches) > 1`; `test_google_drive_glob_multi_account_hard_fails` proves no silent first-pick |
| No `READING_ICLOUD_DIR` deprecation grace | Respected — clean break; `test_legacy_env_var_is_ignored` proves it |
| No OneDrive in v1 | Respected — no OneDrive entries; `publish/SKILL.md` "Out of scope (v1.1)" line explicitly defers |
| No skill-to-skill invocation via Skill tool | Respected — `publish/SKILL.md` step 7 uses direct `uv run …` shell-out to the pdf script path |

**None detected.**

---

## Drift List

Pass 5 — scan for hunks not traceable to any brainstorm intent or task AC.

Candidate flagged in the prompt: **`plugins/publish/skills/publish/scripts/providers.py`** — was a Python resolver part of the design?

Verdict: **not drift.** The brainstorm's `plugins/publish/skills/publish/tests/` bullet lists test cases that materially require a resolver to exist:
- "provider resolution from trigger phrase"
- "env-var precedence"
- "GDrive glob (0 / 1 / >1 matches)"
- "no-provider-matched flow"

These tests cannot be written without a callable Python surface; the only options are (a) put the resolver inline in the test file or (b) factor it into a `scripts/providers.py` module. Option (b) is the conventional choice and matches the layout the task-32 implementation notes describe ("Add provider resolver Python module to support tests"). The resolver's behavior is also exactly what `publish/SKILL.md` prescribes the agent to do at push time — it is not inventing new API surface, just making the documented procedure executable for testing.

The resolver does add one small API surface element the brainstorm doesn't explicitly name: the `ProviderResolutionError` exception class (introduced in TASK-33). The brainstorm says "hard-fail" without specifying the exception type. This is a reasonable choice (custom exception > generic `RuntimeError` for testable error-message assertions) and the implementation notes mention it transparently. Not material drift.

One more minor observation that does NOT rise to drift: `md-to-pdf.py` gained the optional second arg (defaulting to `<source-dir>/<source-stem>.pdf`) and the explicit `.md` hard-fail. The brainstorm `pdf` bullet explicitly says "Output path defaults to `<source-dir>/<source-stem>.pdf` when target omitted" — so the new behavior is in-scope.

**No drift detected.**

---

## Cross-Task Consistency (T1 → T2)

The prompt highlights this concern. Verified:

1. T2 extended T1's `Provider` class signature with a `default_root_glob` parameter and made it XOR with `default_root`. T1's `ICLOUD` provider still works untouched — the XOR check is `(default_root is None) == (default_root_glob is None)`, which passes when icloud sets `default_root` only and google-drive sets `default_root_glob` only.
2. T2 did not invalidate any T1 AC. T1's eight icloud triggers still resolve to `icloud` in `test_each_icloud_trigger_resolves_to_icloud`; T1's env-var precedence test (`test_publish_icloud_dir_overrides_default_root`) still passes; T1's no-provider-matched flow now also covers the google-drive case (the sentinel test asserts `NEEDS_DISAMBIGUATION != "icloud"` AND `!= "google-drive"`).
3. T2's plugin.json bump is a minor 1.0.0 → 1.1.0, consistent with adding a provider (not a breaking change). README description updated to "v1.1 ships icloud and google-drive."
4. T2's `publish/SKILL.md` revision merged the icloud + google-drive triggers into a single frontmatter description with all 15 phrases, and the body documents each provider's resolution branch (icloud → literal default; google-drive → glob with 0/1/>1 rules). Clean extension, not a rewrite.

---

## Reviewer Notes

1. **Documentation/code symmetry is strong.** The brainstorm's 8-step push procedure appears verbatim in `publish/SKILL.md` step ordering, the providers table appears verbatim in `providers.md`, and the trigger lists in `SKILL.md` frontmatter, `providers.md` mapping section, `providers.py` tuples, and `test_providers.py` constants are all consistent (8 icloud + 7 google-drive = 15 total in every location).

2. **Test depth is appropriate.** 20+ tests cover trigger routing (parameterized over all 15 phrases), case-insensitivity, whitespace tolerance, env-var precedence (with trailing-slash normalization), legacy-var-ignored, override-wins-over-legacy, all four GDrive glob scenarios (0/1/>1/env-override), and the disambiguation sentinel.

3. **Legacy-var test technique is nice.** Assembling `"READING_" + "ICLOUD_DIR"` at runtime so a literal `grep -r READING_ICLOUD_DIR plugins/` returns zero matches is a clean way to satisfy both the "test it stays ignored" need and the AC #6 cleanliness check simultaneously. Worth carrying forward as a pattern.

4. **Procedural-rule honesty.** Several brainstorm steps (slug collision sha1 suffix; `git rev-parse` project-root resolution; `mkdir -p`; shell-out invocation) are documented as agent procedure in `SKILL.md` rather than coded into a Python helper. This matches the original `books` skill's idiom and is appropriate for a skill that is primarily a runbook for the agent. The brainstorm itself frames these as procedural steps, not as functions. No regression vs. the pre-rename baseline.

5. **The `Provider` class XOR check** (`(default_root is None) == (default_root_glob is None)`) is a small but valuable invariant that prevents misconfiguration if someone later adds a third provider. Nice touch.

6. **Doc cross-linking via Obsidian wikilinks** (`[[pdf]]`, `[[providers]]`, `[[icloud]]`, `[[google-drive]]`) is consistent with the project's CLAUDE.md documentation conventions.

7. **One forward-looking suggestion (not actionable in this feature):** the slug collision rule lives in three places (`publish/SKILL.md` step 3, `icloud.md` "Slug collision" section, `google-drive.md` "Slug collision" section). If a third provider is added, that's four restatements. Consider extracting it into a single sentence under `providers.md` "Resolution order" with the other transport-symmetric rules, and replacing the per-provider sections with a one-line "See providers.md → Slug collision". Defer to a future cleanup task, not a blocker.

**Verdict: Aligned.** All 15 brainstorm intents delivered (one as documented procedure, which matches both the brainstorm framing and the pre-rename baseline). All 11 scope cuts respected. No drift. Cross-task consistency between T1 and T2 is clean.
