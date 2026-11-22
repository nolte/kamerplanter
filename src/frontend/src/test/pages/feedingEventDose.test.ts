import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import i18n from 'i18next';
import type { FeedingEvent } from '@/api/types';
import {
  feedingPlantKeys,
  formatFeedingAmount,
  formatFeedingDose,
  showsLiquidFields,
} from '@/pages/duengung/feedingEventDose';

function event(overrides: Partial<FeedingEvent> = {}): FeedingEvent {
  return {
    key: 'fe-1',
    plant_key: 'p1',
    timestamp: null,
    application_method: 'fertigation',
    is_supplemental: false,
    tank_fill_event_key: null,
    volume_applied_liters: 5,
    fertilizers_used: [],
    measured_ec_before: null,
    measured_ec_after: null,
    measured_ph_before: null,
    measured_ph_after: null,
    runoff_ec: null,
    runoff_ph: null,
    runoff_volume_liters: null,
    channel_id: null,
    notes: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

const topDress = (overrides: Partial<FeedingEvent> = {}) =>
  event({ application_method: 'top_dress', volume_applied_liters: 0, dose_quantity: 2, dose_unit: 'l', ...overrides });

describe('feedingEventDose (#2903)', () => {
  beforeAll(() => i18n.changeLanguage('de'));
  afterAll(() => i18n.changeLanguage('en'));

  it('shows a top dress in the amount column by its dose, never as 0 L', () => {
    expect(formatFeedingAmount(i18n.t, topDress())).toBe('2 Liter');
    expect(formatFeedingAmount(i18n.t, topDress({ dose_quantity: null, dose_unit: null }))).toBe('—');
    expect(formatFeedingAmount(i18n.t, event())).toBe('5 L');
    // a top dress recorded with a volume on the REQ-004 form keeps its litres
    expect(formatFeedingAmount(i18n.t, topDress({ volume_applied_liters: 3 }))).toBe('3 L');
    // millilitres of a concentrate logged without a task: no volume, the dose instead of "0 L"
    expect(
      formatFeedingAmount(i18n.t, event({ application_method: 'drench', volume_applied_liters: 0, dose_quantity: 5, dose_unit: 'ml' })),
    ).toBe('5 Milliliter');
  });

  it('adds the bed total only to a dose per m²', () => {
    expect(
      formatFeedingDose(i18n.t, { dose_quantity: 40, dose_unit: 'g_per_m2', quantity_total: 100, quantity_total_unit: 'g' }),
    ).toBe('40 Gramm pro m² (100 Gramm gesamt)');
    expect(formatFeedingDose(i18n.t, { dose_quantity: 40, dose_unit: 'g', quantity_total: 100 })).toBe('40 Gramm');
  });

  it('hides the liquid fields of a top dress unless one was recorded', () => {
    expect(showsLiquidFields(event())).toBe(true);
    expect(showsLiquidFields(topDress())).toBe(false);
    expect(showsLiquidFields(topDress({ measured_ph_after: 6.5 }))).toBe(true);
  });

  it('takes every plant of a bed dose, else the one plant key', () => {
    expect(feedingPlantKeys(event({ plant_keys: ['a', 'b'] }))).toEqual(['a', 'b']);
    expect(feedingPlantKeys(event({ plant_keys: [] }))).toEqual(['p1']);
    expect(feedingPlantKeys(event({ plant_key: '', plant_keys: [] }))).toEqual([]);
  });
});
