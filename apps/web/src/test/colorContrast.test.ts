import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

// Regression test for the destructive/grade-b color-contrast fix.
// Parses the actual CSS custom properties out of index.css (the source of
// truth) rather than hardcoding hex values, so any future edit to a token
// automatically gets re-checked here.

const CSS_PATH = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../index.css"
);

function hslToRgb(h: number, s: number, l: number): [number, number, number] {
  s /= 100;
  l /= 100;
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = l - c / 2;
  let rgb: [number, number, number];
  if (h < 60) rgb = [c, x, 0];
  else if (h < 120) rgb = [x, c, 0];
  else if (h < 180) rgb = [0, c, x];
  else if (h < 240) rgb = [0, x, c];
  else if (h < 300) rgb = [x, 0, c];
  else rgb = [c, 0, x];
  return [(rgb[0] + m) * 255, (rgb[1] + m) * 255, (rgb[2] + m) * 255];
}

function relLuminance([r, g, b]: [number, number, number]): number {
  const lin = (c: number) => {
    c /= 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

function contrastRatio(
  a: [number, number, number],
  b: [number, number, number]
): number {
  const l1 = relLuminance(a);
  const l2 = relLuminance(b);
  const [hi, lo] = l1 > l2 ? [l1, l2] : [l2, l1];
  return (hi + 0.05) / (lo + 0.05);
}

function mix(
  fg: [number, number, number],
  bg: [number, number, number],
  alpha: number
): [number, number, number] {
  return [
    fg[0] * alpha + bg[0] * (1 - alpha),
    fg[1] * alpha + bg[1] * (1 - alpha),
    fg[2] * alpha + bg[2] * (1 - alpha),
  ];
}

function parseHsl(token: string): [number, number, number] {
  const [h, s, l] = token
    .trim()
    .split(/\s+/)
    .map((part) => parseFloat(part.replace("%", "")));
  return hslToRgb(h, s, l);
}

/** Extracts `--name: <value>;` from a specific `:root { ... }` or `.dark { ... }` block. */
function extractBlockVars(css: string, selector: string): Record<string, string> {
  const startMarker = `${selector} {`;
  const start = css.indexOf(startMarker);
  if (start === -1) throw new Error(`Could not find CSS block for ${selector}`);
  const end = css.indexOf("}", start);
  const block = css.slice(start + startMarker.length, end);
  const vars: Record<string, string> = {};
  for (const varMatch of block.matchAll(/--([\w-]+):\s*([^;]+);/g)) {
    vars[varMatch[1]] = varMatch[2].trim();
  }
  return vars;
}

const css = readFileSync(CSS_PATH, "utf-8");
const light = extractBlockVars(css, ":root");
const dark = extractBlockVars(css, ".dark");

const WCAG_AA_TEXT = 4.5;

describe.each([
  ["light", light],
  ["dark", dark],
])("%s theme color-contrast tokens", (_themeName, vars) => {
  const card = parseHsl(vars.card);

  it("destructive-fg passes 4.5:1 on card and on its own /10 tint", () => {
    const fg = parseHsl(vars["destructive-fg"]);
    expect(contrastRatio(fg, card)).toBeGreaterThanOrEqual(WCAG_AA_TEXT);
    const tint = mix(parseHsl(vars.destructive), card, 0.1);
    expect(contrastRatio(fg, tint)).toBeGreaterThanOrEqual(WCAG_AA_TEXT);
  });

  it("grade-b-fg passes 4.5:1 on card and on its own /10 tint", () => {
    const fg = parseHsl(vars["grade-b-fg"]);
    expect(contrastRatio(fg, card)).toBeGreaterThanOrEqual(WCAG_AA_TEXT);
    const tint = mix(parseHsl(vars["grade-b"]), card, 0.1);
    expect(contrastRatio(fg, tint)).toBeGreaterThanOrEqual(WCAG_AA_TEXT);
  });

  it("destructive-foreground (white) passes 4.5:1 on the solid destructive button", () => {
    const white: [number, number, number] = [255, 255, 255];
    const solidBg = parseHsl(vars["destructive-solid"]);
    expect(contrastRatio(white, solidBg)).toBeGreaterThanOrEqual(WCAG_AA_TEXT);
  });
});
