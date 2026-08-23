---
id: TASK-42
title: Add icloud transport to offdesk skill alongside syncthing vault
status: Done
assignee: []
created_date: '2026-08-23 07:57'
updated_date: '2026-08-23 08:28'
labels:
  - 'feature:offdesk-icloud-transport'
dependencies: []
priority: medium
ordinal: 42000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**Direction:** Option B — multi-transport `offdesk`: add an `icloud` transport alongside the existing Syncthing vault,
using the named-transport vocabulary `publish` already uses for providers, so `.md` round-trips through an Obsidian
vault on iCloud for iPad review.

**Locked decisions (with rationale):**

- **Two named transports, `syncthing` + `icloud`, one env var each.** *Rationale:* mirrors `publish`'s provider model,
  which already solved env-vs-glob resolution and multi-match ambiguity in this same repo.
- **`icloud` root defaults to the glob `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/*`.** *Rationale:* the
  Obsidian iOS vault name is chosen by the user, so the path cannot be a literal.
- **Glob contract: 0 → hard-fail naming the env var; 1 → use; >1 → hard-fail listing candidates, never auto-pick.**
  *Rationale:* byte-identical to the `google-drive` / `onedrive` rule; silently guessing a vault would write notes into
  the wrong one.
- **`OFFDESK_OBSIDIAN_VAULT` remains a working alias for `syncthing`, ahead of the literal default and behind
  `OFFDESK_SYNCTHING_VAULT`.** *Rationale:* it is already set in the user's profile with seven project folders behind it.
- **`syncthing` is the default transport; all eight existing phrases keep their meaning.** *Rationale:* preserves muscle
  memory and existing folders; `icloud` is opt-in per push.
- **offdesk triggers are anchored on "offdesk"/"оффдеск" and must never contain `ipad`/`айпад`/`books`/`книги`.**
  *Rationale:* those belong to `publish`'s icloud provider, which renders PDF and is push-only — a shared utterance
  would be unresolvable.
- **Layout stays `<vault-root>/<project-slug>/<filename>.md` for both transports.** *Rationale:* symmetric and already
  proven; `Reading/` is `publish` vocabulary for a different job.
- **Pull spans both vaults by default, tagged with transport and mtime; an explicit phrase narrows to one.**
  *Rationale:* the user should not have to recall which device an annotation was left on; mtime exposes sync lag.
- **No `brctl` on the happy path; only on a zero-annotation result, check for `*.icloud` stubs and report
  unmaterialized files.** *Rationale:* dataless files materialize transparently on read, so a pre-download is wasted
  work; the stub case is the only silent-miss path and is cheaper to catch after the fact.
- **Pull search scope is pinned to `<vault>/<slug>/`.** *Rationale:* a `find` over the whole iCloud tree was measured at
  >2 minutes.
- **New frontmatter key `offdesk-transport`; Cleanup unchanged.** *Rationale:* makes a vault copy self-describing; the
  existing `offdesk-*` wildcard already strips it.
- **One task, `obsidian` plugin bumped `0.2.1 → 0.3.0`.** *Rationale:* additive feature; splitting would ship a skill
  advertising a transport it cannot resolve.
- **All artifacts authored in English**, with RU trigger phrases kept verbatim as data.

**Scope cuts:**

- No push to both transports in one invocation.
- No `brctl download` on the pull happy path.
- No deduplication of annotations across vaults.
- No migration of the seven existing project folders out of the Syncthing vault.
- No deprecation warning or removal for `OFFDESK_OBSIDIAN_VAULT`.
- No transports beyond these two (no dropbox/box/etc.).
- No changes to `publish`'s triggers, providers, or behaviour.
- No `Reading/`-style subfolder inside the vault.

**Acceptance criteria (sketch):**

- `transports.py` resolves the `syncthing` root with precedence `OFFDESK_SYNCTHING_VAULT` → `OFFDESK_OBSIDIAN_VAULT` →
  `~/Obsidian/offdesk`, proven by tests covering all three tiers.
- `transports.py` expands the `icloud` glob and returns the single match; 0 matches raises an error naming
  `OFFDESK_ICLOUD_VAULT`; >1 raises an error listing every match.
