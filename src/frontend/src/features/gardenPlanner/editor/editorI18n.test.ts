/**
 * The editor texts (REQ-053, #2536): the refusals the editor can show name a text in DE and EN, and the two locales
 * carry the same keys below `pages.gardenPlan`.
 */
import { describe, expect, it } from 'vitest';
import { deFull as de, enFull as en } from '@/test/i18nTestResources';
import { COMPANION_STATUSES } from '../renderer/companionLines';
import { TOGGLE_LAYERS } from './layers';

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

  it.each(TOGGLE_LAYERS)('names a DE and an EN label and hint for the layer toggle %s', (layer) => {
    for (const locale of [de, en]) {
      expect(typeof at(locale, [...PLAN, 'editor', 'zones', 'layers', layer])).toBe('string');
      expect(typeof at(locale, [...PLAN, 'editor', 'zones', 'layers', `${layer}Hint`])).toBe('string');
    }
  });

  it.each(COMPANION_STATUSES)('words the companion status %s in the info card and the legend, DE and EN', (status) => {
    for (const locale of [de, en]) {
      expect(typeof at(locale, [...PLAN, 'editor', 'companion', 'status', status])).toBe('string');
      expect(typeof at(locale, [...PLAN, 'editor', 'companion', 'reasonCode', status])).toBe('string');
      expect(typeof at(locale, [...PLAN, 'editor', 'zones', 'legend', 'companion', status])).toBe('string');
    }
  });

  it('words the measure tool (GP-UX-071) in DE and EN: rail label, verb tooltip, short text, status, touch "clear"', () => {
    const paths = [
      ['tools', 'measure', 'label'],
      ['tools', 'measure', 'hint'],
      ['tools', 'measure', 'short'],
      ['measure', 'clear'],
      ['measure', 'total'],
      ['touch', 'clear'],
      ...['pointer', 'touch'].flatMap((mode) =>
        ['start', 'first', 'open_one', 'open_other', 'done_one', 'done_other'].map((key) => ['measure', 'status', mode, key]),
      ),
    ];
    for (const locale of [de, en]) {
      for (const path of paths) expect(typeof at(locale, [...PLAN, 'editor', ...path]), path.join('.')).toBe('string');
    }
    // The tooltip names the verb (GP-UX-010).
    expect(at(de, [...PLAN, 'editor', 'tools', 'measure', 'hint'])).toMatch(/^Abstand messen/);
    expect(at(en, [...PLAN, 'editor', 'tools', 'measure', 'hint'])).toMatch(/^Measure a distance/);
  });

  it('carries the same keys in DE and EN', () => {
    const deLeaves = leaves(at(de, PLAN));
    // a subtree missing in BOTH locales would compare equal: the namespace holds about 1000 texts, so a short
    // list means the comparison ran on nothing (a missing `pages.gardenPlan` yields one empty leaf each)
    expect(deLeaves.length).toBeGreaterThan(900);
    expect(deLeaves.sort()).toEqual(leaves(at(en, PLAN)).sort());
  });
});
