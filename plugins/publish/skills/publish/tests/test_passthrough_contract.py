"""Regression guard for the publish skill's passthrough contract (TASK-40).

The publish skill must accept ready-made artifacts (``.pdf``, ``.pptx``,
``.key``, ``.docx``) and copy them verbatim into the provider's per-project
``Reading/<project>`` subfolder — no PDF conversion — while markdown is still
rendered to PDF via the ``pdf`` skill. These assertions pin that contract to
the skill docs so a future edit that silently reinstates the markdown-only
hard-fail, or routes an artifact through the renderer, fails the suite.

The contract is guarded in the docs, NOT by adding logic to ``providers.py``:
transport and the resolver are explicitly out of scope for this task.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
SKILL_MD = HERE.parent / "SKILL.md"
PROVIDERS_MD = HERE.parent / "references" / "providers.md"
PROVIDERS_PY = HERE.parent / "scripts" / "providers.py"
PUBLISH_DIR = HERE.parents[2]
PLUGIN_JSON = PUBLISH_DIR / ".claude-plugin" / "plugin.json"
README_MD = HERE.parents[4] / "README.md"

ARTIFACT_ALLOWLIST = (".pdf", ".pptx", ".key", ".docx")

# The mount-only uploader name is assembled from parts so this guard file adds
# no literal occurrence of it under plugins/publish (AC#5), and so the scan
# below never flags itself. The scan also skips the tests directory.
_UPLOADER = "rcl" + "one"
UPLOADER_COMMANDS = (
    f"{_UPLOADER} copy",
    f"{_UPLOADER} sync",
    f"{_UPLOADER} move",
    f"{_UPLOADER} upload",
    f"{_UPLOADER} mount",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_skill_md_no_longer_hard_fails_on_non_md() -> None:
    text = _read(SKILL_MD)
    assert "Hard-fail if the extension is not `.md`" not in text
    assert "No non-`.md` input" not in text


def test_skill_md_declares_passthrough_allowlist() -> None:
    text = _read(SKILL_MD).lower()
    assert "passthrough" in text
    for ext in ARTIFACT_ALLOWLIST:
        assert ext in text, f"allowlist extension {ext} missing from SKILL.md"


def test_skill_md_passthrough_copies_verbatim() -> None:
    text = _read(SKILL_MD)
    assert "cp " in text, "passthrough must copy via cp"
    assert "verbatim" in text.lower()


def test_skill_md_render_branch_still_uses_md_to_pdf() -> None:
    assert "md-to-pdf.py" in _read(SKILL_MD)


def test_plugin_json_version_bumped_and_describes_passthrough() -> None:
    data = json.loads(_read(PLUGIN_JSON))
    major, minor = (int(part) for part in data["version"].split(".")[:2])
    assert (major, minor) >= (1, 4), f"expected >=1.4.0, got {data['version']}"
    desc = data["description"].lower()
    assert "passthrough" in desc
    assert "copied verbatim" in desc


def test_skill_description_states_render_and_passthrough() -> None:
    text = _read(SKILL_MD).lower()
    assert "rendered to pdf" in text
    assert "copied verbatim" in text
    assert "passthrough" in text


def test_readme_publish_section_states_render_and_passthrough() -> None:
    text = _read(README_MD).lower()
    assert "rendered to pdf" in text
    assert "copied as-is" in text
    assert "passthrough" in text


def test_providers_md_documents_passthrough_layout() -> None:
    text = _read(PROVIDERS_MD)
    assert "passthrough" in text.lower()
    assert "<original-name>" in text
    # The render layout line must remain for the .md branch.
    assert "<slug>.pdf" in text


def test_passthrough_logic_not_added_to_providers_py() -> None:
    """The contract lives in the docs, not the resolver (AC#6)."""
    text = _read(PROVIDERS_PY).lower()
    assert "passthrough" not in text
    for ext in ARTIFACT_ALLOWLIST:
        assert ext not in text, f"{ext} leaked into providers.py resolver logic"


def test_no_headless_uploader_command_added() -> None:
    """AC#5: no headless uploader invocation anywhere under plugins/publish.

    The bare-word mount-only exclusion prose in the reference docs is allowed;
    an actual uploader *command* is not. The tests dir is skipped so this
    file's own command table is not scanned.
    """
    for path in PUBLISH_DIR.rglob("*"):
        if not path.is_file() or HERE in path.parents:
            continue
        if path.suffix not in {".md", ".py", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for cmd in UPLOADER_COMMANDS:
            assert cmd not in text, f"{cmd!r} found in {path}"
