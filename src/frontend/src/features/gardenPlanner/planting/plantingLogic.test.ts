/**
 * Rules of the planting dialog (REQ-053 WP 3.6): the prefill order of GP-FR-061, the validation of an
 * entry, the alternating rows of GP-FR-070, the yellow ring of GP-FR-072, the pot check of W-016.5 and
 * the names the run is created with.
 */
import { describe, expect, it } from 'vitest';
import { computeLayout } from '../model/layout';
import {
  alternatingRows,
  canAlternate,
  containerCheck,
  emptyEntry,
  idPrefixOf,
  needsOverrideReason,
  parseLowerBound,
  prefillFor,
  requestedCount,
  slotIdPrefixOf,
  toEntryLayout,
  toPreviewEntry,
  tooClosePoints,
  validateEntry,
  worstSeverity,
} from './plantingLogic';
import { BED_GEOMETRY, species } from './plantingTestKit';

describe('parseLowerBound', () => {
  it.each([
    ['60', 60],
    ['60-80', 60],
    ['25 – 30', 25],
    ['7,5', 7.5],
    [' 12.5--20', 12.5],
    [40, 40],
  ])('takes the lower bound of %s', (input, expected) => {
    expect(parseLowerBound(input)).toBe(expected);
  });

  it.each([null, undefined, '', 'abc', '0', 0, -3, Number.NaN])('has no value for %s', (input) => {
    expect(parseLowerBound(input as never)).toBeNull();
  });
});

describe('prefillFor (GP-FR-061, F-11)', () => {
  const tomato = species('sp_t', 'Tomato', { spacing_cm: '50-60', row_spacing_cm: '80' });

  it('takes the Steckbrief first, even when the tenant used another value last', () => {
    const prefill = prefillFor(tomato, { spacing_cm: 45, row_spacing_cm: 70, layout_strategy: 'rows' });
    expect(prefill).toMatchObject({
      spacing: '50',
      rowSpacing: '80',
      spacingSource: 'species',
      rowSpacingSource: 'species',
      layout: 'rows',
    });
  });

  it('falls back to what the tenant used last, field by field', () => {
    const noRow = species('sp_b', 'Bean', { spacing_cm: '10', row_spacing_cm: null });
    const prefill = prefillFor(noRow, { spacing_cm: 99, row_spacing_cm: 40 });
    expect(prefill).toMatchObject({
      spacing: '10',
      spacingSource: 'species',
      rowSpacing: '40',
      rowSpacingSource: 'lastUsed',
    });
  });

  it('stays empty - no silent default - when neither source has a value', () => {
    const bare = species('sp_x', 'Unknown');
    expect(prefillFor(bare, null)).toMatchObject({
      spacing: '',
      rowSpacing: '',
      spacingSource: 'none',
      rowSpacingSource: 'none',
      layout: null,
    });
  });
});

describe('validateEntry', () => {
  const valid = { ...emptyEntry('e1'), speciesKey: 'sp_t', spacing: '40' };

  it('accepts a species with a spacing', () => {
    expect(validateEntry(valid)).toEqual({});
  });

  it('asks for the species and the spacing', () => {
    expect(validateEntry(emptyEntry('e1'))).toEqual({
      species: 'speciesRequired',
      spacing: 'spacingRequired',
    });
  });

  it.each([['4'], ['1501']])('refuses a spacing of %s cm (5..1500)', (spacing) => {
    expect(validateEntry({ ...valid, spacing }).spacing).toBe('spacingRange');
  });

  it('needs a row spacing for rows only', () => {
    expect(validateEntry({ ...valid, layout: 'rows' }).rowSpacing).toBe('rowSpacingRequired');
    expect(validateEntry({ ...valid, layout: 'rows', rowSpacing: '3' }).rowSpacing).toBe('rowSpacingRange');
    expect(validateEntry({ ...valid, layout: 'triangular' }).rowSpacing).toBeUndefined();
  });

  it('wants a whole number when the count is fixed', () => {
    expect(validateEntry({ ...valid, countMode: 'number', count: '2.5' }).count).toBe('countRequired');
    expect(validateEntry({ ...valid, countMode: 'number', count: '0' }).count).toBe('countRequired');
    expect(validateEntry({ ...valid, countMode: 'number', count: '12' }).count).toBeUndefined();
    expect(validateEntry({ ...valid, countMode: 'max', count: 'junk' }).count).toBeUndefined();
  });

  it('needs at least one point for free positions, and no spacing is demanded for them to be set', () => {
    const free = { ...valid, layout: 'free' as const, spacing: '' };
    expect(validateEntry(free).points).toBe('noPoints');
    expect(validateEntry({ ...free, freePoints: [[0.1, 0.1]] }).points).toBeUndefined();
  });
});

