/**
 * What the bed sheet of field mode shows (REQ-053 §18.1 steps 3-4): the pending tasks of the bed and its
 * plants (GP-API-030) and the standing plants with species and phase (GP-API-054). The plants are
 * informational - a failed request leaves them `null` (unknown, not "none") instead of failing the sheet.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { parseApiError } from '@/api/errors';
import { getBedQueue } from '../care/careApi';
import type { CareTask } from '../care/careTypes';
import { listPlantStates, type PlantStateWire } from '../planting/plantStateApi';

export type BedSheetState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; tasks: CareTask[]; plants: PlantStateWire[] | null };

export interface BedSheet {
  state: BedSheetState;
  /** Fetch again without blanking the sheet. */
  reload: () => void;
}

export function useBedSheet(bedKey: string): BedSheet {
  const [loaded, setLoaded] = useState<{ bedKey: string; state: BedSheetState } | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      getBedQueue(bedKey),
      listPlantStates(bedKey, controller.signal).catch((): null => null),
    ])
      .then(([tasks, plants]) => {
        if (!controller.signal.aborted) setLoaded({ bedKey, state: { status: 'ready', tasks, plants } });
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setLoaded({ bedKey, state: { status: 'error', message: parseApiError(error) } });
        }
      });
    return () => controller.abort();
  }, [bedKey, attempt]);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);
  const state = loaded && loaded.bedKey === bedKey ? loaded.state : null;
  return useMemo(() => ({ state: state ?? { status: 'loading' }, reload }), [state, reload]);
}
