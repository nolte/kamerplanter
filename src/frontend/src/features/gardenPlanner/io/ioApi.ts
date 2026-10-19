import axios from 'axios';
import i18n from '@/i18n/i18n';
import { tenantClient } from '@/api/client';
import type { ExportOptions, PlanImportReport, PlanImportRequest } from './types';

/**
 * REST access to the plan export and import (REQ-053 §23) through the tenant-scoped client. The three exports are
 * blobs; the import is one JSON call that answers the same report for a dry run and an applied import.
 */

export interface PlanDownload {
  blob: Blob;
  filename: string;
  /** `1:50` and so on, when the server drew a scaled plan (SVG, PDF). */
  scale: string | null;
  /** The server suggests A3 when A4 would need a scale coarser than 1:200. */
  suggestA3: boolean;
}

function exportUrl(siteKey: string, format: ExportOptions['format']): string {
  if (format === 'json') return `/sites/${siteKey}/plan/export`;
  if (format === 'svg') return `/sites/${siteKey}/plan/render.svg`;
  return `/print/garden-plan/${siteKey}`;
}

/** The query of the SVG and the PDF; the JSON backup takes none. */
export function exportParams(options: ExportOptions, locale: string): Record<string, string> {
  if (options.format === 'json') return {};
  const params: Record<string, string> = {
    scale: options.scale,
    paper: options.paper,
    orientation: options.orientation,
    layers: options.layers.join(','),
    locale: locale.startsWith('en') ? 'en' : 'de',
  };
  if (options.format === 'pdf') params.bed_list = String(options.bedList);
  return params;
}

function filenameOf(disposition: unknown, fallback: string): string {
  if (typeof disposition !== 'string') return fallback;
  const match = /filename="([A-Za-z0-9._-]+)"/.exec(disposition);
  return match?.[1] ?? fallback;
}

/** GP-API-004/006/007: the plan as JSON, SVG or PDF. */
export async function fetchPlanExport(
  siteKey: string,
  options: ExportOptions,
  signal?: AbortSignal,
): Promise<PlanDownload> {
  const response = await tenantClient.get<Blob>(exportUrl(siteKey, options.format), {
    params: exportParams(options, i18n.language ?? 'de'),
    responseType: 'blob',
    signal,
  });
  const headers = response.headers as Record<string, unknown>;
  const scale = headers['x-plan-scale'];
  return {
    blob: response.data,
    filename: filenameOf(headers['content-disposition'], `garden-plan-${siteKey}.${options.format}`),
    scale: typeof scale === 'string' ? scale : null,
    suggestA3: headers['x-plan-suggested-paper'] === 'a3',
  };
}

/** GP-API-005: check (`dry_run`) or write a backup file. */
export async function importPlan(siteKey: string, request: PlanImportRequest): Promise<PlanImportReport> {
  const { data } = await tenantClient.post<PlanImportReport>(`/sites/${siteKey}/plan/import`, request);
  return data;
}

/** Hand a blob to the browser as a download. */
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

/** What a failed export request says, when the body (a JSON envelope inside a blob) can be read. */
export interface ExportFailure {
  status: number | null;
  code: string | null;
}

/**
 * Blob requests do not reach the client's envelope parser (the error body is a blob, not an object), so the
 * published code of a refusal (`plan.empty`, `plan.does_not_fit`, ...) is read from the blob here.
 */
export async function describeExportFailure(error: unknown): Promise<ExportFailure> {
  if (!axios.isAxiosError(error)) return { status: null, code: null };
  const status = error.response?.status ?? null;
  const body: unknown = error.response?.data;
  if (typeof Blob !== 'undefined' && body instanceof Blob) {
    try {
      const parsed = JSON.parse(await body.text()) as { error_code?: unknown };
      return { status, code: typeof parsed.error_code === 'string' ? parsed.error_code : null };
    } catch {
      return { status, code: null };
    }
  }
  const code = (body as { error_code?: unknown } | undefined)?.error_code;
  return { status, code: typeof code === 'string' ? code : null };
}
