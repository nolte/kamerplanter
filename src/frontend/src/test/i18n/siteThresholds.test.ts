import { describe, it, expect } from 'vitest';
import type { Orientation } from '@/api/types';
import { deFull as de, enFull as en } from '../i18nTestResources';

/**
 * REQ-053 WP 8.24 (#2667) — the eight compass orientations, the sun-tile help texts and the site threshold
 * section exist in DE **and** EN with the same keys.
 *
 * The orientation list is a `Record<Orientation, true>`: a value added to the union without an entry here
 * (or an entry the union does not have) is a compile error, so the list cannot drift from the type.
 */
const ORIENTATIONS: Record<Orientation, true> = {
  north: true,
  northeast: true,
  east: true,
  southeast: true,
  south: true,
  southwest: true,
  west: true,
  northwest: true,
};

function at(locale: unknown, path: string[]): unknown {
  return path.reduce<unknown>((node, key) => (node as Record<string, unknown> | undefined)?.[key], locale);
}

function nonEmptyString(value: unknown): boolean {
  return typeof value === 'string' && value.trim().length > 0;
}

function keysOf(value: unknown): string[] {
  return Object.keys((value as Record<string, unknown>) ?? {}).sort();
}

describe('orientation and site threshold i18n parity (REQ-053 WP 8.24)', () => {
  it('has eight orientations', () => {
    expect(Object.keys(ORIENTATIONS)).toHaveLength(8);
  });

  it.each(Object.keys(ORIENTATIONS))('labels the orientation "%s" in DE and EN', (value) => {
    expect(nonEmptyString(at(de, ['enums', 'orientation', value]))).toBe(true);
    expect(nonEmptyString(at(en, ['enums', 'orientation', value]))).toBe(true);
  });

  it('carries the same threshold keys in DE and EN, none empty', () => {
    const path = ['pages', 'sites', 'thresholds'];
    expect(keysOf(at(de, path))).toEqual(keysOf(at(en, path)));
    for (const key of keysOf(at(de, path))) {
      expect(nonEmptyString(at(de, [...path, key]))).toBe(true);
      expect(nonEmptyString(at(en, [...path, key]))).toBe(true);
    }
  });

  it('carries the same sun-tile keys in DE and EN, with the bound as a value, not a fixed number', () => {
    const path = ['pages', 'gardenPlan', 'sun', 'options'];
    for (const option of keysOf(at(de, path))) {
      expect(keysOf(at(de, [...path, option]))).toEqual(keysOf(at(en, [...path, option])));
    }
    for (const locale of [de, en]) {
      expect(at(locale, [...path, 'full_sun', 'help_other'])).toMatch(/\{\{count, number\}\}.*\{\{date\}\}/);
      expect(at(locale, [...path, 'partial_shade', 'help'])).toMatch(/\{\{from, number\}\}.*\{\{to, number\}\}/);
      expect(at(locale, [...path, 'deep_shade', 'help_other'])).toMatch(/\{\{count, number\}\}/);
    }
  });
});
