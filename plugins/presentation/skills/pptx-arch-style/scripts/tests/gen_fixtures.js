#!/usr/bin/env node
/**
 * Regenerate every .pptx fixture used by test_lint.py.
 *
 * Why this file is committed: fixtures are deterministic, but binary .pptx
 * blobs are opaque in diffs. This script lets a reviewer rebuild every
 * fixture from source so they remain auditable.
 *
 * Layout produced:
 *   fixtures/golden.pptx                          (3 slides, fully conformant)
 *   fixtures/violators/<rule-id>.pptx             (one violation per file)
 *   fixtures/edge/<case>.pptx                     (tolerance boundaries)
 *
 * Run (from repo root):
 *   node plugins/presentation/skills/pptx-arch-style/scripts/tests/gen_fixtures.js
 *
 * Requires: pptxgenjs, jszip (both already vendored under node_modules/).
 */

"use strict";

const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const JSZip = require("jszip");

const HERE = __dirname;
const FIXTURES = path.join(HERE, "fixtures");
const VIOLATORS = path.join(FIXTURES, "violators");
const EDGE = path.join(FIXTURES, "edge");

const BRAND_RED = "F12D16";
const BADGE_GRAY = "595959";
const HIGHLIGHT_RED = "FF0000";

// ----------------------------- helpers -----------------------------

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

function makePres() {
  const p = new pptxgen();
  p.layout = "LAYOUT_16x9";
  return p;
}

function addTitleSlide(pres, { tag = "title", redBg = true, badge = false } = {}) {
  const s = pres.addSlide();
  s.background = { color: redBg ? BRAND_RED : "FFFFFF" };
  s.addNotes(`<!--arch-style:${tag}-->`);
  s.addText("Title Slide Main", {
    x: 0.8,
    y: 1.2,
    w: 8.4,
    h: 2.5,
    fontFace: "Roboto Condensed",
    fontSize: 52,
    bold: true,
    color: "F3F3F3",
    align: "left",
  });
  if (badge) addPageBadge(s, "1");
  return s;
}

function addSectionSlide(
  pres,
  { tag = "section", centered = true, redLine = false } = {}
) {
  const s = pres.addSlide();
  s.background = { color: BRAND_RED };
  s.addNotes(`<!--arch-style:${tag}-->`);
  s.addText("Section Divider", {
    x: 0.8,
    y: 2.3,
    w: 8.4,
    h: 1.0,
    fontFace: "Roboto Condensed",
    fontSize: 40.5,
    color: "EFEFEF",
    align: centered ? "center" : "left",
    valign: "middle",
  });
  if (redLine) addRedLine(s);
  return s;
}

function addPageBadge(s, num) {
  s.addShape("rect", {
    x: 0,
    y: 0,
    w: 0.496,
    h: 0.518,
    fill: { color: BADGE_GRAY },
    line: { color: BADGE_GRAY, width: 0 },
  });
  s.addText(num, {
    x: 0,
    y: 0,
    w: 0.496,
    h: 0.518,
    fontFace: "Arial",
    fontSize: 15,
    color: "FFFFFF",
    align: "center",
    valign: "middle",
  });
}

function addRedLine(s, { x = 0, y = 0.5, w = 10.0, h = 0.042, color = BRAND_RED } = {}) {
  // line: { type: "none" } emits <a:ln><a:noFill/></a:ln> so the red line does
  // not accidentally match the red-highlight-marker-border rule (which keys on
  // shape.line.color == FF0000).
  s.addShape("rect", {
    x,
    y,
    w,
    h,
    fill: { color },
    line: { type: "none" },
  });
}

function addContentTitle(s) {
  s.addText("Content Slide Title", {
    x: 0.75,
    y: 0.0,
    w: 9.234,
    h: 0.626,
    fontFace: "Arial",
    fontSize: 24,
    bold: true,
    color: "000000",
    align: "left",
  });
}

function addContentBody(s) {
  s.addText("Body text in approved font and size.", {
    x: 0.6,
    y: 0.9,
    w: 8.8,
    h: 0.5,
    fontFace: "Roboto Condensed",
    fontSize: 10.5,
    color: "000000",
    align: "left",
  });
}

