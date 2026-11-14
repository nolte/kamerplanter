/**
 * The bed list as CSV (REQ-053 GP-FR-145, GP-FR-175; WP 8.25): the columns the server writes and the query it takes.
 * The column ids mirror `app/domain/engines/bed_list_csv_engine.py` (Python is the reference); the server refuses an
 * unknown one with 422 `export.unknown_column`. The member names are not a column to pick: they enter the file only
 * through `include_assignment` (SR-024).
 */

/** GP-FR-145: name, type, area, status, soil texture, irrigation zone, active plants - pre-selected. */
export const BED_LIST_DEFAULT_COLUMNS = [
  'name',
  'type',
  'area_m2',
  'status',
  'soil_texture',
  'irrigation_zone',
  'active_plants',
] as const;

/**
 * GP-FR-175: the site features of §10.2 (and the coarse sun class they refine), selectable on top; the last one is
 * the distance to the nearest water source in metres, derived from the plan (GP-FR-167).
 */
export const BED_LIST_SITE_CONDITION_COLUMNS = [
  'sun_exposure',
  'sun_window',
  'direct_sun_hours_summer',
  'foliage_shade_in_summer',
  'frost_risk',
  'cold_air_pocket',
  'heat_retention',
  'wind_exposure',
  'slope_deg',
  'aspect_deg',
  'access_sides',
  'site_flags',
  'nearest_water_source_m',
] as const;

/**
 * GP-FR-176 (#2759): the bed's stable parcel identifier (an allotment number), selectable, written right after the
 * name. Not pre-selected - GP-FR-145 names the defaults, and most gardens set no parcel label.
 */
export const BED_LIST_PARCEL_LABEL_COLUMN = 'parcel_label' as const;

export type BedListColumn =
  | (typeof BED_LIST_DEFAULT_COLUMNS)[number]
  | typeof BED_LIST_PARCEL_LABEL_COLUMN
  | (typeof BED_LIST_SITE_CONDITION_COLUMNS)[number];

/** The bed's own data as the dialog groups it: the GP-FR-145 defaults with the parcel label after the name. */
export const BED_LIST_BED_COLUMNS: readonly BedListColumn[] = [
  BED_LIST_DEFAULT_COLUMNS[0],
  BED_LIST_PARCEL_LABEL_COLUMN,
  ...BED_LIST_DEFAULT_COLUMNS.slice(1),
];

/** Every selectable column in the order the file writes them (the server orders them the same way). */
export const BED_LIST_COLUMNS: readonly BedListColumn[] = [
  ...BED_LIST_BED_COLUMNS,
  ...BED_LIST_SITE_CONDITION_COLUMNS,
];

export interface BedListCsvOptions {
  columns: readonly BedListColumn[];
  /** SR-024: the members a bed is assigned to, by display name. Off unless the person asks for it. */
  includeAssignment: boolean;
  /** The Excel variant: semicolon delimiter and decimal comma. */
  excel: boolean;
}

export const DEFAULT_BED_LIST_CSV_OPTIONS: BedListCsvOptions = {
  columns: BED_LIST_DEFAULT_COLUMNS,
  includeAssignment: false,
  excel: false,
};

/** The chosen columns in the order the file writes them (the server's order), whatever order they were ticked in. */
export function orderedBedListColumns(columns: readonly BedListColumn[]): BedListColumn[] {
  return BED_LIST_COLUMNS.filter((column) => columns.includes(column));
}

/** The query of `GET /locations?format=csv`: the site's beds, the chosen columns in file order. */
export function bedListCsvParams(
  siteKey: string,
  options: BedListCsvOptions,
  locale: string,
): Record<string, string> {
  return {
    site_key: siteKey,
    is_bed: 'true',
    format: 'csv',
    columns: orderedBedListColumns(options.columns).join(','),
    include_assignment: String(options.includeAssignment),
    delimiter: options.excel ? 'semicolon' : 'comma',
    locale: locale.startsWith('en') ? 'en' : 'de',
  };
}
