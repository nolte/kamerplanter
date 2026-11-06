/**
 * The bed list query (REQ-053 GP-FR-145/175, WP 8.25): one column order for the query and the dialog summary, the
 * assignment only through its flag.
 */
import { describe, expect, it } from 'vitest';
import { bedListCsvParams, DEFAULT_BED_LIST_CSV_OPTIONS, orderedBedListColumns } from './bedListCsv';

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
});
