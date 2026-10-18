/**
 * Loads what the care tab shows: the pending tasks of the bed and its plants (GP-API-030) and the
 * plants standing in it, which name the plant tasks. The plants are informational - a failed request
 * leaves the plant tasks with their own names instead of failing the tab.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { parseApiError } from '@/api/errors';
import { getBedQueue, listActivePlants } from './careApi';
import type { BedPlantRef, CareTask } from './careTypes';

export type BedCareState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; tasks: CareTask[]; plants: BedPlantRef[]; loadedAt: number };

export interface BedCare {
  state: BedCareState;
  /** Fetch again without blanking the list (the rows stay while the request runs). */
  reload: () => void;
}

export function useBedCare(bedKey: string): BedCare {
  const [state, setState] = useState<BedCareState>({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getBedQueue(bedKey), listActivePlants(bedKey).catch((): BedPlantRef[] => [])])
      .then(([tasks, plants]) => {
        if (!cancelled) setState({ status: 'ready', tasks, plants, loadedAt: Date.now() });
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ status: 'error', message: parseApiError(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [bedKey, attempt]);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);
  return useMemo(() => ({ state, reload }), [state, reload]);
}
