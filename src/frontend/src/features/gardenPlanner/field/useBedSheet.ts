/**
 * What the bed sheet of field mode shows (REQ-053 §18.1 steps 3-4): the pending tasks of the bed and its
 * plants (GP-API-030) and the standing plants with species and phase (GP-API-054). The plants are
 * informational - a failed request leaves them `null` (unknown, not "none") instead of failing the sheet.
 *
 * Without a connection the sheet comes from the plan cache (REQ-053 WP 9.2) under
 * `{user_key}:{tenant_key}:{location_key}`: `cachedAt` names the online read it was stored by, `offlineMiss`
 * says nothing was cached for this bed. Writes stay locked offline (the sheet checks `online`).
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { parseApiError } from '@/api/errors';
import { getBedQueue } from '../care/careApi';
import type { CareTask } from '../care/careTypes';
import { bedSheetEntry, isOfflineCacheMiss, readThrough, type CacheScope } from '../offline/planCache';
import { listPlantStates, type PlantStateWire } from '../planting/plantStateApi';

export type BedSheetState =
  | { status: 'loading' }
  | { status: 'error'; message: string; offlineMiss: boolean }
  | { status: 'ready'; tasks: CareTask[]; plants: PlantStateWire[] | null; cachedAt: number | null };

interface SheetData {
  tasks: CareTask[];
  plants: PlantStateWire[] | null;
}

export interface BedSheet {
  state: BedSheetState;
  /** Fetch again without blanking the sheet. */
  reload: () => void;
}

export function useBedSheet(bedKey: string, scope: CacheScope | null): BedSheet {
  const [loaded, setLoaded] = useState<{ bedKey: string; state: BedSheetState } | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    readThrough<SheetData>(scope ? bedSheetEntry(scope, bedKey) : null, async () => {
      const [tasks, plants] = await Promise.all([
        getBedQueue(bedKey),
        listPlantStates(bedKey, controller.signal).catch((): null => null),
      ]);
      return { tasks, plants };
    })
      .then(({ data, cachedAt }) => {
        if (!controller.signal.aborted) {
          setLoaded({ bedKey, state: { status: 'ready', tasks: data.tasks, plants: data.plants, cachedAt } });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setLoaded({
            bedKey,
            state: { status: 'error', message: parseApiError(error), offlineMiss: isOfflineCacheMiss(error) },
          });
        }
      });
    return () => controller.abort();
  }, [bedKey, scope, attempt]);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);
  const state = loaded && loaded.bedKey === bedKey ? loaded.state : null;
  return useMemo(() => ({ state: state ?? { status: 'loading' }, reload }), [state, reload]);
}