describe('toEntryLayout / toPreviewEntry', () => {
  it('hands the port what the form says and the server the same fields', () => {
    const form = { ...emptyEntry('e1'), speciesKey: 's', spacing: '30', rowSpacing: '40', layout: 'rows' as const };
    const layout = toEntryLayout(form, 50, [0, 2]);
    expect(layout).toMatchObject({
      layout_strategy: 'rows',
      spacing_cm: 30,
      row_spacing_cm: 40,
      row_assignment: [0, 2],
      mature_width_cm: 50,
    });
    expect(toPreviewEntry(layout!, 12)).toEqual({
      layout_strategy: 'rows',
      spacing_cm: 30,
      row_spacing_cm: 40,
      row_direction: 'along_length',
      row_assignment: [0, 2],
      mature_width_cm: 50,
      max_count: 12,
    });
  });

  it('computes nothing for free positions or an unreadable spacing', () => {
    expect(toEntryLayout({ ...emptyEntry('e'), layout: 'free', spacing: '30' }, null, null)).toBeNull();
    expect(toEntryLayout({ ...emptyEntry('e'), spacing: 'x' }, null, null)).toBeNull();
  });

  it('asks for "as many as fit" with no maximum', () => {
    expect(requestedCount({ ...emptyEntry('e'), countMode: 'max', count: '5' })).toBeNull();
    expect(requestedCount({ ...emptyEntry('e'), countMode: 'number', count: '5' })).toBe(5);
    expect(requestedCount({ ...emptyEntry('e'), countMode: 'number', count: '' })).toBeNull();
  });
});

describe('alternatingRows (GP-FR-070)', () => {
  it('gives each entry every nth row, none twice', () => {
    expect(alternatingRows(5, 2, 0)).toEqual([0, 2, 4]);
    expect(alternatingRows(5, 2, 1)).toEqual([1, 3]);
    expect(alternatingRows(7, 3, 2)).toEqual([2, 5]);
  });

  it('partitions the layout: together the entries hold exactly the plants of the full layout', () => {
    // Anchored on the port itself (which is held to the shared vectors), not on a count written here.
    const base = { layout_strategy: 'rows' as const, spacing_cm: 30, row_spacing_cm: 40 };
    const full = computeLayout(BED_GEOMETRY, base);
    const rows = full.slots.reduce((max, slot) => Math.max(max, (slot.row_index ?? -1) + 1), 0);
    expect(rows).toBeGreaterThan(2);
    const first = computeLayout(BED_GEOMETRY, { ...base, row_assignment: alternatingRows(rows, 2, 0) });
    const second = computeLayout(BED_GEOMETRY, { ...base, row_assignment: alternatingRows(rows, 2, 1) });
    expect(first.count + second.count).toBe(full.count);
    const firstRows = new Set(first.slots.map((slot) => slot.row_index));
    expect(second.slots.every((slot) => !firstRows.has(slot.row_index))).toBe(true);
  });

  it('only entries laid out in rows can share them', () => {
    const grid = { ...emptyEntry('a'), layout: 'grid' as const };
    const rows = { ...emptyEntry('b'), layout: 'rows' as const };
    const zone = { ...emptyEntry('c'), layout: 'zone' as const };
    expect(canAlternate([grid])).toBe(false);
    expect(canAlternate([grid, rows])).toBe(true);
    expect(canAlternate([grid, zone])).toBe(false);
  });
});

describe('tooClosePoints (GP-FR-072: a hint, not a blocker)', () => {
  it('flags both points of a pair below the spacing, and only those', () => {
    const points: [number, number][] = [
      [0, 0],
      [0.2, 0],
      [1, 1],
    ];
    expect(tooClosePoints(points, 30)).toEqual([0, 1]);
  });

  it('does not flag a pair at exactly the spacing (the server tolerance applies)', () => {
    expect(tooClosePoints([[0, 0], [0.3, 0]], 30)).toEqual([]);
    expect(tooClosePoints([[0, 0], [0.299, 0]], 30)).toEqual([]);
    expect(tooClosePoints([[0, 0], [0.29, 0]], 30)).toEqual([0, 1]);
  });
});

describe('containerCheck (W-016.5)', () => {
  const basil = species('sp_b', 'Basil', { recommended_container_volume_l: '5-10' });

  it('warns below the recommended volume and takes its lower bound', () => {
    expect(containerCheck('3', basil)).toEqual({ volumeBelow: true, recommendedL: 5 });
    expect(containerCheck('5', basil).volumeBelow).toBe(false);
    expect(containerCheck('12,5', basil).volumeBelow).toBe(false);
  });

  it('does not warn without a volume or without a recommendation', () => {
    expect(containerCheck('', basil).volumeBelow).toBe(false);
    expect(containerCheck('2', species('sp_x', 'X')).volumeBelow).toBe(false);
  });
});

describe('hints with a strength (D-09)', () => {
  it('asks for a reason from a warning on', () => {
    expect(needsOverrideReason('OK')).toBe(false);
    expect(needsOverrideReason('INFO')).toBe(false);
    expect(needsOverrideReason('WARNING')).toBe(true);
    expect(needsOverrideReason('CRITICAL')).toBe(true);
  });

  it('takes the strongest of several', () => {
    expect(worstSeverity([])).toBe('OK');
    expect(worstSeverity(['INFO', 'CRITICAL', 'WARNING'])).toBe('CRITICAL');
  });
});

describe('names', () => {
  it('derives a 2-5 letter id prefix from the species name, diacritics folded', () => {
    expect(idPrefixOf(species('s', 'Tomate'))).toBe('TOM');
    expect(idPrefixOf(species('s', 'Möhre'))).toBe('MOH');
    expect(idPrefixOf(species('s', '1'))).toMatch(/^[A-Z]{2,5}$/);
    expect(idPrefixOf(null)).toBe('PLT');
  });

  it('builds the LOCATION part of a slot id from the bed name', () => {
    expect(slotIdPrefixOf('Hochbeet 3', 'loc_1')).toBe('HOCHBEET3');
    expect(slotIdPrefixOf('', 'loc_1')).toBe('LLOC1');
    expect(slotIdPrefixOf('A very long bed name indeed', 'k').length).toBeLessThanOrEqual(12);
  });
});
