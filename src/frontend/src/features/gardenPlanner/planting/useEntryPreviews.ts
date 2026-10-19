/**
 * The live preview of the planting dialog (REQ-053 GP-FR-063): the TypeScript port answers at once,
 * the server's answer follows after a short debounce and replaces it - the server is authoritative
 * wherever the two differ. A refusal (`layout.too_many_positions` ...) is a result, not an exception.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { parseApiError } from '@/api/errors';
import { computeLayout, LayoutError, type EntryLayout, type LayoutResult } from '../model/layout';
import type { Geometry, Point } from '../model/types';
import { previewLayout } from './plantingApi';
import { toPreviewEntry } from './plantingLogic';
import type { PreviewResponse, PreviewWarning } from './plantingTypes';

/** How long the inputs must rest before the server is asked (the dialog is typed into). */
export const PREVIEW_DEBOUNCE_MS = 350;

export interface PreviewRequest {
  /** The entry's local id. */
  id: string;
  /** `null` = nothing to compute (spacing missing, or `free`, which the user places by hand). */
  layout: EntryLayout | null;
  /** The requested number of plants; `null` = as many as fit. */
  maxCount: number | null;
}

export interface PreviewPosition {
  point: Point;
  row: number | null;
}

export interface EntryPreview {
  positions: PreviewPosition[];
  zones: Point[][];
  count: number;
  capacityMax: number;
  warnings: PreviewWarning[];
  /** Who computed what is shown. */
  source: 'local' | 'server';
  /** The server has not confirmed the local result yet. */
  pending: boolean;
  /** A refusal (`code`, e.g. `layout.too_many_positions`) or a failed request. */
  error: { code: string | null; message: string } | null;
}

const IDLE: EntryPreview = {
  positions: [],
  zones: [],
  count: 0,
  capacityMax: 0,
  warnings: [],
  source: 'local',
  pending: false,
  error: null,
};

function fromLocal(result: LayoutResult): EntryPreview {
  return {
    positions: result.slots.flatMap((slot) =>
      slot.point ? [{ point: slot.point, row: slot.row_index }] : [],
    ),
    zones: result.slots.flatMap((slot) => (slot.outline ? [slot.outline] : [])),
    count: result.count,
    capacityMax: result.capacity_max,
    warnings: result.warnings.map((w) => ({ code: w.code, detail: w.detail })),
    source: 'local',
    pending: true,
    error: null,
  };
}

function fromServer(response: PreviewResponse): EntryPreview {
  return {
    positions: response.slots.flatMap((slot) =>
      slot.geometry.kind === 'point' ? [{ point: slot.geometry.origin, row: slot.row_index }] : [],
    ),
    zones: response.slots.flatMap((slot) =>
      slot.geometry.kind === 'polygon' ? [slot.geometry.points] : [],
    ),
    count: response.count,
    capacityMax: response.capacity_max,
    warnings: response.warnings,
    source: 'server',
    pending: false,
    error: null,
  };
}

function localPreview(bed: Geometry | null, request: PreviewRequest): EntryPreview {
  if (!bed || !request.layout) return IDLE;
  try {
    return fromLocal(computeLayout(bed, request.layout, request.maxCount));
  } catch (error) {
    if (error instanceof LayoutError) {
      return { ...IDLE, error: { code: error.code, message: error.message } };
    }
    throw error;
  }
}

type ServerAnswer = { signature: string; preview: EntryPreview };

function signatureOf(request: PreviewRequest): string {
  return request.layout ? JSON.stringify(toPreviewEntry(request.layout, request.maxCount)) : '';
}

/** One preview per request, keyed by the request's id. `requests` must be a stable (memoised) array. */
export function useEntryPreviews(
  bedKey: string,
  bed: Geometry | null,
  requests: readonly PreviewRequest[],
  debounceMs: number = PREVIEW_DEBOUNCE_MS,
): Record<string, EntryPreview> {
  const [answers, setAnswers] = useState<Record<string, ServerAnswer>>({});
  const local = useMemo(
    () => Object.fromEntries(requests.map((r) => [r.id, localPreview(bed, r)])),
    [bed, requests],
  );
  const localRef = useRef(local);
  useEffect(() => {
    localRef.current = local;
  }, [local]);
  const signatures = useMemo(
    () => Object.fromEntries(requests.map((r) => [r.id, signatureOf(r)])),
    [requests],
  );
  // The server is asked only for what the port could compute: a refusal would be the same.
  const askable = useMemo(
    () =>
      requests
        .filter((r) => r.layout && local[r.id].error === null)
        .map((r) => ({ id: r.id, signature: signatures[r.id], entry: toPreviewEntry(r.layout!, r.maxCount) })),
    [requests, local, signatures],
  );
  const askKey = JSON.stringify(askable.map((a) => [a.id, a.signature]));
  // What was asked already, by entry: an entry whose content did not change is not asked again when another
  // one changes. An answer that arrives late is kept - it is only read where its signature still matches.
  const asked = useRef<Record<string, string>>({});
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    const pending = askable.filter((item) => asked.current[item.id] !== item.signature);
    if (pending.length === 0) return undefined;
    const handle = setTimeout(() => {
      pending.forEach((item) => {
        asked.current[item.id] = item.signature;
        previewLayout(bedKey, item.entry)
          .then((response) => {
            if (!mounted.current) return;
            setAnswers((current) => ({
              ...current,
              [item.id]: { signature: item.signature, preview: fromServer(response) },
            }));
          })
          .catch((error: unknown) => {
            if (!mounted.current) return;
            setAnswers((current) => ({
              ...current,
              [item.id]: {
                signature: item.signature,
                preview: {
                  ...localRef.current[item.id],
                  pending: false,
                  error: { code: null, message: parseApiError(error) },
                },
              },
            }));
          });
      });
    }, debounceMs);
    return () => clearTimeout(handle);
    // `askKey` stands for the content of `askable`; `local` only feeds the error fallback.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bedKey, askKey, debounceMs]);

  return useMemo(
    () =>
      Object.fromEntries(
        requests.map((r) => {
          const answer = answers[r.id];
          const confirmed = answer && answer.signature === signatures[r.id];
          const preview = confirmed ? answer.preview : local[r.id];
          return [r.id, preview];
        }),
      ),
    [requests, answers, local, signatures],
  );
}
