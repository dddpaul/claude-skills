"""Verify the offdesk skill's transport routing and root resolution.

The skill ships two transports: ``syncthing`` (default) and ``icloud``.

``syncthing`` resolves its root through three tiers —
``OFFDESK_SYNCTHING_VAULT``, then the pre-transport alias
``OFFDESK_OBSIDIAN_VAULT``, then the literal ``~/Obsidian/offdesk``. The
alias is load-bearing: it is already set in the user's profile with project
folders behind it, so a tier that silently stopped working would strand
them.

``icloud`` resolves its root by globbing
``~/Library/Mobile Documents/iCloud~md~obsidian/Documents/*``, because the
vault directory is named by the user in Obsidian on iOS. 0 or >1 matching
directories must raise ``TransportResolutionError`` naming
``OFFDESK_ICLOUD_VAULT`` — never auto-pick, which would write review notes
into the wrong vault.

Routing: each of the eight pre-iCloud push phrases must still resolve to
``syncthing`` and each of the six new phrases to ``icloud``; pull scans
both vaults unless the phrase names one.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).parent
SCRIPTS = HERE.parent / "scripts"
TRANSPORTS_PY = SCRIPTS / "transports.py"
MERGE_PY = SCRIPTS / "merge-frontmatter.py"

ICLOUD_GLOB_PARENT = (
    "Library/Mobile Documents/iCloud~md~obsidian/Documents"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_module():
    return _load(TRANSPORTS_PY, "offdesk_transports")


def _load_merge():
    return _load(MERGE_PY, "offdesk_merge_frontmatter")


SYNCTHING_TRIGGERS = (
    "send to offdesk",
    "send to phone for review",
    "review later",
    "check later",
    "положи это в offdesk",
    "положи это в оффдеск",
    "посмотрю позже",
    "проверю позже",
)

ICLOUD_TRIGGERS = (
    "send to offdesk icloud",
    "offdesk icloud",
    "offdesk on icloud",
    "положи в offdesk icloud",
    "положи в оффдеск айклауд",
    "оффдеск айклауд",
)

NEUTRAL_PULL_TRIGGERS = (
    "review my offdesk notes",
    "check offdesk feedback",
    "посмотри оффдеск фидбэк",
    "проверь оффдеск",
)

ICLOUD_PULL_TRIGGERS = (
    "check offdesk icloud",
    "review my offdesk icloud notes",
    "проверь оффдеск айклауд",
    "посмотри оффдеск айклауд фидбэк",
)

SYNCTHING_PULL_TRIGGERS = (
    "check offdesk syncthing",
    "review my offdesk syncthing notes",
    "проверь оффдеск синктинг",
    "посмотри оффдеск синктинг фидбэк",
)


# --------------------------------------------------------------------------
# Push routing
# --------------------------------------------------------------------------


def test_the_eight_pre_icloud_phrases_are_exactly_the_syncthing_triggers():
    mod = _load_module()
    assert mod.TRANSPORTS["syncthing"].triggers == SYNCTHING_TRIGGERS
    assert len(SYNCTHING_TRIGGERS) == 8


@pytest.mark.parametrize("phrase", SYNCTHING_TRIGGERS)
def test_each_existing_phrase_resolves_to_syncthing(phrase: str):
    mod = _load_module()
    assert mod.resolve_transport(phrase) == "syncthing"


@pytest.mark.parametrize("phrase", ICLOUD_TRIGGERS)
def test_each_icloud_phrase_resolves_to_icloud(phrase: str):
    mod = _load_module()
    assert mod.resolve_transport(phrase) == "icloud"


@pytest.mark.parametrize("phrase", SYNCTHING_TRIGGERS + ICLOUD_TRIGGERS)
def test_trigger_matching_is_case_and_whitespace_insensitive(phrase: str):
    mod = _load_module()
    expected = mod.resolve_transport(phrase)
    assert mod.resolve_transport(phrase.upper()) == expected
    assert mod.resolve_transport(f"  {phrase}  ") == expected


def test_syncthing_is_the_default_for_an_unmarked_phrase():
    mod = _load_module()
    assert mod.DEFAULT_TRANSPORT == "syncthing"
    assert mod.resolve_transport("offdesk this file") == "syncthing"
    assert mod.resolve_transport("") == "syncthing"


@pytest.mark.parametrize(
    "phrase",
    [
        "send this to offdesk icloud please",
        "offdesk, но в icloud",
        "положи это в оффдеск айклауд, пожалуйста",
    ],
)
def test_marked_but_unlisted_phrase_still_routes_to_icloud(phrase: str):
    """A phrase carrying the icloud marker must not fall through to the
    default — that would silently write an iPad-bound note into the
    Syncthing vault."""
    mod = _load_module()
    assert mod.resolve_transport(phrase) == "icloud"


def test_marker_needs_a_word_boundary():
    mod = _load_module()
    assert mod.resolve_transport("send to offdesk unicloudy") == "syncthing"


# --------------------------------------------------------------------------
# Pull scope
# --------------------------------------------------------------------------


@pytest.mark.parametrize("phrase", NEUTRAL_PULL_TRIGGERS)
def test_neutral_pull_phrase_scans_both_vaults(phrase: str):
    mod = _load_module()
    assert mod.resolve_pull_scope(phrase) == ("syncthing", "icloud")


@pytest.mark.parametrize("phrase", ICLOUD_PULL_TRIGGERS)
def test_icloud_pull_phrase_narrows_to_icloud(phrase: str):
    mod = _load_module()
    assert mod.resolve_pull_scope(phrase) == ("icloud",)


@pytest.mark.parametrize("phrase", SYNCTHING_PULL_TRIGGERS)
def test_syncthing_pull_phrase_narrows_to_syncthing(phrase: str):
    mod = _load_module()
    assert mod.resolve_pull_scope(phrase) == ("syncthing",)


def test_pull_phrase_naming_both_transports_scans_both():
    mod = _load_module()
    scope = mod.resolve_pull_scope("check offdesk icloud and syncthing")
    assert scope == ("syncthing", "icloud")


# --------------------------------------------------------------------------
# syncthing root resolution — three tiers
# --------------------------------------------------------------------------


def test_syncthing_env_var_overrides_everything():
    mod = _load_module()
    root = mod.resolve_root(
        "syncthing",
        env={
            "OFFDESK_SYNCTHING_VAULT": "/tmp/offdesk-syncthing",
            "OFFDESK_OBSIDIAN_VAULT": "/tmp/offdesk-legacy",
        },
    )
    assert root == Path("/tmp/offdesk-syncthing")


def test_legacy_obsidian_vault_var_is_used_when_syncthing_var_unset():
    mod = _load_module()
    root = mod.resolve_root(
        "syncthing", env={"OFFDESK_OBSIDIAN_VAULT": "/tmp/offdesk-legacy"}
    )
    assert root == Path("/tmp/offdesk-legacy")


def test_syncthing_default_root_when_no_env_var_set(tmp_path, monkeypatch):
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    assert mod.resolve_root("syncthing", env={}) == tmp_path / "Obsidian" / "offdesk"


def test_syncthing_env_vars_strip_trailing_slash():
    mod = _load_module()
    assert mod.resolve_root(
        "syncthing", env={"OFFDESK_SYNCTHING_VAULT": "/tmp/offdesk-syncthing/"}
    ) == Path("/tmp/offdesk-syncthing")
    assert mod.resolve_root(
        "syncthing", env={"OFFDESK_OBSIDIAN_VAULT": "/tmp/offdesk-legacy/"}
    ) == Path("/tmp/offdesk-legacy")


def test_empty_syncthing_var_falls_through_to_the_legacy_alias():
    mod = _load_module()
    root = mod.resolve_root(
        "syncthing",
        env={
            "OFFDESK_SYNCTHING_VAULT": "   ",
            "OFFDESK_OBSIDIAN_VAULT": "/tmp/offdesk-legacy",
        },
    )
    assert root == Path("/tmp/offdesk-legacy")


def test_syncthing_env_vars_expand_a_tilde(tmp_path, monkeypatch):
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    root = mod.resolve_root(
        "syncthing", env={"OFFDESK_SYNCTHING_VAULT": "~/vaults/offdesk"}
    )
    assert root == tmp_path / "vaults" / "offdesk"


# --------------------------------------------------------------------------
# icloud root resolution — glob contract
# --------------------------------------------------------------------------


def _make_icloud_vault(home: Path, name: str) -> Path:
    root = home / ICLOUD_GLOB_PARENT / name
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_icloud_glob_exactly_one_match_resolves(tmp_path, monkeypatch):
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    expected = _make_icloud_vault(tmp_path, "offdesk")
    assert mod.resolve_root("icloud", env={}) == expected


def test_icloud_glob_zero_matches_hard_fails(tmp_path, monkeypatch):
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(mod.TransportResolutionError) as excinfo:
        mod.resolve_root("icloud", env={})
    assert "OFFDESK_ICLOUD_VAULT" in str(excinfo.value)


def test_icloud_glob_multi_vault_hard_fails_and_lists_every_match(
    tmp_path, monkeypatch
):
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    _make_icloud_vault(tmp_path, "offdesk")
    _make_icloud_vault(tmp_path, "personal")
    _make_icloud_vault(tmp_path, "work")
    with pytest.raises(mod.TransportResolutionError) as excinfo:
        mod.resolve_root("icloud", env={})
    msg = str(excinfo.value)
    assert "OFFDESK_ICLOUD_VAULT" in msg
    for name in ("offdesk", "personal", "work"):
        assert name in msg


def test_icloud_glob_ignores_a_stray_file_beside_the_vaults(
    tmp_path, monkeypatch
):
    """Only directories are candidates: the pattern ends in a bare ``*``, so
    a loose file in the container must not fake a multi-vault machine."""
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    expected = _make_icloud_vault(tmp_path, "offdesk")
    (tmp_path / ICLOUD_GLOB_PARENT / "notes.md").write_text("x", encoding="utf-8")
    assert mod.resolve_root("icloud", env={}) == expected


def test_icloud_env_override_skips_the_glob_entirely(tmp_path, monkeypatch):
    """HOME points at an empty tree, which would hard-fail under the glob;
    the env value is used verbatim instead."""
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    override = "/tmp/explicit-icloud-vault"
    root = mod.resolve_root("icloud", env={"OFFDESK_ICLOUD_VAULT": override})
    assert root == Path(override)


def test_icloud_env_override_strips_trailing_slash(tmp_path, monkeypatch):
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    root = mod.resolve_root(
        "icloud", env={"OFFDESK_ICLOUD_VAULT": "/tmp/explicit-icloud-vault/"}
    )
    assert root == Path("/tmp/explicit-icloud-vault")


def test_icloud_has_no_legacy_alias():
    mod = _load_module()
    assert mod.TRANSPORTS["icloud"].env_vars == ("OFFDESK_ICLOUD_VAULT",)


def test_a_transport_needs_exactly_one_kind_of_default_root():
    mod = _load_module()
    with pytest.raises(ValueError):
        mod.Transport(
            name="bogus",
            env_var="OFFDESK_BOGUS_VAULT",
            triggers=(),
            markers=(),
            pull_triggers=(),
            default_root="~/bogus",
            default_root_glob="~/bogus/*",
        )


# --------------------------------------------------------------------------
# offdesk-transport frontmatter key
# --------------------------------------------------------------------------


def test_merge_frontmatter_transport_names_match_the_resolver():
    """merge-frontmatter.py stays standalone-runnable by repeating the
    transport names; this pins the copy to the resolver."""
    mod = _load_module()
    merge = _load_merge()
    assert merge.TRANSPORT_NAMES == tuple(mod.TRANSPORTS)
    assert merge.DEFAULT_TRANSPORT == mod.DEFAULT_TRANSPORT


def _run_merge(tmp_path: Path, source: str, *extra: str) -> str:
    merge = _load_merge()
    src = tmp_path / "note.md"
    dst = tmp_path / "vault" / "proj" / "note.md"
    src.write_text(source, encoding="utf-8")
    argv = [
        "--src",
        str(src),
        "--dst",
        str(dst),
        "--offdesk-source",
        "docs/note.md",
        "--offdesk-project-root",
        "/home/user/proj",
        "--offdesk-copied-at",
        "2026-08-23T09:00:00Z",
        *extra,
    ]
    assert merge.main(argv) == 0
    return dst.read_text(encoding="utf-8")


def test_merge_frontmatter_writes_the_transport_key(tmp_path):
    out = _run_merge(
        tmp_path, "# Note\n\nbody\n", "--offdesk-transport", "icloud"
    )
    assert "offdesk-transport: icloud" in out


def test_merge_frontmatter_transport_defaults_to_syncthing(tmp_path):
    out = _run_merge(tmp_path, "# Note\n\nbody\n")
    assert "offdesk-transport: syncthing" in out


def test_merge_frontmatter_preserves_existing_keys(tmp_path):
    source = (
        "---\n"
        "title: Existing\n"
        "confluence-page-id: '12345'\n"
        "tags:\n"
        "  - one\n"
        "  - two\n"
        "---\n"
        "\n# Note\n\nbody\n"
    )
    out = _run_merge(
        tmp_path, source, "--offdesk-transport", "icloud"
    )
    assert "title: Existing" in out
    assert "confluence-page-id: '12345'" in out
    assert "tags:\n  - one\n  - two\n" in out
    assert "offdesk-transport: icloud" in out
    assert out.count("offdesk-transport:") == 1
    assert out.endswith("# Note\n\nbody\n")


def test_merge_frontmatter_updates_an_existing_transport_key(tmp_path):
    source = "---\ntitle: T\noffdesk-transport: syncthing\n---\n\nbody\n"
    out = _run_merge(
        tmp_path, source, "--offdesk-transport", "icloud"
    )
    assert out.count("offdesk-transport:") == 1
    assert "offdesk-transport: icloud" in out
    assert "offdesk-transport: syncthing" not in out


def test_merge_frontmatter_rejects_an_unknown_transport(tmp_path):
    with pytest.raises(SystemExit):
        _run_merge(tmp_path, "body\n", "--offdesk-transport", "dropbox")


def test_offdesk_transport_is_a_declared_offdesk_key():
    merge = _load_merge()
    assert "offdesk-transport" in merge.OFFDESK_KEYS
    assert all(key.startswith("offdesk-") for key in merge.OFFDESK_KEYS)
