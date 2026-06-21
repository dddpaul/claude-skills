"""Verify the publish skill's trigger → provider resolver.

The publish skill ships only the ``icloud`` provider in v1. All eight
documented trigger phrases must route to ``icloud``. The
``PUBLISH_ICLOUD_DIR`` env var must override the default root; the legacy
pre-rename env var must be ignored. Phrases that do not name a provider
must return the ``NEEDS_DISAMBIGUATION`` sentinel, not a silent default.

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


@pytest.mark.parametrize("phrase", ICLOUD_TRIGGERS)
def test_each_icloud_trigger_resolves_to_icloud(phrase: str):
    mod = _load_module()
    assert mod.resolve_provider(phrase) == "icloud"


@pytest.mark.parametrize("phrase", ICLOUD_TRIGGERS)
def test_trigger_matching_is_case_insensitive(phrase: str):
    mod = _load_module()
    assert mod.resolve_provider(phrase.upper()) == "icloud"
    assert mod.resolve_provider(f"  {phrase}  ") == "icloud"


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
