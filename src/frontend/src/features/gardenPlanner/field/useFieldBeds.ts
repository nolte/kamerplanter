/**
 * The bed list of field mode (REQ-053 GP-UX-030): `GET /locations?site_key=&is_bed=true` with the task
 * counters. It is the first request of field mode - the plan geometry follows once it has answered
 * ("two requests, the list first").
 *
 * A reload never takes rows away: when it fails after the list was shown, the last rows stay - and with
 * them an open bed sheet, its dialog and its undo - and the failure is only reported as `reloadError`.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { parseApiError } from '@/api/errors';
import { listBeds } from '../bed/bedApi';
import type { BedListItem } from '../bed/types';

export type FieldBedsState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; beds: BedListItem[] };

export interface FieldBeds {
  state: FieldBedsState;
  /** `true` once the list has answered (success or failure): the geometry may load now. */
  settled: boolean;
  /** The last reload failed while rows were shown; the rows are the last good answer. */
  reloadError: string | null;
  /** Fetch again; the rows stay while the request runs. */
  reload: () => void;
}

interface Loaded {
  siteKey: string;
  state: FieldBedsState;
  reloadError: string | null;
}

export function useFieldBeds(siteKey: string): FieldBeds {
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    listBeds(siteKey)
      .then((beds) => {
        if (!cancelled) setLoaded({ siteKey, state: { status: 'ready', beds }, reloadError: null });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        const message = parseApiError(error);
        setLoaded((previous) =>
          previous && previous.siteKey === siteKey && previous.state.status === 'ready'
            ? { ...previous, reloadError: message }
            : { siteKey, state: { status: 'error', message }, reloadError: null },
        );
      });
    return () => {
      cancelled = true;
    };
  }, [siteKey, attempt]);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);
  const current = loaded && loaded.siteKey === siteKey ? loaded : null;
  return useMemo(
    () => ({
      state: current?.state ?? { status: 'loading' },
      settled: current !== null,
      reloadError: current?.reloadError ?? null,
      reload,
    }),
    [current, reload],
  );
}