- Each of the eight existing offdesk phrases resolves to `syncthing`; each new icloud phrase resolves to `icloud`.
- A test asserts the offdesk and publish trigger sets are disjoint and that no offdesk phrase contains
  `ipad`/`айпад`/`books`/`книги`.
- `merge-frontmatter.py` accepts `--offdesk-transport` and writes an `offdesk-transport` key without disturbing existing
  frontmatter keys.
- `SKILL.md` documents both transports, the syncthing default, pull-across-both with transport+mtime tagging, and the
  zero-result `.icloud` stub check; no remaining claim that the vault is Syncthing-only.
- `references/transports.md` exists with the transport table, resolution order, and trigger mapping.
- `references/setup.md` has an iCloud section covering vault creation on iOS, the resulting Mac path, and the env var.
- `README.md` `### offdesk` names both transports with at least three example trigger phrases.
- `plugins/obsidian/.claude-plugin/plugin.json` is `0.3.0`, and the `obsidian` entry in `.claude-plugin/marketplace.json`
  describes both transports.
- `uv run ruff check .` passes and `uv run pytest` shows no new failures.

**Implementation checklist:**

- Write `scripts/transports.py` modelled on `publish`'s `providers.py`.
- Add `--offdesk-transport` to `merge-frontmatter.py`.
- Rework `SKILL.md` (frontmatter, transports, push routing, pull semantics, stub check, transport-neutral prose).
- Write `references/transports.md`; add the iCloud section to `references/setup.md`.
- Write `tests/test_transports.py` and `tests/test_trigger_collisions.py`.
- Update `README.md`, `plugin.json` (0.3.0), and `.claude-plugin/marketplace.json`.
- Run `uv run ruff check .` and `uv run pytest`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 transports.py resolves the syncthing root with precedence OFFDESK_SYNCTHING_VAULT then OFFDESK_OBSIDIAN_VAULT then ~/Obsidian/offdesk, with a test covering all three tiers
- [x] #2 transports.py expands the icloud glob: 0 matches raises an error naming OFFDESK_ICLOUD_VAULT; exactly 1 match returns that path; more than 1 raises an error listing every match
- [x] #3 Each of the eight existing offdesk phrases resolves to syncthing and each new icloud phrase resolves to icloud, proven by a parametrised test
- [x] #4 A test asserts the offdesk and publish trigger sets are disjoint and that no offdesk phrase contains ipad, айпад, books or книги
- [x] #5 merge-frontmatter.py accepts --offdesk-transport and writes an offdesk-transport key without disturbing existing frontmatter keys
- [x] #6 SKILL.md frontmatter and body document both transports with syncthing as the default plus the new icloud trigger phrases, and retain no claim that the vault is Syncthing-only
- [x] #7 SKILL.md pull section specifies the both-vault default, transport and mtime tagging in the report, and the zero-result .icloud stub check
- [x] #8 references/transports.md exists with the transport table, resolution order and trigger mapping, and references/setup.md gains an iCloud section covering vault creation on iOS, the resulting Mac path and the env var
- [x] #9 README ### offdesk section, plugins/obsidian/.claude-plugin/plugin.json at version 0.3.0, and the obsidian entry in .claude-plugin/marketplace.json all describe both transports
- [x] #10 uv run ruff check . passes and uv run pytest shows no new failures beyond the pre-existing test_helper_renders_canonical_decision_tree environment failure
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Plan: (1) scripts/transports.py modelled on publish's providers.py — Transport class, SYNCTHING (env OFFDESK_SYNCTHING_VAULT -> legacy alias OFFDESK_OBSIDIAN_VAULT -> ~/Obsidian/offdesk) and ICLOUD (env OFFDESK_ICLOUD_VAULT -> glob ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/*, 0/1/>1 contract, directory-only candidates), resolve_transport (push, default syncthing, icloud marker) and resolve_pull_scope (both vaults by default, explicit phrase narrows). (2) merge-frontmatter.py gains optional --offdesk-transport writing an offdesk-transport key. (3) SKILL.md reworked: transport-neutral prose, transports section, push routing, pull-across-both with transport+mtime tags, zero-result .icloud stub check. (4) references/transports.md new; references/setup.md gains an iCloud section. (5) tests/test_transports.py + tests/test_trigger_collisions.py. (6) README ### offdesk, plugin.json 0.3.0, marketplace.json obsidian entry. Baseline before changes: uv run pytest = 106 passed, 1 pre-existing failure in plugins/presentation/.../test_decision_tree_helper.py (unrelated); uv run ruff check . clean.

