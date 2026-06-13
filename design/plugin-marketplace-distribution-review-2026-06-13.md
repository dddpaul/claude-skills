# Feature Review: plugin-marketplace-distribution

**Verdict: Aligned**

**Passes run:** 3, 5 (brainstorm scope cuts; out-of-scope creep)
**Passes skipped:**
- Pass 1 (PRD coverage) — no PRD found. `design/plugin-marketplace-distribution-prd.md` does not exist; only the brainstorm doc is present. The brainstorm is treated as the design-intent source; coverage is collapsed into Pass 5.
- Pass 2 (non-goal protection) — no PRD, no formal "Non-Goals" section. Brainstorm "Scope cuts" are covered by Pass 3 instead.
- Pass 4 (success-metric realism) — no PRD, no success-metric section. The brainstorm states only behavioural goals ("teammates can install via /plugin marketplace add"), which are testable by demonstration rather than instrumentation.

Custom rules: `.claude/ralph-review-rules.md` not present. Standard rubric applied.

---

## Intent → Implementation Matrix (Brainstorm-derived, in lieu of PRD)

| ID | Intent (brainstorm) | Status | Evidence |
|----|---------------------|--------|----------|
| ARCH-1 | Option A monorepo marketplace; repo IS the marketplace | Delivered | `/Users/paul/Private/Projects/ai/claude-skills/.claude-plugin/marketplace.json` at root |
| ARCH-2 | Marketplace name `dddpaul-claude-skills` | Delivered | `marketplace.json` line 2: `"name": "dddpaul-claude-skills"` |
| ARCH-3 | Two initial plugins: `architect` (arch-describe, arch-draw) and `presentation` (pptx-core-style, pptx-arch-style) | Delivered | `plugins/architect/skills/{arch-describe,arch-draw}`, `plugins/presentation/skills/{pptx-core-style,pptx-arch-style}` |
| ARCH-4 | Per-plugin SemVer; both start at `0.1.0` | Delivered | `plugins/architect/.claude-plugin/plugin.json` & `plugins/presentation/.claude-plugin/plugin.json` both carry `"version": "0.1.0"` |
| ARCH-5 | No git tags / no staging branch; master = release channel | Delivered (by omission) | No tag-creation or branch-policy code in diff |
| LAYOUT-1 | `.claude-plugin/marketplace.json` at root | Delivered | confirmed on disk, 576 bytes |
| LAYOUT-2 | `plugins/<domain>/.claude-plugin/plugin.json` + `plugins/<domain>/skills/<name>/SKILL.md` | Delivered | directory listing matches exactly |
| MAN-1 | `marketplace.json` matches design JSON | Delivered | byte-by-byte match (verified via `jq .`): same `name`, `owner.name`, two plugin entries with identical `name`/`source`/`description` strings |
| MAN-2 | Both `plugin.json` files share same field set (name, description, version, author, homepage, repository, license) | Delivered | both contain exactly those 7 fields; both use `Pavel Derendyaev`, `Apache-2.0`, and both URLs equal `https://github.com/dddpaul/claude-skills` |
| MAN-3 | `author.name` field uses full name "Pavel Derendyaev" (one of the open questions in brainstorm) | Resolved (default kept) | Both manifests use `Pavel Derendyaev`, consistent with brainstorm's "currently `Pavel Derendyaev` from git config" |
| MIG-1 | Plain `git mv` to preserve blame | Delivered | Diff shows `similarity index 100% / rename from … / rename to …` for all 6 skill files; `git log --diff-filter=R` confirms renames at the git layer |
| MIG-2 | No internal-path rewrites needed (relative links survive) | Delivered & verified | Only 3 relative refs exist (`arch-draw/SKILL.md` → `references/cheatsheet.md`, `references/agent-prompt.md`; `arch-describe/SKILL.md` → `references/architectures.md`); all 3 resolve at new location. No absolute or `../`-style links in skill bodies. |
| MIG-3 | All 4 root-level skill dirs removed | Delivered | `ls -d arch-describe arch-draw pptx-core-style pptx-arch-style` returns "No such file or directory" for all four |
| DOC-1 | README "Installation" rewritten with `/plugin marketplace add` + `/plugin install <plugin>@dddpaul-claude-skills`; old `claude config add skills` + settings.json snippet removed | Delivered | README.md lines 113-134; `grep -F "claude config add skills" README.md` returns nothing; `grep -F '"skills":' README.md` returns nothing |
| DOC-2 | README "Project Structure" tree redrawn | Delivered | README.md lines 85-111 show the nested plugins/ tree |
| DOC-3 | Each skill summary tagged with `*Plugin: architect*` / `*Plugin: presentation*` | Delivered | README.md L9, L30, L57, L70 |
| DOC-4 | "Creating New Skills" uses `plugins/<domain>/skills/<name>/` template AND mentions registering new domains in `marketplace.json` | Delivered | README.md L140-147 |
| DOC-5 | CLAUDE.md "Project-Specific" gets bullet covering layout + SemVer bump rules (patch/minor/major) | Delivered | CLAUDE.md L91 — single bullet covers `plugins/<domain>/skills/<name>/` layout, `.claude-plugin/marketplace.json` reference, AND all three SemVer levels (patch / minor / major) with rules |
| DOC-6 | README skill descriptions preserved (no opportunistic rewording) | Delivered | Diff against `8ce2c8a:README.md` confirms only structural additions (plugin tags, tree, install section) — every line of skill prose (Usage, Capabilities, Covers, Example, etc.) is byte-identical |

