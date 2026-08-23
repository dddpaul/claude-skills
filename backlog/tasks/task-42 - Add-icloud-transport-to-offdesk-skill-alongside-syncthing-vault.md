---
id: TASK-42
title: Add icloud transport to offdesk skill alongside syncthing vault
status: To Do
assignee: []
created_date: '2026-08-23 07:57'
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
- [ ] #1 transports.py resolves the syncthing root with precedence OFFDESK_SYNCTHING_VAULT then OFFDESK_OBSIDIAN_VAULT then ~/Obsidian/offdesk, with a test covering all three tiers
- [ ] #2 transports.py expands the icloud glob: 0 matches raises an error naming OFFDESK_ICLOUD_VAULT; exactly 1 match returns that path; more than 1 raises an error listing every match
- [ ] #3 Each of the eight existing offdesk phrases resolves to syncthing and each new icloud phrase resolves to icloud, proven by a parametrised test
- [ ] #4 A test asserts the offdesk and publish trigger sets are disjoint and that no offdesk phrase contains ipad, айпад, books or книги
- [ ] #5 merge-frontmatter.py accepts --offdesk-transport and writes an offdesk-transport key without disturbing existing frontmatter keys
- [ ] #6 SKILL.md frontmatter and body document both transports with syncthing as the default plus the new icloud trigger phrases, and retain no claim that the vault is Syncthing-only
- [ ] #7 SKILL.md pull section specifies the both-vault default, transport and mtime tagging in the report, and the zero-result .icloud stub check
- [ ] #8 references/transports.md exists with the transport table, resolution order and trigger mapping, and references/setup.md gains an iCloud section covering vault creation on iOS, the resulting Mac path and the env var
- [ ] #9 README ### offdesk section, plugins/obsidian/.claude-plugin/plugin.json at version 0.3.0, and the obsidian entry in .claude-plugin/marketplace.json all describe both transports
- [ ] #10 uv run ruff check . passes and uv run pytest shows no new failures beyond the pre-existing test_helper_renders_canonical_decision_tree environment failure
<!-- AC:END -->
