import { useCallback, useEffect, useMemo, useState } from 'react';
import { getGardenPlan } from '../api/gardenPlan';
import type { PlanLocation } from '../model/types';
import { listZones } from './zonesApi';
import type { IrrigationZone, PlanZone } from './zoneTypes';

export type ZoneLoadStatus = 'seeded' | 'loading' | 'ready' | 'error';

export interface UseIrrigationZones {
  /** The zones of the site: the plan's own list until the first answer of the zone endpoint, then that answer. */
  zones: readonly PlanZone[];
  /** The full records (with the HA flag) once the endpoint answered; empty before. */
  records: readonly IrrigationZone[];
  status: ZoneLoadStatus;
  reload: () => void;
}

/**
 * The irrigation zones of a site. The plan response already carries them (`include=zones`), so the zone layer
 * needs no request at all; the endpoint is read once the panel opens or after a change (`reload`), and a failed
 * read keeps the plan's list on screen (the layer is an enhancement of the plan, never a reason for it to fail).
 */
export function useIrrigationZones(
  siteKey: string,
  seed: readonly PlanZone[],
  fetchEnabled: boolean,
): UseIrrigationZones {
  const [answer, setAnswer] = useState<{ siteKey: string; items: IrrigationZone[] } | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  // The last `attempt` whose read finished (answered or failed).
  const [settledAttempt, setSettledAttempt] = useState(0);
  // A reload asked for after a write is finished even when the panel closes meanwhile: the hatch, the legend and
  // the bed info read this list too, and would otherwise keep the old assignment until the panel opens again.
  // Only a change of site or the unmount aborts it.
  const pendingReload = attempt > settledAttempt;
  const wanted = fetchEnabled || pendingReload;

  useEffect(() => {
    if (!wanted) return undefined;
    const abort = new AbortController();
    listZones(siteKey, abort.signal)
      .then((items) => {
        if (abort.signal.aborted) return;
        setAnswer({ siteKey, items });
        setFailed(false);
        setSettledAttempt(attempt);
      })
      .catch(() => {
        if (abort.signal.aborted) return;
        setFailed(true);
        setSettledAttempt(attempt);
      });
    return () => abort.abort();
  }, [siteKey, wanted, attempt]);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);
  const records = useMemo(() => (answer?.siteKey === siteKey ? answer.items : []), [answer, siteKey]);
  const ready = answer?.siteKey === siteKey;
  return useMemo(
    () => ({
      zones: ready ? records : seed,
      records,
      status: failed ? 'error' : ready ? 'ready' : fetchEnabled ? 'loading' : 'seeded',
      reload,
    }),
    [ready, records, seed, failed, fetchEnabled, reload],
  );
}

/**
 * Last watering per bed (ISO instant by bed key). The loaded plan has it already; after a watering round the
 * plan is read again (`include=tasks` carries `last_watered_at`) so the layer follows without a reload of the page.
 */
export function useLastWatered(
  siteKey: string,
  locations: Readonly<Record<string, PlanLocation>>,
  refreshToken: number,
): Readonly<Record<string, string | null | undefined>> {
  const [fresh, setFresh] = useState<{ token: number; siteKey: string; byBed: Record<string, string | null> } | null>(
    null,
  );

  useEffect(() => {
    if (refreshToken === 0) return undefined;
    const abort = new AbortController();
    getGardenPlan(siteKey, ['tasks'])
      .then((plan) => {
        if (abort.signal.aborted) return;
        const byBed: Record<string, string | null> = {};
        for (const location of plan.locations) byBed[location.key] = location.last_watered_at ?? null;
        setFresh({ token: refreshToken, siteKey, byBed });
      })
      .catch(() => {
        // The layer keeps the numbers it had; they only age by a day at most.
      });
    return () => abort.abort();
  }, [siteKey, refreshToken]);

  return useMemo(() => {
    if (fresh && fresh.siteKey === siteKey) return fresh.byBed;
    const byBed: Record<string, string | null> = {};
    for (const location of Object.values(locations)) byBed[location.key] = location.last_watered_at ?? null;
    return byBed;
  }, [fresh, siteKey, locations]);
}
