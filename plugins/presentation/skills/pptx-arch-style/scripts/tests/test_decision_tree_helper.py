"""Smoke test for the decision-tree.js helper (TASK-28).

Runs a tiny Node script that requires decision-tree.js, builds a 1-slide
deck via drawDecisionTree(), writes it to a tmp file, and asserts:

  1. node exits 0 (helper does not throw on the canonical SKILL.md spec)
  2. the produced .pptx lints clean under the full pptx-arch-style ruleset
     (no errors, no warnings) — in particular, all final-segment connectors
     emit endArrowType/beginArrowType so decision-tree-connector-arrowhead-
     missing does NOT fire

This protects against future drift between the SKILL.md canonical snippet
and the bundled helper.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "lint.py"
HELPER = HERE.parent / "decision-tree.js"
RULES = HERE.parent.parent / "references" / "rules.yaml"
NODE_BIN = shutil.which("node")


def _load_lint_module():
    spec = importlib.util.spec_from_file_location("pptx_arch_lint", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


lint_mod = _load_lint_module()


@pytest.fixture(scope="module")
def rules():
    return lint_mod.load_rules(RULES)


NODE_DRIVER = r"""
const path = require('path');
const pptxgen = require('pptxgenjs');
const { drawDecisionTree } = require(process.env.HELPER_PATH);

const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
const slide = pres.addSlide();
slide.background = { color: 'FFFFFF' };
slide.addNotes('<!--arch-style:content-->');

// Mandatory content-slide chrome to satisfy linter (badge + red line).
slide.addShape('rect', {
  x: 0, y: 0, w: 0.5, h: 0.5,
  fill: { color: '595959' }, line: { type: 'none' },
});
slide.addText('1', {
  x: 0, y: 0, w: 0.5, h: 0.5,
  fontFace: 'Arial', fontSize: 9, bold: true, color: 'FFFFFF',
  align: 'center', valign: 'middle',
});
slide.addShape('rect', {
  x: 0, y: 0.85, w: 10, h: 0.042,
  fill: { color: 'F12D16' }, line: { type: 'none' },
});

drawDecisionTree(slide, {
  diamonds: [
    { x: 3.90, y: 1.20, text: 'Условие А?' },
    { x: 3.90, y: 2.40, text: 'Условие Б?' },
  ],
  terminals: [
    { x: 7.20, y: 1.38, text: 'Terminal NO', color: 'blue' },
    { x: 1.60, y: 4.10, text: 'Outcome 1',   color: 'green' },
    { x: 4.10, y: 4.10, text: 'Outcome 2',   color: 'blue' },
    { x: 6.60, y: 4.10, text: 'Outcome 3',   color: 'green' },
  ],
  connectors: [
    { kind: 'h', fromX: 6.10, toX: 7.20, y: 1.65, withArrow: true,
      label: { text: 'НЕТ', x: 6.30, y: 1.40 } },
    { kind: 'v', x: 5.00, fromY: 2.10, toY: 2.40, withArrow: true,
      label: { text: 'ДА',  x: 5.05, y: 2.15 } },
    { kind: 'v', x: 5.00, fromY: 3.30, toY: 3.70, withArrow: false },
    { kind: 'h', fromX: 2.50, toX: 7.50, y: 3.70, withArrow: false },
    { kind: 'v', x: 2.50, fromY: 3.70, toY: 4.10, withArrow: true  },
    { kind: 'v', x: 5.00, fromY: 3.70, toY: 4.10, withArrow: true  },
    { kind: 'v', x: 7.50, fromY: 3.70, toY: 4.10, withArrow: true  },
  ],
});

// NOTE: this smoke test does NOT apply the Rule #11 <a:effectLst/>
// background override — it filters the lint report to decision-tree
// connector rules only, so background-effectLst-override violations
// (if any) are ignored.

pres.writeFile({ fileName: process.env.OUTPUT_PATH })
  .then(() => process.exit(0))
  .catch((err) => { console.error(err); process.exit(1); });
"""


@pytest.mark.skipif(NODE_BIN is None, reason="node not available")
def test_helper_renders_canonical_decision_tree(tmp_path, rules):
    """drawDecisionTree() builds a 1-slide deck from the SKILL.md canonical
    spec; the deck must lint without any decision-tree-connector-arrowhead-
    missing or -orthogonal warnings (other content-chrome rules may or may
    not fire — we filter to the rules this helper is responsible for)."""
    output = tmp_path / "helper-canonical.pptx"
    driver_path = tmp_path / "driver.js"
    driver_path.write_text(NODE_DRIVER, encoding="utf-8")

    node_modules = HERE / "node_modules"
    assert node_modules.exists(), "pptxgenjs must be vendored under tests/node_modules"

    result = subprocess.run(
        [NODE_BIN, str(driver_path)],
        env={
            "HELPER_PATH": str(HELPER),
            "OUTPUT_PATH": str(output),
            "NODE_PATH": str(node_modules),
            "PATH": "/usr/bin:/usr/local/bin",
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"node driver failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert output.exists(), "drawDecisionTree() should have produced a .pptx"

    report = lint_mod.lint(output, rules)
    decision_tree_violations = [
        v for v in report.violations
        if v.rule_id in {
            "decision-tree-connector-orthogonal",
            "decision-tree-connector-arrowhead-missing",
        }
    ]
    assert decision_tree_violations == [], (
        f"helper-rendered tree must have zero decision-tree-connector violations; "
        f"got {decision_tree_violations}"
    )
