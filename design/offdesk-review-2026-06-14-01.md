# Feature Review: offdesk (second pass)

**Verdict: Aligned**

**Passes run:** 1, 3, 5
**Passes skipped:** 2, 4 — no PRD exists (`design/offdesk-prd.md` not present), only a brainstorm with three addenda. Pass 2 (non-goal protection) requires a PRD non-goals section — the brainstorm "Scope cuts" are evaluated under Pass 3 instead. Pass 4 (success metrics) cannot run without a PRD metrics section.

No `.claude/ralph-review-rules.md` file present — standard rubric only.

## Intent → Implementation Matrix

Carry-over rows from the 2026-06-14 review (B-1 … B-19) plus three new rows specific to TASK-5 (B-20 env var contract, B-21 marketplace rewording, B-22 plugin version bump).

| ID | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| B-1 | Plugin packaging: new `obsidian` plugin in marketplace, third entry, source `./plugins/obsidian` | Delivered | `.claude-plugin/marketplace.json` lines 14–18: third entry present, source path correct. Description updated by TASK-5 — see B-21. |
| B-2 | Plugin manifest mirrors architect/presentation: name, description, author, license, homepage/repo URLs | Delivered | `plugins/obsidian/.claude-plugin/plugin.json` has all 7 fields, same shape as siblings. Version field now `0.2.0` (B-22). |
| B-3 | SKILL.md frontmatter `name: offdesk` + all 12 refined trigger phrases (addendum #3) | Delivered | `plugins/obsidian/skills/offdesk/SKILL.md` lines 1–4: every refined trigger from addendum #3 verbatim, including "оффдеск" Cyrillic and delayed-review phrasings. |
| B-4 | SKILL.md body section order: Push, Pull, Cleanup, Slug collision, Annotation convention, Setup | **Delivered with expansion** | New "Vault path" section now precedes Push (lines 18–35) per addendum #1 / TASK-5 AC#1. Original section order otherwise preserved (Push line 37, Pull line 84, Cleanup line 117, Slug collision line 128, Annotation line 138, Setup line 148). |
| B-5 | Push procedure: git rev-parse + pwd fallback, slug=basename, mkdir vault subdir, 3-key frontmatter merge, no second `---` block, keep existing keys | Delivered | SKILL.md lines 43–67: all elements present. Step 3 now uses VAULT_ROOT expansion (B-20). |
| B-6 | Pull procedure: correct grep regex, frontmatter parse for source-back, `<source-file>:<line>` format, confirm before modifying source | Delivered | SKILL.md lines 92–108: regex `^>\s*\[!ai\]` line 96, frontmatter parse lines 99–103, report format line 104, "Never auto-apply" line 108. Grep target now uses VAULT_ROOT (B-20). |
| B-7 | Cleanup procedure: strip `offdesk-*` keys AND `>[!ai]` callouts before upstream push | Delivered | SKILL.md lines 110–126: both bullets present. Vault-path mention rewritten to `$VAULT_ROOT/<slug>/` (line 125) per TASK-5 scope. |
| B-8 | Slug collision: short hash suffix of project_root | Delivered | SKILL.md lines 128–135: example `foo-a1b2c3`, sha1, stable. Vault root reference now `$VAULT_ROOT/foo/` (line 131). |
| B-9 | Annotation convention: `>[!ai]` for Claude, `>[!todo]` ignored, multi-line, no-space/with-space | Delivered | SKILL.md lines 137–145: all four points covered. No regression. |
| B-10 | Setup section links to references/setup.md | Delivered | SKILL.md line 152 retains `[references/setup.md](references/setup.md)`. |
| B-11 | Setup reference covers Syncthing macOS, Syncthing Android via F-Droid, QR pairing, Obsidian Android install + path, Templates plugin with both callout files, toolbar bindings, all 6 .stignore patterns | Delivered | `references/setup.md`: brew lines 9–12, Android+F-Droid lines 36–42, Obsidian Android path line 48, Templates+toolbar lines 56–73, all 6 .stignore patterns lines 90–96. |
| B-12 | Frontmatter merge: prefer inline ≤30 lines, otherwise script. 122-line stdlib script with edge-case handling | Delivered with caveat | `scripts/merge-frontmatter.py` unchanged by TASK-5 (no diff to the script in the v0.1.0→v0.2.0 range). Still stdlib-only, still handles the three documented edge cases, still idempotent. **D-2 unaddressed** — see Drift list. |
| B-13 | README: offdesk subsection with `*Plugin: obsidian*` tag + RU triggers | Delivered | README.md lines 81–94: heading, plugin tag, both required Russian triggers. No regression. |
| B-14 | README Project Structure tree extended with obsidian plugin subtree | Delivered | README.md lines 117–135: shows `obsidian/` last sibling, `SKILL.md`, `references/setup.md`. Tree balancing (`├──` for presentation, `└──` for obsidian) intact. |
| B-15 | README Installation block: `/plugin install obsidian@dddpaul-claude-skills` line | Delivered | README.md line 150. No regression. |
| B-16 | CLAUDE.md plugin-layout rule still covers obsidian without edits | Delivered | `git diff --name-only` confirms CLAUDE.md untouched across all three tasks. |
| B-17 | Addendum #1: configurable vault path via `OFFDESK_OBSIDIAN_VAULT`, default `~/Obsidian/offdesk/`, documented near top of body | **NEW: Delivered** (was Missing in prior review) | TASK-5 closed this — see B-20/B-21/B-22 below for the constituent pieces. |
| B-18 | Addendum #2: implementation home in this repo as `plugins/obsidian/skills/offdesk/` | Delivered | Unchanged from v0.1.0. |
| B-19 | Addendum #3 trigger refinements | Delivered | Unchanged from v0.1.0; no regression from TASK-5. |
| B-20 | **NEW (TASK-5):** SKILL.md documents env var contract near top of body (default, override mechanism, restart-shell note); push step 3, pull step 2, helper-script call site, and write target all use `VAULT_ROOT="${OFFDESK_OBSIDIAN_VAULT:-$HOME/Obsidian/offdesk}"` with trailing-slash normalization | Delivered | "Vault path" section at SKILL.md lines 18–35 covers default + override + restart note. VAULT_ROOT expansion at lines 31, 49, 94 (three resolution sites); trailing-slash strip at lines 32, 50, 95; mkdir at line 51; write target `$VAULT_ROOT/<slug>/<filename>.md` at line 65; helper-script call site at line 76 (`--dst "$VAULT_ROOT/<slug>/<filename>.md"`); pull grep target at line 96. `grep -F '~/Obsidian/android' SKILL.md` returns zero matches — AC#5 satisfied verbatim. |
| B-21 | **NEW (TASK-5):** marketplace.json description uses generic "Obsidian vault" wording (no "phone/tablet") | Delivered | `.claude-plugin/marketplace.json` line 18: `"Obsidian vault tooling — offdesk push/pull for off-desk markdown review via Syncthing."` — exact match to addendum #1's prescribed text. `grep -iF 'phone' marketplace.json` returns zero matches. |
| B-22 | **NEW (TASK-5):** plugin.json version bumped 0.1.0 → 0.2.0 | Delivered | `plugins/obsidian/.claude-plugin/plugin.json` line 4: `"version": "0.2.0"`. Bump is correct per CLAUDE.md SemVer rules (broadened configuration surface, non-breaking since no v0.1.0 users). |

## Non-Goal Violations

Pass 2 skipped (no PRD non-goals section). The brainstorm's "Scope cuts" are evaluated under Pass 3.

## Scope Cut Violations

None detected. All v0.1.0 scope cuts still respected, and TASK-5 added no new scope:

- **No standalone CLI tool** — still only `merge-frontmatter.py` as a helper, explicitly permitted by the brainstorm.
- **No PDF rendering, Telegram bot, VPS** — absent.
- **No automatic feedback application** — SKILL.md line 108 "Never auto-apply" preserved.
- **No symlinks** — `merge-frontmatter.py` still writes real files via `args.dst.write_text`.
- **No iPad / second-device parallel vault** — addendum #1 explicitly notes the env var subsumes the need for separate device-named vaults; no per-device subdir scaffolding introduced.
- **No automating user-setup steps** — `setup.md` continues to document manual steps only.

## Drift List

**D-1 (CLOSED).** Addendum #1 (configurable vault path, default rename, marketplace rewording) is now fully implemented. Specifically:

- SKILL.md: zero remaining `~/Obsidian/android` strings (verified by `grep -F`); env var contract documented in the new "Vault path" section before Push; push step 3, pull step 2, helper-script call site, and write target all use the prescribed VAULT_ROOT expansion with trailing-slash strip.
- setup.md: laptop vault root is `~/Obsidian/offdesk` (lines 27, 86); env var override sentence present (lines 29–32); only remaining `Obsidian/android` string is the Android-side `/storage/emulated/0/Obsidian/android/` at line 48 — exactly as addendum #1 prescribes and explicitly justified at lines 51–53.
- marketplace.json description now `"Obsidian vault tooling — offdesk push/pull for off-desk markdown review via Syncthing."` — verbatim match.
- plugin.json version `0.2.0`.

All three commits referenced in task notes (`89d7a44`, `cc8c72d`, `987a52a`) match the merged history.

**D-2 (UNCHANGED, deliberately out of scope for TASK-5).** `merge-frontmatter.py` still ships without tests, and the two minor code issues from the prior review remain:

- The `merge_keys` function at line 34 writes `f"{key}: {value}"` without YAML-escaping the value (line 75 of the script). Current callers (ISO timestamp, relative path, absolute project root) are unlikely to contain YAML-significant characters in practice, but the script is unchanged from v0.1.0 — TASK-5 explicitly excluded this in its "Out of scope" section.
- The dead-code `missing = [k for k in OFFDESK_KEYS if k not in updates]` block at lines 111–113 still always evaluates empty because `updates` is built with all three keys in `main`. Cosmetic but cruft.

TASK-5 explicitly carved D-2 out as a future task ("merge-frontmatter.py minor cleanup … Separate task if desired"). Not a regression, not a blocker — but it remains as a candidate follow-up if a `feature:offdesk` v0.2.1 patch is desired before declaring the area frozen.

**D-3 (UNCHANGED, informational).** SKILL.md lines 70–82 (the "For the YAML merge, the inline shell + python is acceptable when small; otherwise call the helper" wording) is the same minor inline-vs-helper ambiguity flagged in the prior review. Not introduced by TASK-5; preserved verbatim.

**D-4 (UNCHANGED, informational).** README tree still does not list `scripts/merge-frontmatter.py` under `skills/offdesk/`. Same as prior review; TASK-4's AC didn't require it, and TASK-5 did not touch README.md (correctly so per its "Out of scope" section: "README.md Installation block changes — none needed since the install command is identical").

**D-5 (NEW, informational, non-blocking).** TASK-5's implementation notes explicitly call out three remaining "phone/tablet" mentions in SKILL.md that the reviewer of TASK-5 considered out of scope under AC#8 (which narrowed the rewording to marketplace.json only):

- SKILL.md line 3 (frontmatter description): `"Copy markdown from any project into a Syncthing-synced Obsidian vault on phone/tablet, then pull annotated ..."`.
- SKILL.md line 9 (intro paragraph): `"... vault on a phone/tablet for off-desk reading, ..."`.
- SKILL.md line 67 (push step 7 narrative): `"Syncthing propagates to the phone/tablet automatically."`.

Addendum #1 instruction 4 only literally addresses the marketplace entry, so this is not a textual violation of the canonical design. But the addendum's stated *motivation* ("misleading default … device-named folders … iPad would get a confusing default name") applies equally to SKILL.md prose. Since this is a generic "off-desk reading device" abstraction, replacing "phone/tablet" with "off-desk device" or "secondary device" in SKILL.md prose would be more consistent with the device-neutral rebrand. Flagging as informational because:
  1. The TASK-5 reviewer already approved the AC-narrowing decision.
  2. README.md line 84 also says "phone/tablet" and was not touched by TASK-5 — so any rewording would need to span README too for consistency.
  3. The trigger phrase `"send to phone for review"` in SKILL.md frontmatter (line 3) and README.md (line 84) is part of the *user-facing trigger set* — addendum #3 retained that English phrasing intentionally, so a wholesale "phone" purge would break a documented trigger.

Recommend leaving D-5 as-is unless a v0.2.1 pass also revisits trigger phrasings.

**No new structural drift introduced by TASK-5.** Diff `--name-only` confirms only nine files touched across the entire feature: marketplace.json, README.md, three backlog task files, plugin.json, SKILL.md, setup.md, merge-frontmatter.py. CLAUDE.md untouched. pyproject.toml / uv.lock untouched (no new dependencies). architect and presentation plugin manifests untouched. No opportunistic refactors, no formatting-only changes elsewhere.

## Reviewer Notes

1. **D-1 is closed; verdict moves from Partial to Aligned.** TASK-5 delivered exactly the four artifacts the prior review's recommended-follow-up paragraph called for: SKILL.md vault-path documentation + procedure threading, setup.md path migration, marketplace.json rewording, plugin.json version bump. The literal AC text in TASK-5 (10 ACs, all checked) maps 1:1 to the prior review's D-1 enumeration plus the addendum #1 instructions, so the closure is verifiable by grep rather than judgment.

2. **AC-vs-addendum hygiene improved.** TASK-5 was scoped *because* of the prior review's drift call-out, and its description explicitly cites the addendum and the prior review. This is the right pattern for handling AC-vs-design-doc drift after the fact — file a focused follow-up rather than retroactively edit the original task. The implementer of TASK-3 made the correct conservative judgment call (honor AC literal, flag follow-up), and TASK-5 closed the loop in a single iteration. Worth recording as a positive process signal for future Ralph runs.

3. **Plugin version semantics check out.** 0.1.0 → 0.2.0 minor bump per CLAUDE.md SemVer ("minor for new skills or broadened triggers"). TASK-5 broadens the configuration surface (env var support, configurable default) without breaking — no v0.1.0 users to migrate. If a v0.2.1 patch addresses D-2 (script tests + YAML escape + dead-code removal), that's the right semver per the rule ("patch for content tweaks"). If the operator wants D-5's SKILL.md/README "phone/tablet" wording softened to fully align with addendum #1's spirit, the bump would still be patch-level (cosmetic prose adjustment).

4. **`merge-frontmatter.py` is unchanged.** TASK-5 only adjusted the *destination path* passed to the script from SKILL.md — the script itself is byte-identical to its v0.1.0 form. D-2 remains tracked but out of scope for the v0.2.0 milestone.

5. **Verdict rationale.** All 22 design intents (19 carried over + 3 new from addendum #1) now Delivered. Zero non-goal violations, zero scope cuts violated, no new drift introduced. Only outstanding items are D-2 (script quality, deliberately deferred), D-3 (minor wording ambiguity, pre-existing), D-4 (README tree completeness, AC-compliant), and D-5 (informational SKILL.md prose suggestion). None of these block the Aligned verdict — they are candidate-follow-up territory, not drift.

6. **Recommended optional follow-up (single TASK-6, patch-level v0.2.1).** If the operator wants the feature area fully polished before freezing:
   - Add 3–5 pytest cases for `merge-frontmatter.py` covering: no existing frontmatter, in-place key update, append new keys, idempotent re-run, body trailing-newline preservation.
   - Remove the dead-code `missing` check.
   - Wrap YAML values in single quotes in `merge_keys` (defensive against future callers passing values with `:` or `#`).
   - Optional: rewrite SKILL.md lines 9 and 67 (and README line 84) to say "secondary device" instead of "phone/tablet" for full addendum #1 alignment, *while preserving* the `"send to phone for review"` trigger phrase per addendum #3.

   If the operator considers v0.2.0 the natural shipping point for the feature, none of D-2/D-3/D-4/D-5 are blockers and no further task is required to close out `feature:offdesk`.

**The feature is shippable at v0.2.0 and the cumulative implementation matches the canonical design intent.**
