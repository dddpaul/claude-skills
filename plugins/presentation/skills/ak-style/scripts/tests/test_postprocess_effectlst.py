"""Tests for the ``<a:effectLst/>`` post-processing script.

Loads the script as a module (it ships with a PEP 723 shebang for direct
execution) so we can call ``postprocess()`` and ``ensure_effectlst()`` without
shelling out. The ``background-effectLst-override.pptx`` violator fixture is
the canonical input — a deck whose ``<p:bgPr>`` blocks lack the override.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "postprocess-effectlst.py"
LINT_SCRIPT = HERE.parent / "lint.py"
FIXTURES = HERE / "fixtures"
RULES = HERE.parent.parent / "references" / "rules.yaml"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


postprocess_mod = _load("postprocess_effectlst", SCRIPT)
lint_mod = _load("pptx_arch_lint", LINT_SCRIPT)


@pytest.fixture
def violator_copy(tmp_path):
    src = FIXTURES / "violators" / "background-effectLst-override.pptx"
    dst = tmp_path / "deck.pptx"
    shutil.copy(src, dst)
    return dst


def test_postprocess_makes_linter_pass(violator_copy):
    rules = lint_mod.load_rules(RULES)
    before = lint_mod.lint(violator_copy, rules)
    assert "background-effectLst-override" in {v.rule_id for v in before.violations}, (
        "fixture should violate the effectLst rule before patching"
    )

    rc = postprocess_mod.postprocess(violator_copy)
    assert rc == 0

    after = lint_mod.lint(violator_copy, rules)
    assert "background-effectLst-override" not in {v.rule_id for v in after.violations}, (
        f"effectLst rule should pass after postprocess; got {after.violations}"
    )


def test_postprocess_is_idempotent(violator_copy):
    rc1 = postprocess_mod.postprocess(violator_copy)
    rc2 = postprocess_mod.postprocess(violator_copy)
    assert rc1 == 0 and rc2 == 0

    rules = lint_mod.load_rules(RULES)
    report = lint_mod.lint(violator_copy, rules)
    assert "background-effectLst-override" not in {v.rule_id for v in report.violations}


def test_postprocess_reports_missing_bg(tmp_path):
    src = FIXTURES / "golden.pptx"
    dst = tmp_path / "golden.pptx"
    shutil.copy(src, dst)
    rc = postprocess_mod.postprocess(dst)
    assert rc in (0, 1), "golden may either already carry overrides or have no bgPr"


def test_cli_handles_missing_file(tmp_path):
    rc = postprocess_mod.main([str(tmp_path / "does-not-exist.pptx")])
    assert rc == 1
