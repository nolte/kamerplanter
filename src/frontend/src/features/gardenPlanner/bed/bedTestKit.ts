import type { BedListItem, BedSummary } from './types';

/** Fixtures of the bed view tests (REQ-053 WP 3.5). */

export function bedSummary(overrides: Partial<BedSummary> = {}): BedSummary {
  return {
    key: 'loc_b03',
    name: 'Raised bed 3',
    site_key: 'site_1',
    parent_location_key: null,
    location_type_key: 'raised_bed',
    area_m2: 2.4,
    geometry: { kind: 'rect', origin: [1, 1], width_m: 1.2, length_m: 2, rotation_deg: 0 },
    bbox: [1, 1, 2.2, 3],
    bed_status: 'active',
    sun_exposure: 'partial_shade',
    is_bed: true,
    season_state: 'planted',
    active_plant_count: 6,
    species_keys: ['sp_tomato', 'sp_basil'],
    open_task_count: 3,
    overdue_task_count: 1,
    next_due_at: '2026-06-18T00:00:00Z',
    last_care_at: '2026-06-14T18:30:00Z',
    soil_profile: {
      soil_texture: 'loam',
      drainage: 'good',
      site_water_regime: 'fresh',
      conditions: ['stony'],
      growing_medium_kind: 'native_soil',
      ph: 6.5,
      ph_method: 'cacl2',
    },
    ...overrides,
  };
}

export function bedListItem(key: string, overrides: Partial<BedListItem> = {}): BedListItem {
  return {
    key,
    name: `Bed ${key}`,
    site_key: 'site_1',
    location_type_key: 'raised_bed',
    area_m2: 2.4,
    geometry: { kind: 'rect', origin: [1, 1], width_m: 1.2, length_m: 2, rotation_deg: 0 },
    bbox: [1, 1, 2.2, 3],
    bed_status: 'active',
    sun_exposure: 'unknown',
    active_plant_count: 2,
    open_task_count: 1,
    overdue_task_count: 0,
    next_due_at: null,
    ...overrides,
  };
}
