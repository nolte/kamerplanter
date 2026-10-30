import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { PlantMarkerState } from '../renderer/types';
import { listPlantStates, type PlantStateWire } from './plantStateApi';
import { stateInstant, usePlantStateClock } from './plantStateClock';
import { usePlantStateText } from './usePlantStateText';
import { viewsOf } from './usePlantStates';

/** The answers of the beds loaded so far, by bed key; `siteKey` ties them to the plan they belong to. */
interface BedCache {
  siteKey: string;
  beds: Readonly<Record<string, readonly PlantStateWire[]>>;
}

export interface UsePlanPlantStates {
  /** What the plant-state layer draws, by plant key; empty while the layer is off. */
  states: Readonly<Record<string, PlantMarkerState>>;
  /** Phase names the answers carried, by phase key: they colour and word a phase without another request. */
  phaseNames: Readonly<Record<string, string>>;
  /** Bed loads started since mount (one `listPlantStates` per bed): the fan-out the tests pin. */
  requestCount: () => number;
  /** Drop every answer and load the visible beds again, e.g. after a care action. */
  refresh: () => void;
}

const NO_STATES: Readonly<Record<string, PlantMarkerState>> = {};
const NO_NAMES: Readonly<Record<string, string>> = {};

/**
 * The plant states of the overview plan (REQ-053 GP-UX-061, #2488): no route of its own - the bed answer
 * (`GET /locations/{key}/plant-states`, ≤ 200 per page) is read for every bed in `visibleBedKeys`, which the caller
 * limits to the beds at marker LOD, and only while the layer is `enabled`. Each bed is read once and cached; the
 * cache is dropped when the page returns to the foreground (GP-FR-191) and when the layer goes off, and an answer
 * that arrives after that is ignored. The state is computed once per answer and day (GP-NFR-073), never per frame.
 */
export function usePlanPlantStates(
  siteKey: string,
  visibleBedKeys: readonly string[],
  enabled: boolean,
): UsePlanPlantStates {
  const [cache, setCache] = useState<BedCache>({ siteKey, beds: {} });
  const inFlight = useRef(new Map<string, AbortController>());
  // A bed whose read failed is not asked again until the cache is dropped: no retry loop on a broken bed.
  const failed = useRef(new Set<string>());
  const requests = useRef(0);

  const abortAll = useCallback(() => {
    for (const controller of inFlight.current.values()) controller.abort();
    inFlight.current.clear();
    failed.current.clear();
  }, []);

  const refresh = useCallback(() => {
    abortAll();
    setCache((previous) => ({ siteKey: previous.siteKey, beds: {} }));
  }, [abortAll]);

  const day = usePlantStateClock(enabled, refresh);

  // Off, or another site: everything still on its way is cancelled and the answers are dropped.
  useEffect(() => {
    if (!enabled) return undefined;
    return () => {
      abortAll();
      setCache({ siteKey, beds: {} });
    };
  }, [enabled, siteKey, abortAll]);

  // A stable signature: panning inside the same set of beds does not re-run the loader.
  const signature = useMemo(() => [...new Set(visibleBedKeys)].sort().join('|'), [visibleBedKeys]);
  const beds = cache.siteKey === siteKey ? cache.beds : null;

  useEffect(() => {
    if (!enabled || beds === null || signature === '') return;
    for (const bedKey of signature.split('|')) {
      if (bedKey in beds || inFlight.current.has(bedKey) || failed.current.has(bedKey)) continue;
      const controller = new AbortController();
      inFlight.current.set(bedKey, controller);
      requests.current += 1;
      listPlantStates(bedKey, controller.signal)
        .then((items) => {
          if (controller.signal.aborted) return;
          inFlight.current.delete(bedKey);
          setCache((previous) =>
            previous.siteKey === siteKey ? { siteKey, beds: { ...previous.beds, [bedKey]: items } } : previous,
          );
        })
        .catch(() => {
          // States are an enhancement of the plan: a failed bed keeps its plain markers.
          if (controller.signal.aborted) return;
          inFlight.current.delete(bedKey);
          failed.current.add(bedKey);
        });
    }
  }, [enabled, siteKey, signature, beds]);

  // Unmount: nothing may land in a gone component.
  useEffect(() => abortAll, [abortAll]);

  const text = usePlantStateText();
  const views = useMemo(() => {
    if (!enabled || beds === null) return null;
    // `day` is the clock: the states are computed when an answer or the day changes, not per frame.
    const now = stateInstant(day);
    return Object.values(beds).flatMap((items) => Object.values(viewsOf(items, now)));
  }, [enabled, beds, day]);
  const states = useMemo(
    () =>
      views && views.length > 0
        ? Object.fromEntries(views.map((view): [string, PlantMarkerState] => [view.plant_key, text.marker(view)]))
        : NO_STATES,
    [views, text],
  );
  const phaseNames = useMemo(() => {
    if (!views || views.length === 0) return NO_NAMES;
    const named: Record<string, string> = {};
    for (const view of views) {
      if (view.phase?.name) named[view.phase.key] = view.phase.name;
    }
    return named;
  }, [views]);
  const requestCount = useCallback(() => requests.current, []);
  return useMemo(
    () => ({ states, phaseNames, requestCount, refresh }),
    [states, phaseNames, requestCount, refresh],
  );
}
