/**
 * REQ-053 W-015 — the count after thinning (port of `thinning_calculator.thinning_count`, same cases as
 * `tests/unit/domain/calculators/test_thinning_calculator.py`), the sowable positions and the failed slots.
 */
import { describe, expect, it } from 'vitest';
import type { PlantingItem } from './plantingTypes';
import { failedSlots, isSowable, parseDecimal, thinningCount } from './thinningLogic';

describe('thinningCount', () => {
  it('holds one plant per spacing along a row', () => {
    expect(thinningCount('length', 1.2, 5)).toBe(24);
  });

  it('does not lose a plant to float noise', () => {
    expect(thinningCount('length', 1.0, 10)).toBe(10);
  });

  it('holds one plant per square of the spacing in a zone', () => {
    expect(thinningCount('area', 1.0, 10)).toBe(100);
  });

  it('keeps one seedling in a slot smaller than one spacing', () => {
    expect(thinningCount('length', 0.02, 5)).toBe(1);
  });

  it('has no count without a positive spacing - there is no default', () => {
    expect(thinningCount('length', 1.0, 0)).toBeNull();
    expect(thinningCount('length', 1.0, -5)).toBeNull();
    expect(thinningCount('length', 1.0, Number.NaN)).toBeNull();
  });
});

describe('parseDecimal', () => {
  it('reads a decimal comma', () => {
    expect(parseDecimal('7,5')).toBe(7.5);
    expect(parseDecimal(' ')).toBeNull();
    expect(parseDecimal('abc')).toBeNull();
  });
});

const planned = (overrides: Partial<PlantingItem>): PlantingItem => ({
  state: 'planned',
  slot_key: 'r1',
  slot_id: 'BED_R01',
  species_key: 'sp_carrot',
  run_key: 'run_1',
  ...overrides,
});

describe('isSowable', () => {
  it('offers sowing for a planned row or zone that is not sown yet', () => {
    expect(isSowable(planned({ slot_role: 'row' }))).toBe(true);
    expect(isSowable(planned({ slot_role: 'zone' }))).toBe(true);
  });

  it('offers no sowing for a position, a sown row or a plant', () => {
    expect(isSowable(planned({ slot_role: 'position' }))).toBe(false);
    expect(isSowable(planned({ slot_role: 'row', sown_at: '2026-04-12' }))).toBe(false);
    expect(isSowable(planned({ state: 'active', slot_role: 'row' }))).toBe(false);
  });
});

describe('failedSlots', () => {
  const died = (slot: string, removed: string, overrides: Partial<PlantingItem> = {}): PlantingItem => ({
    state: 'historical',
    slot_key: slot,
    slot_id: slot.toUpperCase(),
    species_key: 'sp_tomato',
    cultivar_key: 'cv_1',
    plant_key: `p_${slot}_${removed}`,
    removed_on: removed,
    termination_type: 'died',
    ...overrides,
  });

  it('lists a slot whose newest plant died, with its crop', () => {
    expect(failedSlots([died('s1', '2026-06-01')])).toEqual([
      { slotKey: 's1', slotId: 'S1', speciesKey: 'sp_tomato', cultivarKey: 'cv_1', removedOn: '2026-06-01' },
    ]);
  });

  it('counts senesced as failed, a harvest not', () => {
    expect(failedSlots([died('s1', '2026-06-01', { termination_type: 'senesced' })])).toHaveLength(1);
    expect(failedSlots([died('s1', '2026-06-01', { state: 'harvested', termination_type: 'harvested' })])).toEqual([]);
  });

  it('judges the newest plant of the slot only', () => {
    const items = [
      died('s1', '2026-05-01'),
      died('s1', '2026-07-01', { state: 'harvested', termination_type: 'harvested' }),
    ];
    expect(failedSlots(items)).toEqual([]);
  });

  it('skips a slot in which something stands or is planned again', () => {
    const items = [
      died('s1', '2026-06-01'),
      { state: 'active', slot_key: 's1', slot_id: 'S1', species_key: 'sp_tomato', plant_key: 'p_new' } as PlantingItem,
      died('s2', '2026-06-01'),
      planned({ slot_key: 's2' }),
    ];
    expect(failedSlots(items)).toEqual([]);
  });
});
