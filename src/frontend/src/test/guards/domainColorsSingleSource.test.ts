import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import type { CalendarEventCategory } from '@/api/types';
import { METRIC_COLOR_KEYS, PHASE_COLOR_KEYS, phaseColorKey } from '@/theme/domainColors';

/**
 * #3021 (frontend audit 2026-11, M7; UI-NFR-016 R-006/R-008, UI-NFR-006): growth-phase, sensor-metric and
 * calendar-category colours have ONE source, `src/theme/domainColors.ts`, surfaced as `theme.palette.phase` /
 * `.metric` / `.eventCategory` with light and dark values. The phase map had been declared seven times with four
 * conflicting palettes — `germination` alone had four values.
 *
 * This guard reads every production source outside `src/theme/` and fails on a domain key mapped to a colour
 * literal (`vegetative: '#43A047'`, `ph: "rgb(…)"`, `harvest: { light: '#…' }`) or on a declaration named like
 * one of the old maps (`PHASE_COLORS`, `METRIC_COLORS`, `CATEGORY_COLORS`). The key set is read from the token
 * module itself, so a phase added there is guarded here without touching this file.
 */

const SRC = path.resolve(__dirname, '../..');
const THEME_DIR = path.join(SRC, 'theme');

const CATEGORY_KEYS: readonly CalendarEventCategory[] = [
  'training',
  'pruning',
  'transplanting',
  'feeding',
  'ipm',
  'harvest',
  'maintenance',
  'phase_transition',
  'tank_maintenance',
  'watering_forecast',
  'custom',
];

/** Keys that are colour tokens. A key the phase resolver knows (aliases included) counts as a phase key. */
function isDomainKey(key: string): boolean {
  return (
    phaseColorKey(key) !== undefined ||
    (METRIC_COLOR_KEYS as readonly string[]).includes(key) ||
    (CATEGORY_KEYS as readonly string[]).includes(key)
  );
}

const COLOUR_LITERAL = String.raw`(?:#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\()`;
/** `key: '<colour>'` or `key: { light: '<colour>' …` — the key quoted or bare. */
const KEYED_COLOUR = new RegExp(
  String.raw`(?:^|[\s{,])['"]?([a-z][a-z0-9_]*)['"]?\s*:\s*(?:\{[^}\n]*?)?['"\x60]${COLOUR_LITERAL}`,
  'g',
);
const MAP_DECLARATION = /\b(?:const|let|var)\s+(PHASE_COLOU?RS?|METRIC_COLOU?RS?|CATEGORY_COLOU?RS?)\b/g;

function isProductionSource(file: string): boolean {
  return /\.(ts|tsx)$/.test(file) && !/\.(test|spec)\.tsx?$/.test(file) && !file.endsWith('.d.ts');
}

function sourceFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (full === THEME_DIR || full === path.join(SRC, 'test')) continue;
      out.push(...sourceFiles(full));
    } else if (isProductionSource(full)) {
      out.push(full);
    }
  }
  return out;
}

/** Every redeclared domain colour in `code`, as `line: snippet`. */
function findRedeclarations(code: string): string[] {
  const hits: string[] = [];
  code.split('\n').forEach((line, index) => {
    if (/^\s*(\/\/|\*)/.test(line)) return;
    for (const match of line.matchAll(KEYED_COLOUR)) {
      if (isDomainKey(match[1])) hits.push(`${index + 1}: ${line.trim()}`);
    }
    for (const match of line.matchAll(MAP_DECLARATION)) {
      hits.push(`${index + 1}: declares ${match[1]}`);
    }
  });
  return hits;
}

describe('domain colours have a single source (#3021)', () => {
  it('reads a non-trivial set of files and keys', () => {
    expect(sourceFiles(SRC).length).toBeGreaterThan(200);
    expect(PHASE_COLOR_KEYS.length).toBeGreaterThan(10);
  });

  it('no production source outside src/theme/ redeclares a phase, metric or category colour', () => {
    const offenders: string[] = [];
    for (const file of sourceFiles(SRC)) {
      const hits = findRedeclarations(readFileSync(file, 'utf8'));
      for (const hit of hits) offenders.push(`${path.relative(SRC, file)}:${hit}`);
    }
    expect(offenders).toEqual([]);
  });

  describe('the detector', () => {
    it.each([
      ['a bare phase key', "const MAP = {\n  germination: '#81C784',\n};"],
      ['a quoted alias key', "const m = { 'fruiting': \"#ffcc80\" };"],
      ['a metric key with rgb()', 'const m = { ph: `rgb(1, 2, 3)` };'],
      ['a category key', "const m = { ipm: '#FF9800' };"],
      ['a light/dark pair', "const m = { flowering: { light: '#AB47BC', dark: '#BA68C8' } };"],
      ['an old map name', 'const PHASE_COLORS: Record<string, string> = {};'],
      ['a renamed CATEGORY_COLORS', 'let CATEGORY_COLORS = {};'],
    ])('flags %s', (_name, code) => {
      expect(findRedeclarations(code)).not.toEqual([]);
    });

    it.each([
      ['a theme lookup', "const c = getPhaseColor(theme, 'germination');"],
      ['a non-domain key', "const m = { primary: '#2e7d32' };"],
      ['a phase key mapped to a non-colour', "const m = { germination: 'pages.phase.germination' };"],
      ['a comment', "// germination: '#81C784' used to live here"],
      ['a palette path', "sx={{ color: 'text.secondary' }}"],
    ])('accepts %s', (_name, code) => {
      expect(findRedeclarations(code)).toEqual([]);
    });
  });
});
