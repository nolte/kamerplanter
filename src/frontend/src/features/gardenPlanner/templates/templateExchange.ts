/**
 * Template exchange as a JSON file (REQ-053 GP-FR-173, GP-API-070/071; WP 9.9). "Export" downloads one template
 * as a file without keys, owner, author or note; "Import" sends such a file - first as a dry run (the check
 * report), then, once the user confirms, for real. The file travels as the request body itself, unchanged.
 */
import { tenantClient } from '@/api/client';
import { isApiError } from '@/api/errors';
import type { Geometry } from '../model/types';

/** GP-API-071: the server refuses a larger file with 413; the panel says so before sending it. */
export const MAX_TEMPLATE_FILE_BYTES = 256 * 1024;

/** The file of GP-API-070 (and the `template` of the report: the template as it is or would be stored). */
export interface BedTemplateExchangeFile {
  format: 'kamerplanter.bed_template';
  schema_version: string;
  name: string;
  location_type_key: string;
  default_geometry: Geometry;
  height_m?: number | null;
  default_layout: { row_spacing_cm?: number | null; spacing_cm?: number | null };
  soil_profile_defaults?: Record<string, unknown> | null;
}

/** GP-API-071: the same report for the dry run and the applied import. */
export interface BedTemplateImportReport {
  dry_run: boolean;
  schema_version: string;
  migrated: boolean;
  template: BedTemplateExchangeFile;
  created_key: string | null;
  /** Known fields of the file that were dropped on purpose (`tenant_key`, `created_by`, ...). */
  dropped_fields: string[];
  unknown_fields_ignored: number;
}

/** Why an import was refused, as the panel words it. */
export type TemplateImportFailure =
  | { kind: 'name_taken'; suggestedName: string | null }
  | { kind: 'too_large' }
  | { kind: 'forbidden' }
  | { kind: 'code'; code: string }
  | { kind: 'generic' };

function filenameOf(disposition: unknown, fallback: string): string {
  if (typeof disposition !== 'string') return fallback;
  const match = /filename="([A-Za-z0-9._-]+)"/.exec(disposition);
  return match?.[1] ?? fallback;
}

/** GP-API-070: one template as a file (readable by every member). */
export async function exportBedTemplate(key: string): Promise<{ blob: Blob; filename: string }> {
  const response = await tenantClient.get<Blob>(
    `/bed-templates/${encodeURIComponent(key)}/export`,
    { responseType: 'blob' },
  );
  const headers = response.headers as Record<string, unknown>;
  return {
    blob: response.data,
    filename: filenameOf(headers['content-disposition'], `bed-template-${key}.json`),
  };
}

/**
 * GP-API-071: check (`dryRun`) or import a template file. `name` replaces the file's name - the way out of a
 * 409 `bed_template.name_taken`.
 */
export async function importBedTemplate(
  file: Blob,
  options: { dryRun: boolean; name?: string | null },
): Promise<BedTemplateImportReport> {
  const params: Record<string, string> = { dry_run: String(options.dryRun) };
  if (options.name) params.name = options.name;
  const { data } = await tenantClient.post<BedTemplateImportReport>(
    '/bed-templates/import',
    file,
    { params, headers: { 'Content-Type': 'application/json' } },
  );
  return data;
}

/** The refusal of an import, read from the published code of the error envelope. */
export function describeImportFailure(error: unknown): TemplateImportFailure {
  if (!isApiError(error)) return { kind: 'generic' };
  if (error.statusCode === 413) return { kind: 'too_large' };
  if (error.statusCode === 403) return { kind: 'forbidden' };
  const detail = error.details[0] as (typeof error.details)[number] & { suggested_name?: unknown };
  const code = detail?.code ?? '';
  if (error.statusCode === 409 && code === 'bed_template.name_taken') {
    const suggested = detail.suggested_name;
    return { kind: 'name_taken', suggestedName: typeof suggested === 'string' ? suggested : null };
  }
  return code ? { kind: 'code', code } : { kind: 'generic' };
}
