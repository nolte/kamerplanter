/**
 * The bed list of field mode (REQ-053 GP-UX-030): `GET /locations?site_key=&is_bed=true` with the task
 * counters. It is the first request of field mode - the plan geometry follows once it has answered
 * ("two requests, the list first").
 *
 * A reload never takes rows away: when it fails after the list was shown, the last rows stay - and with
 * them an open bed sheet, its dialog and its undo - and the failure is only reported as `reloadError`.
 *
 * Without a connection the list comes from the plan cache (REQ-053 WP 9.2): `cachedAt` names the time of
 * the online read it was stored by, `offlineMiss` says the cache had nothing for this site.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { parseApiError } from '@/api/errors';
import { listBeds } from '../bed/bedApi';
import type { BedListItem } from '../bed/types';
import { bedListEntry, isOfflineCacheMiss, readThrough, type CacheScope } from '../offline/planCache';

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
  /** The rows come from the plan cache: epoch milliseconds of the online read; `null` = from the server. */
  cachedAt: number | null;
  /** Offline and nothing cached for this site: an empty state, not an error. */
  offlineMiss: boolean;
}

interface Loaded {
  siteKey: string;
  state: FieldBedsState;
  reloadError: string | null;
  cachedAt: number | null;
  offlineMiss: boolean;
}

export function useFieldBeds(siteKey: string, scope: CacheScope | null): FieldBeds {
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    readThrough(scope ? bedListEntry(scope, siteKey) : null, () => listBeds(siteKey))
      .then(({ data: beds, cachedAt }) => {
        if (!cancelled) {
          setLoaded({ siteKey, state: { status: 'ready', beds }, reloadError: null, cachedAt, offlineMiss: false });
        }
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        const message = parseApiError(error);
        const offlineMiss = isOfflineCacheMiss(error);
        setLoaded((previous) =>
          previous && previous.siteKey === siteKey && previous.state.status === 'ready'
            ? { ...previous, reloadError: offlineMiss ? null : message }
            : { siteKey, state: { status: 'error', message }, reloadError: null, cachedAt: null, offlineMiss },
        );
      });
    return () => {
      cancelled = true;
    };
  }, [siteKey, scope, attempt]);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);
  const current = loaded && loaded.siteKey === siteKey ? loaded : null;
  return useMemo(
    () => ({
      state: current?.state ?? { status: 'loading' },
      settled: current !== null,
      reloadError: current?.reloadError ?? null,
      reload,
      cachedAt: current?.cachedAt ?? null,
      offlineMiss: current?.offlineMiss ?? false,
    }),
    [current, reload],
  );
}
