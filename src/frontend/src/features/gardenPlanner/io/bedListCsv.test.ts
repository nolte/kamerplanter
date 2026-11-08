/**
 * The bed list query (REQ-053 GP-FR-145/175, WP 8.25): one column order for the query and the dialog summary, the
 * assignment only through its flag.
 */
import { describe, expect, it } from 'vitest';
import {
  BED_LIST_DEFAULT_COLUMNS,
  BED_LIST_SITE_CONDITION_COLUMNS,
  bedListCsvParams,
  DEFAULT_BED_LIST_CSV_OPTIONS,
  orderedBedListColumns,
} from './bedListCsv';

describe('bedListCsv', () => {
  it('orders the chosen columns as the file writes them, not as they were ticked', () => {
    expect(orderedBedListColumns(['frost_risk', 'name', 'sun_exposure'])).toEqual([
      'name',
      'sun_exposure',
      'frost_risk',
    ]);
  });

  it('asks for the beds with the default columns and without member names by default', () => {
    expect(bedListCsvParams('s1', DEFAULT_BED_LIST_CSV_OPTIONS, 'en-GB')).toEqual({
      site_key: 's1',
      is_bed: 'true',
      format: 'csv',
      columns: 'name,type,area_m2,status,soil_texture,irrigation_zone,active_plants',
      include_assignment: 'false',
      delimiter: 'comma',
      locale: 'en',
    });
  });

  it('offers the distance to the nearest water source as a selectable column, last in the file (GP-FR-167)', () => {
    expect(BED_LIST_SITE_CONDITION_COLUMNS).toContain('nearest_water_source_m');
    expect(BED_LIST_DEFAULT_COLUMNS).not.toContain('nearest_water_source_m' as never);
    const options = { ...DEFAULT_BED_LIST_CSV_OPTIONS, columns: ['nearest_water_source_m', 'name', 'site_flags'] as const };
    expect(bedListCsvParams('s1', options, 'de').columns).toBe('name,site_flags,nearest_water_source_m');
  });
});