---

## Scope Cut Violations (Pass 3)

The brainstorm lists 7 explicit cuts; verifying each:

- **Option B (one repo per domain)** — not implemented. Only one repo touched.
- **Option C (per-plugin git tags)** — no tags created. `git tag` would be empty for this work.
- **Topic-themed marketplace name** — name stayed `dddpaul-claude-skills`, not renamed.
- **Renaming skills to drop prefixes** — all four skill dirs keep their original names; SKILL.md `name:` frontmatter unchanged.
- **Symlinking instead of moving** — `git mv` was used (rename detection at 100% similarity), no symlinks.
- **Per-skill scripts / hooks / commands / agents** — manifests do not declare any of these (only the 7 declared fields).
- **Public-OSS polish** — no CHANGELOG, no CONTRIBUTING, no docs site, no badges added.

**None detected.**

---

## Drift List (Pass 5)

Walking every hunk in the cumulative diff:

| Hunk | In-scope? | Justification |
|------|-----------|---------------|
| `.claude-plugin/marketplace.json` (new) | Yes | Core deliverable (ARCH-1, MAN-1) |
| `plugins/architect/.claude-plugin/plugin.json` (new) | Yes | Core deliverable (MAN-2) |
| `plugins/presentation/.claude-plugin/plugin.json` (new) | Yes | Core deliverable (MAN-2) |
| 6 × skill file renames | Yes | Migration (MIG-1) |
| `README.md` changes | Yes | DOC-1..DOC-4, DOC-6 |
| `CLAUDE.md` change | Yes | DOC-5 |
| `backlog/tasks/task-1*.md` (new) | Yes | Required by Ralph task lifecycle |
| `backlog/tasks/task-2*.md` (new) | Yes | Required by Ralph task lifecycle |
| `design/plugin-marketplace-distribution-brainstorm.md` (new) | Yes | The brainstorm doc itself; expected artefact |
| `.gitignore` +`.venv/` | Borderline-but-justified | `.venv/` is created by `uv run ruff check .` (verified — running ruff just now created `.venv/`). AC #8/#7 in both tasks required ruff to pass, which implicitly bootstraps a venv. Excluding it from VCS is correct hygiene. Not flagged. |
| `pyproject.toml` (new, 10 lines) | Borderline-but-justified | Likewise required for `uv run ruff check .` to function. Contents are minimal: `[project] name="workspace", version="0.1.0", requires-python=">=3.11", dependencies=[]` plus `[dependency-groups] dev = ["ruff>=0.15.17"]`. No unrelated dependencies snuck in. The project name `"workspace"` is a generic auto-bootstrapped default — see Reviewer Notes below. Not flagged. |
| `uv.lock` (new) | Borderline-but-justified | Lockfile for the ruff dependency above. Pinning a lockfile is standard uv hygiene per the repo's own CLAUDE.md ("All Python dependencies must be installed, synchronized, and locked using uv"). Not flagged. |