function addContentSlide(pres, opts = {}) {
  const {
    tag = "content",
    pageNum = "2",
    badge = true,
    redLine = true,
    redLineCoords = { x: 0.0, y: 0.5, w: 10.0, h: 0.042 },
    redLineColor = BRAND_RED,
    bodyFontSize = 10.5,
    extraShapes = [],
  } = opts;
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addNotes(`<!--arch-style:${tag}-->`);
  if (badge) addPageBadge(s, pageNum);
  if (redLine) addRedLine(s, { ...redLineCoords, color: redLineColor });
  addContentTitle(s);
  s.addText("Body text in approved font and size.", {
    x: 0.6,
    y: 0.9,
    w: 8.8,
    h: 0.5,
    fontFace: "Roboto Condensed",
    fontSize: bodyFontSize,
    color: "000000",
    align: "left",
  });
  for (const fn of extraShapes) fn(s);
  return s;
}

// Post-process the produced .pptx zip to inject (or skip) <a:effectLst/>
// inside every <p:bgPr>. pptxgenjs does not expose this knob directly.
async function postProcessEffectLst(pptxPath, { inject = true } = {}) {
  const buf = fs.readFileSync(pptxPath);
  const zip = await JSZip.loadAsync(buf);
  const slidePaths = Object.keys(zip.files).filter((f) =>
    /^ppt\/slides\/slide\d+\.xml$/.test(f)
  );
  for (const sp of slidePaths) {
    let xml = await zip.file(sp).async("string");
    if (inject) {
      if (xml.includes("<a:effectLst/>") || xml.includes("<a:effectLst>")) continue;
      if (xml.includes("</p:bgPr>")) {
        xml = xml.replace("</p:bgPr>", "<a:effectLst/></p:bgPr>");
      } else if (xml.includes("<p:cSld>")) {
        xml = xml.replace(
          "<p:cSld>",
          "<p:cSld><p:bg><p:bgPr><a:effectLst/></p:bgPr></p:bg>"
        );
      }
      zip.file(sp, xml);
    }
    // If !inject, leave the slide as-is. pptxgenjs by default does not write
    // effectLst, so the missing-effect-override violator needs no change.
  }
  const out = await zip.generateAsync({ type: "nodebuffer" });
  fs.writeFileSync(pptxPath, out);
}

async function buildPres(pres, outPath, { effectLst = true } = {}) {
  await pres.writeFile({ fileName: outPath });
  await postProcessEffectLst(outPath, { inject: effectLst });
}

// ----------------------------- fixtures -----------------------------

async function buildGolden() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres);
  addContentSlide(pres);
  await buildPres(pres, path.join(FIXTURES, "golden.pptx"));
}

async function buildViolatorMissingPageBadge() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres);
  addContentSlide(pres, { badge: false });
  await buildPres(pres, path.join(VIOLATORS, "content-must-have-page-badge.pptx"));
}

async function buildViolatorMissingRedLine() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres);
  addContentSlide(pres, { redLine: false });
  await buildPres(pres, path.join(VIOLATORS, "content-must-have-red-line.pptx"));
}

async function buildViolatorTitleHasPageBadge() {
  const pres = makePres();
  addTitleSlide(pres, { badge: true });
  addSectionSlide(pres);
  addContentSlide(pres);
  await buildPres(pres, path.join(VIOLATORS, "title-no-page-badge.pptx"));
}

async function buildViolatorSectionHasRedLine() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres, { redLine: true });
  addContentSlide(pres);
  await buildPres(pres, path.join(VIOLATORS, "section-no-red-line.pptx"));
}

async function buildViolatorWrongRedLineCoords() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres);
  // Coords drift by 0.1in on x — well past the 0.005 tolerance — but width
  // stays >= 9.5 so the mandatory-element check still finds the line. This
  // isolates the failure to red-accent-line-coords only.
  addContentSlide(pres, { redLineCoords: { x: 0.1, y: 0.5, w: 9.8, h: 0.042 } });
  await buildPres(pres, path.join(VIOLATORS, "red-accent-line-coords.pptx"));
}

async function buildViolatorWrongRedColor() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres);
  addContentSlide(pres, { redLineColor: HIGHLIGHT_RED });
  await buildPres(pres, path.join(VIOLATORS, "brand-red-must-use-F12D16.pptx"));
}