Commit: `f5c19e1` - task-42: add icloud transport to offdesk alongside the syncthing vault

Commit: `ab8a4d2` - task-42: make the icloud root snippet shell-agnostic and the stub check recursive

Commit: `db8bc4d` - task-42: skip dot-directories when the icloud snippet expands the container

Implemented on branch task-42 (3 commits: f5c19e1 implementation, ab8a4d2 + db8bc4d review fixes).

New scripts/transports.py mirrors publish's providers.py: a Transport class with one env var each, SYNCTHING (OFFDESK_SYNCTHING_VAULT -> OFFDESK_OBSIDIAN_VAULT alias -> ~/Obsidian/offdesk) and ICLOUD (OFFDESK_ICLOUD_VAULT -> glob ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/*, 0/1/>1 contract that never auto-picks). resolve_transport() routes push phrases (default syncthing; the eight pre-iCloud phrases unchanged), resolve_pull_scope() returns both transports unless a phrase names one. Two deliberate additions beyond the literal checklist, both reviewed and accepted: (a) a marker-word fallback so a marked-but-unlisted utterance ('send this to offdesk icloud please') cannot silently land in the Syncthing vault — the addendum's own rule is that icloud is 'always explicitly marked'; (b) directory-only candidates for the glob, since the pattern ends in a bare * and a stray file beside the vaults would otherwise fake a multi-match hard-fail.

merge-frontmatter.py gained --offdesk-transport (choices syncthing|icloud, default syncthing) writing an offdesk-transport key; its TRANSPORT_NAMES copy is pinned to TRANSPORTS by a test so the script stays standalone-runnable. Cleanup needed no edit (offdesk-* wildcard) beyond naming the new key.

SKILL.md reworked (transport-neutral prose, transports table + resolution order, push routing, pull-both with transport+mtime tags and no dedup, zero-result .icloud stub check); new references/transports.md; references/setup.md gained an 'iCloud — iPad setup' section (vault creation on iOS, resulting Mac path, env var, eviction/stub notes). README ### offdesk + tree updated; obsidian plugin.json 0.2.1 -> 0.3.0 with its description byte-identical to the marketplace obsidian entry (TASK-41 doc-parity precedent).

Tests: tests/test_transports.py (routing, pull scope, three-tier syncthing precedence, glob 0/1/>1, dir-only filtering, frontmatter key) and tests/test_trigger_collisions.py (offdesk vs publish sets disjoint, no ipad/айпад/books/книги in any offdesk phrase, no cross-skill substring containment, module<->SKILL.md parity both directions). +78 tests.

Gates: uv run ruff check . clean. uv run pytest 184 passed / 1 failed — test_helper_renders_canonical_decision_tree in plugins/presentation, pre-existing on master (verified 106 passed / same 1 failed at baseline), in a plugin this branch does not touch.

Review: the .claude-config-managed task-reviewer agent is UNREGISTERED in this checkout (Agent tool errors 'Agent type task-reviewer not found'), so an independent claude agent ran under the same charter. It found one BLOCKING defect — the icloud shell snippet used ${matches[0]}, which is empty under zsh (1-indexed arrays), so the exactly-one-match happy path would have written notes to /<slug>/ outside any vault. Fixed in ab8a4d2 by rewriting the snippet array-free and glob-free (find -mindepth 1 -maxdepth 1 -type d, count via wc -l, explicit exit 1 on both failure branches); verified byte-identical behaviour under sh, bash and zsh across 0/1/>1 vault fixtures. Also fixed: the stub check is now recursive (find -name '*.icloud'), and db8bc4d adds ! -name '.*' so a .Trash in the Obsidian container cannot fake a second vault — shell and Python resolver now agree on that fixture. Verdict APPROVED at db8bc4d after re-verification (9/10 source mutations caught; the survivor is a documented can't-fail trailing-slash test kept for symmetry with publish's identical pair). Known, accepted divergence: find -type d ignores a symlinked vault dir while os.path.isdir follows it; both sides fail safe and transports.md declares the module authoritative.
<!-- SECTION:NOTES:END -->
