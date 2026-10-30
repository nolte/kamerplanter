/**
 * The editor texts (REQ-053, #2536): the refusals the editor can show name a text in DE and EN, and the two locales
 * carry the same keys below `pages.gardenPlan`.
 */
import { describe, expect, it } from 'vitest';
import { deFull as de, enFull as en } from '@/test/i18nTestResources';

const PLAN = ['pages', 'gardenPlan'];
const NOTICE = [...PLAN, 'editor', 'notice'];

function at(locale: unknown, path: readonly string[]): unknown {
  return path.reduce<unknown>((node, key) => (node as Record<string, unknown> | undefined)?.[key], locale);
}

function leaves(node: unknown, prefix = ''): string[] {
  if (typeof node !== 'object' || node === null) return [prefix];
  return Object.entries(node).flatMap(([key, value]) => leaves(value, prefix === '' ? key : `${prefix}.${key}`));
}

describe('garden plan editor texts', () => {
  it.each([['distribute.overlap'], ['distribute.locked_covered']])(
    'names a DE and an EN text for the refusal %s',
    (code) => {
      expect(typeof at(de, [...NOTICE, ...code.split('.')])).toBe('string');
      expect(typeof at(en, [...NOTICE, ...code.split('.')])).toBe('string');
    },
  );

  it('carries the same keys in DE and EN', () => {
    const deLeaves = leaves(at(de, PLAN));
    // a subtree missing in BOTH locales would compare equal: the namespace holds about 1000 texts, so a short
    // list means the comparison ran on nothing (a missing `pages.gardenPlan` yields one empty leaf each)
    expect(deLeaves.length).toBeGreaterThan(900);
    expect(deLeaves.sort()).toEqual(leaves(at(en, PLAN)).sort());
  });
});
