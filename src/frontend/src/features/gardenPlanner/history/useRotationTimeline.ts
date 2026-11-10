/**
 * Loads the planting timeline of a bed (`GET /locations/{key}/rotation`, REQ-053 GP-API-039). The
 * server chooses the look-back (`max(pause of the families involved, 5)` years, at most ten) unless the
 * caller names `years`. A new `version` fetches again (a year was filled in or a planting changed elsewhere).
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { parseApiError } from '@/api/errors';
import { getRotationTimeline } from './historyApi';
import type { RotationTimeline } from './historyTypes';

export type TimelineState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; timeline: RotationTimeline };

export function useRotationTimeline(bedKey: string, years?: number, version = 0) {
  const [state, setState] = useState<TimelineState>({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    getRotationTimeline(bedKey, years)
      .then((timeline) => {
        if (!cancelled) setState({ status: 'ready', timeline });
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ status: 'error', message: parseApiError(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [bedKey, years, version, attempt]);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);
  return useMemo(() => ({ state, reload }), [state, reload]);
}
