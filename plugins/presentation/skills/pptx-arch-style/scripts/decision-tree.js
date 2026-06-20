// decision-tree.js — pptx-arch-style decision-tree helper (Path B).
//
// Single public function: drawDecisionTree(slide, spec). Renders diamonds,
// terminals, and direction-aware orthogonal connectors per the canonical
// "Decision Tree Diagrams" section of SKILL.md. Coordinates are inches and
// must lie inside the content area (Y0=1.10, YE=5.10 per v0.7.0 anatomy).
//
// Direction semantics: every connector takes explicit (from, to) coordinates;
// arrowheads always land at the SEMANTIC `to` end. Helpers detect the flip
// (to < from) and place `beginArrowType` vs `endArrowType` accordingly, so
// callers never have to think about coordinate order vs visual arrow side.
//
// No pptxgenjs import — the helper calls slide.addText / slide.addShape on
// whatever object the caller passes in, so it works with any pptxgenjs
// Slide instance.

'use strict';

const GRAY = '595959';
const YELLOW_FILL = 'FFF2CC';
const YELLOW_BORDER = 'D6B656';
const BLUE_FILL = 'DAEAF5';
const BLUE_BORDER = '9CC3E5';
const GREEN_FILL = 'D9EAD3';
const GREEN_BORDER = '82B366';
const RED_FILL = 'FFE0E0';
const RED_BORDER = 'C0392B';

const DIAMOND = { w: 2.20, h: 0.90 };
const TERMINAL = { w: 1.80, h: 0.55 };

const TERMINAL_PALETTE = {
  blue: { fill: BLUE_FILL, border: BLUE_BORDER },
  green: { fill: GREEN_FILL, border: GREEN_BORDER },
  red: { fill: RED_FILL, border: RED_BORDER },
};

function drawDiamond(slide, { x, y, text, w, h }) {
  slide.addText(text, {
    shape: 'diamond',
    x,
    y,
    w: w || DIAMOND.w,
    h: h || DIAMOND.h,
    fill: { color: YELLOW_FILL },
    line: { color: YELLOW_BORDER, width: 1 },
    fontFace: 'Arial',
    fontSize: 9,
    bold: true,
    color: '000000',
    align: 'center',
    valign: 'middle',
    margin: 0,
  });
}

function drawTerminal(slide, { x, y, text, color, w, h }) {
  const palette = TERMINAL_PALETTE[color || 'blue'];
  if (!palette) {
    throw new Error(
      `decision-tree.js: unknown terminal color '${color}'. Expected one of: ${Object.keys(TERMINAL_PALETTE).join(', ')}.`,
    );
  }
  slide.addText(text, {
    shape: 'roundRect',
    x,
    y,
    w: w || TERMINAL.w,
    h: h || TERMINAL.h,
    rectRadius: 0.06,
    fill: { color: palette.fill },
    line: { color: palette.border, width: 1 },
    fontFace: 'Arial',
    fontSize: 9,
    bold: true,
    color: '000000',
    align: 'center',
    valign: 'middle',
    margin: 0,
  });
}

function drawLabel(slide, { x, y, text, w, h }) {
  slide.addText(text, {
    x,
    y,
    w: w || 0.40,
    h: h || 0.20,
    fontFace: 'Arial',
    fontSize: 9,
    color: '666666',
    align: 'left',
    valign: 'middle',
  });
}

function buildLineOpts(withArrow, flipped) {
  const opts = { color: GRAY, width: 1 };
  if (withArrow) {
    opts[flipped ? 'beginArrowType' : 'endArrowType'] = 'triangle';
  }
  return opts;
}

function drawVLine(slide, { x, fromY, toY, withArrow }) {
  if (fromY === toY) {
    throw new Error(
      `decision-tree.js: vertical connector has fromY===toY (${fromY}); zero-length LINE is meaningless.`,
    );
  }
  const flipped = toY < fromY;
  slide.addShape('line', {
    x,
    y: Math.min(fromY, toY),
    w: 0,
    h: Math.abs(toY - fromY),
    line: buildLineOpts(withArrow, flipped),
  });
}

function drawHLine(slide, { fromX, toX, y, withArrow }) {
  if (fromX === toX) {
    throw new Error(
      `decision-tree.js: horizontal connector has fromX===toX (${fromX}); zero-length LINE is meaningless.`,
    );
  }
  const flipped = toX < fromX;
  slide.addShape('line', {
    x: Math.min(fromX, toX),
    y,
    w: Math.abs(toX - fromX),
    h: 0,
    line: buildLineOpts(withArrow, flipped),
  });
}

function drawConnector(slide, connector) {
  if (connector.kind === 'v') {
    drawVLine(slide, connector);
  } else if (connector.kind === 'h') {
    drawHLine(slide, connector);
  } else {
    throw new Error(
      `decision-tree.js: connector.kind must be 'v' or 'h', got '${connector.kind}'.`,
    );
  }
  if (connector.label) {
    drawLabel(slide, connector.label);
  }
}

function drawDecisionTree(slide, spec) {
  if (!slide || typeof slide.addText !== 'function' || typeof slide.addShape !== 'function') {
    throw new Error(
      'decision-tree.js: first argument must be a pptxgenjs Slide (addText/addShape required).',
    );
  }
  if (!spec || typeof spec !== 'object') {
    throw new Error('decision-tree.js: spec must be an object.');
  }
  const { diamonds = [], terminals = [], connectors = [], labels = [] } = spec;

  for (const d of diamonds) drawDiamond(slide, d);
  for (const t of terminals) drawTerminal(slide, t);
  for (const c of connectors) drawConnector(slide, c);
  for (const l of labels) drawLabel(slide, l);
}

module.exports = {
  drawDecisionTree,
  drawDiamond,
  drawTerminal,
  drawVLine,
  drawHLine,
  drawLabel,
};
