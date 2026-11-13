/**
 * What the bed sheet of field mode shows (REQ-053 §18.1 steps 3-4): the pending tasks of the bed and its
 * plants (GP-API-030) and the standing plants with species and phase (GP-API-054). The plants are
 * informational - a failed request leaves them `null` (unknown, not "none") instead of failing the sheet.
 *
 * Without a connection the sheet comes from the plan cache (REQ-053 WP 9.2) under
 * `{user_key}:{tenant_key}:{location_key}`: `cachedAt` names the online read it was stored by, `offlineMiss`
 * says nothing was cached for this bed. Writes stay locked offline (the sheet checks `online`).
 *
 * Only a complete answer is cached (#2789 review C5): a failed or aborted plant-state read must not
 * overwrite a good entry with `plants: null`. And only what the sheet shows (L1): the person-related
 * fields of a task (assignee, completion notes, photos, ratings) and the plants' photo refs are stripped.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { parseApiError } from '@/api/errors';
import { getBedQueue } from '../care/careApi';
import type { CareTask } from '../care/careTypes';
import { bedSheetEntry, isOfflineCacheMiss, readThrough, type CacheScope } from '../offline/planCache';
import { useRequestLanguage } from '@/hooks/useRequestLanguage';
import { isPlantEntry, listPlantStates, type PlantStateWire } from '../planting/plantStateApi';

export type BedSheetState =
  | { status: 'loading' }
  | { status: 'error'; message: string; offlineMiss: boolean }
  | { status: 'ready'; tasks: CareTask[]; plants: PlantStateWire[] | null; cachedAt: number | null };

interface SheetData {
  tasks: CareTask[];
  plants: PlantStateWire[] | null;
  /** Both reads answered and none was aborted; read by `storedProjection('bedSheets')`, never stored. */
  complete?: boolean;
}

export interface BedSheet {
  state: BedSheetState;
  /** Fetch again without blanking the sheet. */
  reload: () => void;
  /** A read is on its way and its answer is not in yet (the first load or a reload). */
  reloading: boolean;
}

/** How long one read of the bed sheet may take before it counts as no answer. */
export const SHEET_READ_TIMEOUT_MS = 15_000;

export function useBedSheet(bedKey: string, scope: CacheScope | null): BedSheet {
  const [loaded, setLoaded] = useState<{ bedKey: string; attempt: number; state: BedSheetState } | null>(null);
  const [attempt, setAttempt] = useState(0);
  // The plants' species names are worded by the server in the UI language (#2902): a switch reads again, and the
  // offline copy is kept per language.
  const requestLanguage = useRequestLanguage();

  useEffect(() => {
    const controller = new AbortController();
    readThrough<SheetData>(scope ? bedSheetEntry(scope, bedKey, requestLanguage) : null, async () => {
      let complete = true;
      const [tasks, plants] = await Promise.all([
        // A bounded read (review B1): a request that never answers must end, so `reloading` ends and the lie-fi
        // lock of the sheet lifts; the timeout counts as a network failure (the cache answers, the retry goes on).
        getBedQueue(bedKey, { timeout: SHEET_READ_TIMEOUT_MS }),
        // The sheet lists standing plants: a sown slot (W-015) is not one.
        listPlantStates(bedKey, controller.signal, SHEET_READ_TIMEOUT_MS)
          .then((entries) => entries.filter(isPlantEntry))
          .catch((): null => {
            complete = false;
            return null;
          }),
      ]);
      return { tasks, plants, complete: complete && !controller.signal.aborted };
      // The cache stores only a complete answer, stripped of person data (`storedProjection('bedSheets')`).
    })
      .then(({ data, cachedAt }) => {
        if (!controller.signal.aborted) {
          setLoaded({ bedKey, attempt, state: { status: 'ready', tasks: data.tasks, plants: data.plants, cachedAt } });
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setLoaded({
            bedKey,
            attempt,
            state: { status: 'error', message: parseApiError(error), offlineMiss: isOfflineCacheMiss(error) },
          });
        }
      });
    return () => controller.abort();
  }, [bedKey, scope, attempt, requestLanguage]);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);
  const state = loaded && loaded.bedKey === bedKey ? loaded.state : null;
  const reloading = !(loaded && loaded.bedKey === bedKey && loaded.attempt === attempt);
  return useMemo(() => ({ state: state ?? { status: 'loading' }, reload, reloading }), [state, reload, reloading]);
}
