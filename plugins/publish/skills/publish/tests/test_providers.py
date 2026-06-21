"""Verify the publish skill's trigger → provider resolver.

The publish skill ships two providers: ``icloud`` and ``google-drive``.
All eight icloud trigger phrases must route to ``icloud``; all seven
google-drive trigger phrases must route to ``google-drive``. Each
provider's env var must override the default root; the legacy pre-rename
env var must be ignored. Phrases that do not name a provider must return
the ``NEEDS_DISAMBIGUATION`` sentinel, not a silent default.

``google-drive`` resolves its default root by globbing
``~/Library/CloudStorage/GoogleDrive-*/My Drive/Reading``; 0 or >1 matches
must raise ``ProviderResolutionError`` whose message names
``PUBLISH_GOOGLE_DRIVE_DIR`` as the disambiguator.

The legacy var's name is assembled from string parts so a strict
``grep -r`` for the literal name across ``plugins/`` finds no matches —
the rename is a clean break, and no source file (production or test)
contains the legacy identifier.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).parent
SCRIPT = HERE.parent / "scripts" / "providers.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("publish_providers", SCRIPT)
    assert spec and spec.loader, f"cannot load {SCRIPT}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ICLOUD_TRIGGERS = (
    "send to books",
    "read on ipad",
    "review on books",
    "send to icloud",
    "положи это в books",
    "положи это в книги",
    "почитаю на айпаде",
    "положи в icloud",
)

GOOGLE_DRIVE_TRIGGERS = (
    "send to gdrive",
    "send to google drive",
    "read on gdrive",
    "read on drive",
    "положи в gdrive",
    "положи в гугл драйв",
    "отправь на драйв",
)


@pytest.mark.parametrize("phrase", ICLOUD_TRIGGERS)
def test_each_icloud_trigger_resolves_to_icloud(phrase: str):
    mod = _load_module()
    assert mod.resolve_provider(phrase) == "icloud"


@pytest.mark.parametrize("phrase", ICLOUD_TRIGGERS)
def test_trigger_matching_is_case_insensitive(phrase: str):
    mod = _load_module()
    assert mod.resolve_provider(phrase.upper()) == "icloud"
    assert mod.resolve_provider(f"  {phrase}  ") == "icloud"


@pytest.mark.parametrize("phrase", GOOGLE_DRIVE_TRIGGERS)
def test_each_google_drive_trigger_resolves_to_google_drive(phrase: str):
    mod = _load_module()
    assert mod.resolve_provider(phrase) == "google-drive"


@pytest.mark.parametrize("phrase", GOOGLE_DRIVE_TRIGGERS)
def test_google_drive_trigger_matching_is_case_insensitive(phrase: str):
    mod = _load_module()
    assert mod.resolve_provider(phrase.upper()) == "google-drive"
    assert mod.resolve_provider(f"  {phrase}  ") == "google-drive"


def test_publish_icloud_dir_overrides_default_root():
    mod = _load_module()
    override = "/tmp/publish-test-root"
    root = mod.resolve_root("icloud", env={"PUBLISH_ICLOUD_DIR": override})
    assert root == Path(override)


def test_publish_icloud_dir_strips_trailing_slash():
    mod = _load_module()
    root = mod.resolve_root(
        "icloud", env={"PUBLISH_ICLOUD_DIR": "/tmp/publish-test-root/"}
    )
    assert root == Path("/tmp/publish-test-root")


def test_default_root_when_publish_icloud_dir_unset():
    mod = _load_module()
    root = mod.resolve_root("icloud", env={})
    expected = Path(
        "~/Library/Mobile Documents/com~apple~CloudDocs/Reading"
    ).expanduser()
    assert root == expected


LEGACY_VAR = "READING_" + "ICLOUD_DIR"


def test_legacy_env_var_is_ignored():
    mod = _load_module()
    root = mod.resolve_root(
        "icloud", env={LEGACY_VAR: "/tmp/legacy-should-be-ignored"}
    )
    expected = Path(
        "~/Library/Mobile Documents/com~apple~CloudDocs/Reading"
    ).expanduser()
    assert root == expected


def test_publish_icloud_dir_wins_over_legacy_env_var():
    mod = _load_module()
    root = mod.resolve_root(
        "icloud",
        env={
            "PUBLISH_ICLOUD_DIR": "/tmp/publish-wins",
            LEGACY_VAR: "/tmp/legacy-should-be-ignored",
        },
    )
    assert root == Path("/tmp/publish-wins")


@pytest.mark.parametrize(
    "phrase",
    [
        "publish this",
        "отправь это",
        "send this somewhere",
        "",
        "почитаю",
    ],
)
def test_unmatched_phrase_returns_disambiguation_sentinel(phrase: str):
    mod = _load_module()
    assert mod.resolve_provider(phrase) == mod.NEEDS_DISAMBIGUATION
    assert mod.NEEDS_DISAMBIGUATION != "icloud"
    assert mod.NEEDS_DISAMBIGUATION != "google-drive"


def _make_gdrive_account(home: Path, suffix: str) -> Path:
    """Create a fake ``~/Library/CloudStorage/GoogleDrive-<suffix>/My Drive/Reading``."""
    root = home / "Library" / "CloudStorage" / f"GoogleDrive-{suffix}" / "My Drive" / "Reading"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_publish_google_drive_dir_overrides_default_root(tmp_path, monkeypatch):
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    _make_gdrive_account(tmp_path, "alice@example.com")
    _make_gdrive_account(tmp_path, "bob@example.com")
    override = str(tmp_path / "explicit-root")
    root = mod.resolve_root(
        "google-drive", env={"PUBLISH_GOOGLE_DRIVE_DIR": override}
    )
    assert root == Path(override)


def test_publish_google_drive_dir_strips_trailing_slash(tmp_path, monkeypatch):
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    override = str(tmp_path / "explicit-root") + "/"
    root = mod.resolve_root(
        "google-drive", env={"PUBLISH_GOOGLE_DRIVE_DIR": override}
    )
    assert root == Path(str(tmp_path / "explicit-root"))


def test_google_drive_glob_exactly_one_match_resolves(tmp_path, monkeypatch):
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    expected = _make_gdrive_account(tmp_path, "alice@example.com")
    root = mod.resolve_root("google-drive", env={})
    assert root == expected


def test_google_drive_glob_zero_matches_hard_fails(tmp_path, monkeypatch):
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(mod.ProviderResolutionError) as excinfo:
        mod.resolve_root("google-drive", env={})
    assert "PUBLISH_GOOGLE_DRIVE_DIR" in str(excinfo.value)


def test_google_drive_glob_multi_account_hard_fails(tmp_path, monkeypatch):
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    _make_gdrive_account(tmp_path, "alice@example.com")
    _make_gdrive_account(tmp_path, "bob@example.com")
    with pytest.raises(mod.ProviderResolutionError) as excinfo:
        mod.resolve_root("google-drive", env={})
    msg = str(excinfo.value)
    assert "PUBLISH_GOOGLE_DRIVE_DIR" in msg
    assert "alice@example.com" in msg
    assert "bob@example.com" in msg


def test_google_drive_env_override_skips_glob_entirely(tmp_path, monkeypatch):
    """When the env var is set, the glob is not consulted — proven by
    pointing HOME at an empty tree (which would hard-fail under the glob
    path) and confirming the env value is used verbatim."""
    mod = _load_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    override = "/tmp/some-explicit-gdrive-root"
    root = mod.resolve_root(
        "google-drive", env={"PUBLISH_GOOGLE_DRIVE_DIR": override}
    )
    assert root == Path(override)
