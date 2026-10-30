import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { captureHandledError } from '@/observability/errorTracking';
import type { PlantMarkerState } from '../renderer/types';
import { listPlantStates, type PlantStateWire } from './plantStateApi';
import { stateInstant, usePlantStateClock } from './plantStateClock';
import { usePlantStateText } from './usePlantStateText';
import { viewsOf } from './usePlantStates';

/**
 * The answers of the beds loaded so far, by bed key. `siteKey` and `generation` tie them to the plan and the load
 * round they belong to: a site change, `refresh`, the foreground or the layer going off start a new round.
 */
interface BedCache {
  siteKey: string;
  generation: number;
  beds: Readonly<Record<string, readonly PlantStateWire[]>>;
}

export interface UsePlanPlantStates {
  /** What the plant-state layer draws, by plant key; empty while the layer is off. */
  states: Readonly<Record<string, PlantMarkerState>>;
  /** Phase names the answers carried, by phase key: they colour and word a phase without another request. */
  phaseNames: Readonly<Record<string, string>>;
  /** Bed loads started since mount (one `listPlantStates` per bed): the fan-out the tests pin. */
  requestCount: () => number;
  /** Drop every answer and load the visible beds again, e.g. after a plan save or a care action. */
  refresh: () => void;
}

/** At most this many bed reads run at once; the rest wait in a FIFO queue (crossing the LOD threshold of a big plan). */
export const PLANT_STATE_CONCURRENCY = 4;

const NO_STATES: Readonly<Record<string, PlantMarkerState>> = {};
const NO_NAMES: Readonly<Record<string, string>> = {};
const NO_BEDS: Readonly<Record<string, readonly PlantStateWire[]>> = {};

/**
 * The plant states of the overview plan (REQ-053 GP-UX-061, #2488): no route of its own - the bed answer
 * (`GET /locations/{key}/plant-states`, ≤ 200 per page) is read for every bed in `visibleBedKeys`, which the caller
 * limits to the beds at marker LOD, and only while the layer is `enabled`. At most `PLANT_STATE_CONCURRENCY` reads
 * run at once, the rest queue in order; queued beds that leave the view are dropped from the queue. Each bed is read
 * once and cached; the cache is dropped on `refresh`, when the page returns to the foreground (GP-FR-191), when the
 * site changes and when the layer goes off, and an answer that arrives after that is ignored. A bed whose read
 * failed keeps its plain markers and is asked again when the set of visible beds changes. The state is computed
 * once per answer and day (GP-NFR-073), never per frame.
 */
export function usePlanPlantStates(
  siteKey: string,
  visibleBedKeys: readonly string[],
  enabled: boolean,
): UsePlanPlantStates {
  const [generation, setGeneration] = useState(0);
  const [cache, setCache] = useState<BedCache>({ siteKey, generation: 0, beds: NO_BEDS });
  const inFlight = useRef(new Map<string, AbortController>());
  const queue = useRef<string[]>([]);
  // A bed whose read failed is not asked again for the same set of visible beds: no retry loop on a broken bed.
  const failed = useRef(new Set<string>());
  const failedFor = useRef('');
  const requests = useRef(0);

  const abortAll = useCallback(() => {
    for (const controller of inFlight.current.values()) controller.abort();
    inFlight.current.clear();
    queue.current = [];
    failed.current.clear();
  }, []);

  const refresh = useCallback(() => {
    abortAll();
    setGeneration((current) => current + 1);
  }, [abortAll]);

  const day = usePlantStateClock(enabled, refresh);

  // Off: everything still on its way or queued is cancelled and the answers are dropped (a new round).
  useEffect(() => {
    if (!enabled) return undefined;
    return () => {
      abortAll();
      setGeneration((current) => current + 1);
    };
  }, [enabled, abortAll]);

  // Another site, or unmount: the reads of the old site are cancelled. The cache belongs to its site, so the new
  // site starts empty without a new round - its first reads start in this same commit and must stay current.
  useEffect(() => abortAll, [siteKey, abortAll]);

  // A stable signature: panning inside the same set of beds does not re-run the loader.
  const signature = useMemo(() => [...new Set(visibleBedKeys)].sort().join('|'), [visibleBedKeys]);
  const beds = cache.siteKey === siteKey && cache.generation === generation ? cache.beds : NO_BEDS;

  // Starts queued reads up to the cap; called when the queue is filled and whenever a read settles.
  const pump = useCallback(() => {
    const run = (): void => {
      while (inFlight.current.size < PLANT_STATE_CONCURRENCY && queue.current.length > 0) {
        const bedKey = queue.current.shift() as string;
        const controller = new AbortController();
        inFlight.current.set(bedKey, controller);
        requests.current += 1;
        listPlantStates(bedKey, controller.signal)
          .then((items) => {
            if (controller.signal.aborted) return;
            inFlight.current.delete(bedKey);
            setCache((previous) => {
              const same = previous.siteKey === siteKey && previous.generation === generation;
              return { siteKey, generation, beds: { ...(same ? previous.beds : NO_BEDS), [bedKey]: items } };
            });
            run();
          })
          .catch((error: unknown) => {
            if (controller.signal.aborted) return;
            inFlight.current.delete(bedKey);
            failed.current.add(bedKey);
            // States are an enhancement of the plan: a failed bed keeps its plain markers, silently in the UI.
            captureHandledError(error, { area: 'garden-plan-plant-states', bedKey });
            run();
          });
      }
    };
    run();
  }, [siteKey, generation]);

  useEffect(() => {
    if (signature !== failedFor.current) {
      failedFor.current = signature;
      failed.current.clear();
    }
    // The queue only ever holds beds that are visible now: a bed that left the view is not read any more.
    queue.current =
      !enabled || signature === ''
        ? []
        : signature
            .split('|')
            .filter((bedKey) => !(bedKey in beds) && !inFlight.current.has(bedKey) && !failed.current.has(bedKey));
    pump();
  }, [enabled, signature, beds, pump]);

  const text = usePlantStateText();
  const views = useMemo(() => {
    if (!enabled || beds === NO_BEDS) return null;
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
