/**
 * REQ-053 W-015 — the count after thinning (port of `thinning_calculator.thinning_count`, same cases as
 * `tests/unit/domain/calculators/test_thinning_calculator.py`), the sowable positions and the failed slots.
 */
import { describe, expect, it } from 'vitest';
import type { PlantingItem } from './plantingTypes';
import {
  failedSlots,
  isAwaitingThinning,
  isSowable,
  isZoneStand,
  parseDecimal,
  recordsZoneStand,
  spacingExceedsSlot,
  thinningCount,
  thinningFormula,
  thinningLimit,
} from './thinningLogic';

describe('zone stand above the quota (#2862)', () => {
  it('records a stand only for a zone above the quota', () => {
    expect(recordsZoneStand('area', 501, 500)).toBe(true);
    expect(recordsZoneStand('area', 500, 500)).toBe(false);
    expect(recordsZoneStand('length', 600, 500)).toBe(false);
    expect(recordsZoneStand('area', null, 500)).toBe(false);
  });

  it('lets a zone count up to the stand bound and keeps a row at the quota', () => {
    expect(thinningLimit('area', 500, 100000)).toBe(100000);
    expect(thinningLimit('length', 500, 100000)).toBe(500);
    expect(thinningLimit('area', 500, null)).toBe(500);
  });

  it('tells a zone stand from a sown slot still to thin', () => {
    const sown: PlantingItem = { state: 'planned', slot_key: 'z1', species_key: 'sp', slot_role: 'zone', sown_at: '2026-04-12' };
    const stand: PlantingItem = { ...sown, thinned_at: '2026-05-20' };
    expect([isAwaitingThinning(sown), isZoneStand(sown)]).toEqual([true, false]);
    expect([isAwaitingThinning(stand), isZoneStand(stand)]).toEqual([false, true]);
    expect(isSowable(stand)).toBe(false);
  });
});

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

describe('thinningCount with a row spacing (#2862, same cases as TestRowSpacing in pytest)', () => {
  it('counts carrot at 4 cm in rows 25 cm apart as about 100 per m²', () => {
    expect(thinningCount('area', 1.0, 4, 25)).toBe(100);
  });

  it('keeps the square-grid estimate without a row spacing', () => {
    expect(thinningCount('area', 1.0, 4)).toBe(625);
    expect(thinningCount('area', 1.0, 4, null)).toBe(625);
  });

  it('ignores the row spacing on a row', () => {
    expect(thinningCount('length', 1.2, 5, 25)).toBe(24);
  });

  it('has no count for a row spacing that is not positive', () => {
    expect(thinningCount('area', 1.0, 4, 0)).toBeNull();
  });

  it('names the formula', () => {
    expect(thinningFormula('length', 25)).toBe('along_row');
    expect(thinningFormula('area', 25)).toBe('rows');
    expect(thinningFormula('area', null)).toBe('square_grid');
  });
});

describe('spacingExceedsSlot', () => {
  it('tells when one spacing is longer than the row or wider than the zone', () => {
    expect(spacingExceedsSlot('length', 0.3, 40)).toBe(true);
    expect(spacingExceedsSlot('length', 1.2, 5)).toBe(false);
    expect(spacingExceedsSlot('area', 0.04, 25)).toBe(true);
    expect(spacingExceedsSlot('area', 1.0, 10)).toBe(false);
    // 4 cm × 25 cm is a cell of 0.01 m²: a zone of 0.005 m² keeps one seedling, the square grid would not say so.
    expect(spacingExceedsSlot('area', 0.005, 4, 25)).toBe(true);
    expect(spacingExceedsSlot('area', 0.005, 4)).toBe(false);
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
      {
        slotKey: 's1',
        slotId: 'S1',
        plantKey: 'p_s1_2026-06-01',
        speciesKey: 'sp_tomato',
        cultivarKey: 'cv_1',
        removedOn: '2026-06-01',
      },
    ]);
  });

  it('offers a replant only after a plant died - not after it senesced or was harvested', () => {
    expect(failedSlots([died('s1', '2026-06-01', { termination_type: 'senesced' })])).toEqual([]);
    expect(failedSlots([died('s1', '2026-06-01', { state: 'harvested', termination_type: 'harvested' })])).toEqual([]);
  });

  it('judges the newest plant of the slot only', () => {
    const items = [
      died('s1', '2026-05-01'),
      died('s1', '2026-07-01', { state: 'harvested', termination_type: 'harvested' }),
    ];
    expect(failedSlots(items)).toEqual([]);
  });

  it('names the newest died plant of the slot as the one a replant replaces (#2888)', () => {
    const items = [died('s1', '2026-05-01'), died('s1', '2026-06-15')];
    expect(failedSlots(items).map((slot) => slot.plantKey)).toEqual(['p_s1_2026-06-15']);
  });

  it('has no plant to name when the listing carries no plant key', () => {
    expect(failedSlots([died('s1', '2026-06-01', { plant_key: null })])[0].plantKey).toBeNull();
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