**No drift detected** that warrants opening a follow-up task.

---

## Reviewer Notes

1. **Adversarial JSON check** — confirmed byte-by-byte (modulo whitespace): `marketplace.json` matches the brainstorm spec exactly. Both plugin descriptions match the design's quoted long-form one-liners. Both `plugin.json` files have identical structure, both use `version=0.1.0`, both use the full repo URL for `homepage` and `repository`, both license `Apache-2.0`. No trailing commas, no rogue fields, no missing fields.

2. **One harmless wording delta worth knowing about** — the brainstorm shows the plugin.json descriptions as `"<one-line>"` (a placeholder), so concrete description text was an implementation choice. The implementer used:
   - `architect`: `"Architecture documentation and diagramming skills"` — same prefix as marketplace.json's longer entry.
   - `presentation`: `"Presentation style guides for architectural decks"` — shorter rewording (marketplace entry says "Presentation style guides for the pptx skill — corporate core-style and architecture-committee arch-style").

   Both are accurate and reasonable. This is intent-faithful, not drift.

3. **Brainstorm open question — author identity** — left as default (`Pavel Derendyaev`, not the `dddpaul` handle). Brainstorm explicitly flagged this as "Re-confirm at implementation time." If the operator prefers the handle, that's a one-line edit in two files. Mentioning so it's not forgotten.

4. **`pyproject.toml` name is `workspace`** — auto-generated by `uv init` and benign for an internal-only project, but technically not very descriptive. Consider a follow-up patch-bump task to rename to `claude-skills` or similar if/when the project ever publishes Python artifacts. Not blocking.

5. **Git history preserved** — `git log --follow plugins/architect/skills/arch-describe/SKILL.md` traces back through the rename to the original `Initial commit`. Rename detection works at 100% similarity for every moved file. The brainstorm's bet on `git mv` paid off.

6. **No internal-path rewrites needed — verified empirically** — `grep` for `references/` inside `plugins/` returns exactly 3 hits, all of which are relative-to-skill (`references/cheatsheet.md`, `references/agent-prompt.md`, `references/architectures.md`). All three files exist at the new locations. Brainstorm's MIG-2 prediction holds.

7. **Ruff still clean post-feature** — re-ran `uv run ruff check .` from cold: "All checks passed!" (after creating `.venv/`, which is now properly gitignored).

8. **One acceptance gap worth a sanity check** — none of the ACs actually exercised the marketplace by running `/plugin marketplace add` against a local clone. The brainstorm doesn't require this either, but as the operator: it would be worth running the end-to-end install flow once (locally or against a colleague's machine) before declaring victory, since this is a "ship it" feature and the user-facing UX is the whole point. Manifest correctness ≠ install success, especially for the manifest schema fields `marketplace.json` may or may not require (e.g., whether Claude Code's plugin loader insists on additional fields like `metadata.version` for the marketplace itself). The currently-shipped manifest matches the design, but the design was speculative about schema. Recommend an explicit verification step before broadcasting to teammates.

**Feature can ship.** The implementation matches the design intent and respects every scope cut. The two open questions from the brainstorm (author identity, install-flow smoke-test) are operator decisions, not blockers.

Files referenced (absolute):
- `/Users/paul/Private/Projects/ai/claude-skills/.claude-plugin/marketplace.json`
- `/Users/paul/Private/Projects/ai/claude-skills/plugins/architect/.claude-plugin/plugin.json`
- `/Users/paul/Private/Projects/ai/claude-skills/plugins/presentation/.claude-plugin/plugin.json`
- `/Users/paul/Private/Projects/ai/claude-skills/README.md`
- `/Users/paul/Private/Projects/ai/claude-skills/CLAUDE.md`
- `/Users/paul/Private/Projects/ai/claude-skills/design/plugin-marketplace-distribution-brainstorm.md`
- `/Users/paul/Private/Projects/ai/claude-skills/pyproject.toml`
- `/Users/paul/Private/Projects/ai/claude-skills/.gitignore`