async function buildViolatorWrongHighlightWidth() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres);
  addContentSlide(pres, {
    extraShapes: [
      (s) =>
        s.addShape("roundRect", {
          x: 3,
          y: 2,
          w: 2,
          h: 1,
          rectRadius: 0.1,
          fill: { type: "none" },
          line: { color: HIGHLIGHT_RED, width: 0.5 },
        }),
    ],
  });
  await buildPres(pres, path.join(VIOLATORS, "red-highlight-marker-border.pptx"));
}

async function buildViolatorForbiddenFontSize() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres);
  addContentSlide(pres, {
    extraShapes: [
      (s) =>
        s.addText("Off-spec size", {
          x: 0.6,
          y: 2,
          w: 4,
          h: 0.4,
          fontFace: "Arial",
          fontSize: 18,
          color: "000000",
          align: "left",
        }),
    ],
  });
  await buildPres(pres, path.join(VIOLATORS, "text-runs-use-approved-font-and-size.pptx"));
}

async function buildViolatorSectionNotCentered() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres, { centered: false });
  addContentSlide(pres);
  await buildPres(pres, path.join(VIOLATORS, "section-text-centered.pptx"));
}

async function buildViolatorMissingEffectOverride() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres);
  addContentSlide(pres);
  await buildPres(
    pres,
    path.join(VIOLATORS, "background-effectLst-override.pptx"),
    { effectLst: false }
  );
}

async function buildViolatorUntaggedSlide() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres);
  // Content slide with NO classification tag in notes.
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  // (no addNotes call)
  addPageBadge(s, "3");
  addRedLine(s);
  addContentTitle(s);
  addContentBody(s);
  await buildPres(pres, path.join(VIOLATORS, "untagged-slide.pptx"));
}

async function buildEdgeWithinTolerance() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres);
  addContentSlide(pres, {
    // 0.003 drift on every axis — under 0.005 tolerance, should pass.
    redLineCoords: { x: 0.003, y: 0.503, w: 9.997, h: 0.042 },
  });
  await buildPres(pres, path.join(EDGE, "red-line-within-tolerance.pptx"));
}

async function buildEdgeOutsideTolerance() {
  const pres = makePres();
  addTitleSlide(pres);
  addSectionSlide(pres);
  addContentSlide(pres, {
    // 0.010 drift on x — over 0.005 tolerance, should fail.
    redLineCoords: { x: 0.01, y: 0.5, w: 10.0, h: 0.042 },
  });
  await buildPres(pres, path.join(EDGE, "red-line-outside-tolerance.pptx"));
}

// ----------------------------- main -----------------------------

async function main() {
  ensureDir(FIXTURES);
  ensureDir(VIOLATORS);
  ensureDir(EDGE);

  const tasks = [
    ["golden.pptx", buildGolden],
    ["violators/content-must-have-page-badge.pptx", buildViolatorMissingPageBadge],
    ["violators/content-must-have-red-line.pptx", buildViolatorMissingRedLine],
    ["violators/title-no-page-badge.pptx", buildViolatorTitleHasPageBadge],
    ["violators/section-no-red-line.pptx", buildViolatorSectionHasRedLine],
    ["violators/red-accent-line-coords.pptx", buildViolatorWrongRedLineCoords],
    ["violators/brand-red-must-use-F12D16.pptx", buildViolatorWrongRedColor],
    ["violators/red-highlight-marker-border.pptx", buildViolatorWrongHighlightWidth],
    [
      "violators/text-runs-use-approved-font-and-size.pptx",
      buildViolatorForbiddenFontSize,
    ],
    ["violators/section-text-centered.pptx", buildViolatorSectionNotCentered],
    [
      "violators/background-effectLst-override.pptx",
      buildViolatorMissingEffectOverride,
    ],
    ["violators/untagged-slide.pptx", buildViolatorUntaggedSlide],
    ["edge/red-line-within-tolerance.pptx", buildEdgeWithinTolerance],
    ["edge/red-line-outside-tolerance.pptx", buildEdgeOutsideTolerance],
  ];

  for (const [label, fn] of tasks) {
    process.stdout.write(`generating ${label} ... `);
    await fn();
    process.stdout.write("ok\n");
  }
  console.log(`\nFixtures written under ${FIXTURES}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
