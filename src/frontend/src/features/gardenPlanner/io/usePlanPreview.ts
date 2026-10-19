import { useEffect, useState } from 'react';
import { describeExportFailure, fetchPlanExport } from './ioApi';
import type { ExportOptions } from './types';

/** How long the options stay unchanged before a preview is requested (each preview is one export request). */
const PREVIEW_DEBOUNCE_MS = 500;

export interface BackupSummary {
  locations: number;
  gardenObjects: number;
  slots: number;
  bytes: number;
}

export type PlanPreview =
  | { status: 'idle' | 'loading' }
  | { status: 'svg'; url: string; scale: string | null; suggestA3: boolean }
  | { status: 'json'; summary: BackupSummary }
  | { status: 'error'; code: string | null; httpStatus: number | null };

interface Settled {
  key: string;
  preview: PlanPreview;
}

function countOf(value: unknown): number {
  return Array.isArray(value) ? value.length : 0;
}

/**
 * The preview of the export dialog (GP-UX-050): the drawn plan for SVG and PDF (the SVG is what the PDF embeds),
 * the size of the backup for JSON. A request per settled option change, cancelled when the options change again
 * or the dialog closes; the object URL is released with it.
 *
 * Derived, not stored: a result belongs to the key it was fetched for, and anything else reads as "loading", so
 * no state is set from the effect body.
 */
export function usePlanPreview(siteKey: string, options: ExportOptions, enabled: boolean): PlanPreview {
  const { paper, orientation, scale } = options;
  // SVG and PDF share one preview (the SVG the PDF embeds): switching between them must not refetch or revoke it.
  const kind = options.format === 'json' ? 'json' : 'svg';
  const layers = options.layers.join(',');
  const key = `${siteKey}|${kind === 'json' ? 'json' : `svg|${paper}|${orientation}|${scale}|${layers}`}`;
  const [settled, setSettled] = useState<Settled | null>(null);

  useEffect(() => {
    if (!enabled) return undefined;
    const controller = new AbortController();
    let objectUrl: string | null = null;
    const timer = setTimeout(() => {
      const request: ExportOptions = {
        format: kind,
        paper,
        orientation,
        scale,
        layers: layers === '' ? [] : (layers.split(',') as ExportOptions['layers']),
        bedList: false,
      };
      fetchPlanExport(siteKey, request, controller.signal)
        .then(async (download) => {
          if (controller.signal.aborted) return;
          if (kind === 'json') {
            const parsed = JSON.parse(await download.blob.text()) as Record<string, unknown>;
            setSettled({
              key,
              preview: {
                status: 'json',
                summary: {
                  locations: countOf(parsed.locations),
                  gardenObjects: countOf(parsed.garden_objects),
                  slots: countOf(parsed.slots),
                  bytes: download.blob.size,
                },
              },
            });
            return;
          }
          objectUrl = URL.createObjectURL(download.blob);
          setSettled({
            key,
            preview: { status: 'svg', url: objectUrl, scale: download.scale, suggestA3: download.suggestA3 },
          });
        })
        .catch(async (error: unknown) => {
          if (controller.signal.aborted) return;
          const failure = await describeExportFailure(error);
          setSettled({
            key,
            preview: { status: 'error', code: failure.code, httpStatus: failure.status },
          });
        });
    }, PREVIEW_DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
      if (objectUrl !== null) URL.revokeObjectURL(objectUrl);
    };
  }, [key, enabled, siteKey, kind, paper, orientation, scale, layers]);

  if (!enabled) return { status: 'idle' };
  return settled !== null && settled.key === key ? settled.preview : { status: 'loading' };
}
