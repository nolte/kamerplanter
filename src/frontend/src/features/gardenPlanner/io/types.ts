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

export interface ExportOptions {
  format: ExportFormat;
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
};

export type ImportMode = 'replace' | 'merge';

export interface ImportCounts {
  locations: number;
  garden_objects: number;
  slots: number;
  plan_settings: number;
}

export interface DroppedReference {
  entity: 'location' | 'garden_object' | 'slot';
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
  document: Record<string, unknown>;
}

/** GP-NFR-051: the file is at most 5 MB. */
export const MAX_IMPORT_FILE_BYTES = 5 * 1024 * 1024;
