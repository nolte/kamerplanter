/**
 * Wire types of the plan export and import (REQ-053 GP-API-004…007, GP-API-005). Plain data; the
 * parsing of the backup file itself stays on the server, which treats it as untrusted input.
 */

export type ExportFormat = 'json' | 'svg' | 'pdf';
export type ExportPaper = 'a4' | 'a3';
export type ExportOrientation = 'landscape' | 'portrait';

/** `auto` or one of the fixed scales the server accepts (GP-FR-142). */
export const EXPORT_SCALES = [
  'auto',
  '1:20',
  '1:25',
  '1:50',
  '1:75',
  '1:100',
  '1:125',
  '1:150',
  '1:200',
  '1:250',
  '1:300',
  '1:400',
  '1:500',
] as const;
export type ExportScale = (typeof EXPORT_SCALES)[number];

export const EXPORT_LAYERS = ['grid', 'beds', 'objects', 'slots', 'plants', 'labels'] as const;
export type ExportLayer = (typeof EXPORT_LAYERS)[number];

/** GP-FR-172: what the JSON backup holds - the whole site, exactly the selected items, or them and all below. */
export type ExportScope = 'site' | 'selection' | 'subtree';

/** What is selected on the plan; the keys the server expects for a partial export (a garden object as `object:<key>`). */
export interface PlanSelection {
  locationKeys: readonly string[];
  objectKeys: readonly string[];
}

/** The server accepts at most this many keys for a partial export. */
export const MAX_EXPORT_KEYS = 100;

export interface ExportOptions {
  format: ExportFormat;
  /** JSON only. */
  scope: ExportScope;
  /** JSON only: the keys `scope` names (`selection`, `subtree`); empty for `site`. */
  keys: readonly string[];
  paper: ExportPaper;
  orientation: ExportOrientation;
  scale: ExportScale;
  layers: readonly ExportLayer[];
  /** PDF only: the bed list as a second page. */
  bedList: boolean;
}

export const DEFAULT_EXPORT_OPTIONS: ExportOptions = {
  format: 'pdf',
  paper: 'a4',
  orientation: 'landscape',
  scale: 'auto',
  layers: ['beds', 'objects', 'plants', 'labels'],
  bedList: false,
  scope: 'site',
  keys: [],
};

export type ImportMode = 'replace' | 'merge';

/** GP-FR-172: where the file goes. Keys are always new; the other two never resolve a reference outside the file. */
export type ImportTarget = 'same_site' | 'other_site' | 'other_tenant';
export const IMPORT_TARGETS: readonly ImportTarget[] = ['same_site', 'other_site', 'other_tenant'];
/** `offset_m` of a merge moves every geometry by at most this much per axis (m). */
export const MAX_OFFSET_M = 1000;

export interface ImportCounts {
  locations: number;
  garden_objects: number;
  slots: number;
  plan_settings: number;
  zones: number;
}

export interface DroppedReference {
  entity: 'location' | 'garden_object' | 'slot' | 'irrigation_zone';
  key: string;
  field: string;
  reason: string;
}

export interface ImportFinding {
  field: string;
  code: string;
  key: string | null;
}

/** The answer of `POST /plan/import`, the same for a dry run and an applied import. */
export interface PlanImportReport {
  mode: ImportMode;
  dry_run: boolean;
  target: ImportTarget;
  offset_m: [number, number] | null;
  would_create: ImportCounts;
  would_update: ImportCounts;
  would_delete: ImportCounts;
  kept_locations: number;
  dropped_references: DroppedReference[];
  dropped_references_total: number;
  errors: ImportFinding[];
  errors_total: number;
  applied: boolean;
  plan_revision: number | null;
  snapshot_written: boolean;
}

export interface PlanImportRequest {
  mode: ImportMode;
  dry_run: boolean;
  force: boolean;
  confirm_site_name: string | null;
  target?: ImportTarget;
  /** `merge` only: `[dx, dy]` in metres added to every geometry of the file. */
  offset_m?: [number, number] | null;
  document: Record<string, unknown>;
}

/** One plan a `replace` import overwrote (GP-FR-148/170); the plan itself stays on the server. */
export interface PlanSnapshot {
  audit_key: string;
  revision: number;
  at: string;
  summary: string;
  changed_by_name: string | null;
  locations: number;
  garden_objects: number;
  slots: number;
  zones: number;
}

export interface SnapshotRestoreRequest {
  dry_run: boolean;
  force: boolean;
  confirm_site_name: string | null;
}

/** GP-NFR-051: the file is at most 5 MB. */
export const MAX_IMPORT_FILE_BYTES = 5 * 1024 * 1024;

/** GP-FR-174: a CSV bed list is at most 1 MiB and 500 data lines; the server refuses more (413 / 422). */
export const MAX_CSV_FILE_BYTES = 1024 * 1024;
export const MAX_CSV_ROWS = 500;

/** One problem of one line of a CSV bed list; `line` counts the header as 1, `column` is `null` for the whole row. */
export interface BedCsvFinding {
  line: number;
  column: string | null;
  code: string;
}

/** A line the import writes (or wrote): the bed it becomes, placed as a `rect` with `origin` lower-left. */
export interface BedCsvRow {
  line: number;
  name: string;
  location_type_key: string;
  width_m: number;
  length_m: number;
  origin: [number, number];
  sun_exposure: string;
  soil_texture: string | null;
  irrigation_zone_key: string | null;
  /** The new bed's key; `null` in a dry run. */
  location_key: string | null;
}

/** The answer of `POST /sites/{key}/beds/import-csv`, the same for the dry run and the confirmation. */
export interface BedCsvImportReport {
  dry_run: boolean;
  rows_total: number;
  rows: BedCsvRow[];
  rows_valid: number;
  rows_skipped: number;
  errors: BedCsvFinding[];
  errors_total: number;
  warnings: BedCsvFinding[];
  warnings_total: number;
  ignored_columns: string[];
  /** Exact count; `ignored_columns` lists at most 50. */
  ignored_columns_total: number;
  applied: boolean;
  /** The revision the check ran against (sent back as `expected_revision`), or the new one. */
  plan_revision: number;
}
