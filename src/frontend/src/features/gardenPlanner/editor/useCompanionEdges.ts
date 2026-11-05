import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { captureHandledError } from '@/observability/errorTracking';
import { getCompanionEdges, type CompanionEdgeWire, type CompanionEdgesWire } from '../api/companionEdges';
import type { PlanModel } from '../model/planModel';
import type { CompanionLine } from '../renderer/companionLines';
import { markersVisible } from '../renderer/lod';
import { markerIndex } from '../renderer/planIndex';
import type { Viewport } from '../renderer/types';
import { cullBoundsM, intersects } from '../renderer/viewport';

/**
 * The data of the companion-planting layer (REQ-053 GP-FR-134): `GET /locations/{key}/companion-edges` for every
 * bed in `bedKeys` - the caller passes {@link companionBedKeys}, the visible beds at marker LOD - and only while the
 * layer is `enabled`. Each bed is read once and cached; at most `COMPANION_CONCURRENCY` reads run at once and queued
 * beds that leave the view are dropped from the queue, so a pan or a zoom over a big plan starts no request storm.
 * The cache is dropped on `refresh` (a saved plan may have new neighbours), when the site changes and when the layer
 * goes off; every read still on its way is then aborted and its answer ignored. A bed whose read failed keeps no
 * lines and is asked again only when the set of visible beds changes (no retry loop).
 */

/** At most this many bed reads run at once. */
export const COMPANION_CONCURRENCY = 4;

interface BedCache {
  siteKey: string;
  generation: number;
  beds: Readonly<Record<string, CompanionEdgesWire>>;
}

export interface UseCompanionEdges {
  /** The drawable lines of the beds in `bedKeys` (an edge with an unknown position is skipped). */
  lines: readonly CompanionLine[];
  /** The edge behind every line, by line id: what the info card shows. */
  edges: Readonly<Record<string, CompanionEdgeWire>>;
  /** `true` when a bed in view has more pairs than its answer lists. */
  truncated: boolean;
  /** Bed reads started since mount: the fan-out the tests pin. */
  requestCount: () => number;
  /** Drop every answer and read the visible beds again. */
  refresh: () => void;
}

const NO_BEDS: Readonly<Record<string, CompanionEdgesWire>> = {};
const NO_LINES: readonly CompanionLine[] = [];
const NO_EDGES: Readonly<Record<string, CompanionEdgeWire>> = {};

/**
 * The beds whose companion lines can be drawn: in the culled viewport, with two or more positions (an edge needs two
 * occupied slots) and at marker LOD (GP-NFR-067) - below it a bed is a cluster and has no lines to hang them on.
 */
export function companionBedKeys(model: PlanModel, viewport: Viewport): string[] {
  const cull = cullBoundsM(viewport);
  const keys: string[] = [];
  for (const bed of markerIndex(model).values()) {
    if (bed.markers.length < 2 || !model.locations[bed.locationKey]?.geometry) continue;
    if (!intersects(bed.bbox, cull) || !markersVisible(bed.minSpacingM, viewport.pxPerM)) continue;
    keys.push(bed.locationKey);
  }
  return keys;
}

export function lineIdOf(bedKey: string, edge: CompanionEdgeWire): string {
  return `${bedKey}:${edge.slot_a.slot_key}|${edge.slot_b.slot_key}`;
}

/** The lines of the answers of `bedKeys`, in answer order; an edge without both positions cannot be drawn and is skipped. */
export function companionLinesOf(
  beds: Readonly<Record<string, CompanionEdgesWire>>,
  bedKeys: readonly string[],
): { lines: CompanionLine[]; edges: Record<string, CompanionEdgeWire>; truncated: boolean } {
  const lines: CompanionLine[] = [];
  const edges: Record<string, CompanionEdgeWire> = {};
  let truncated = false;
  for (const bedKey of bedKeys) {
    const answer = beds[bedKey];
    if (!answer) continue;
    truncated ||= answer.truncated;
    for (const edge of answer.edges) {
      const a = edge.slot_a.position;
      const b = edge.slot_b.position;
      if (!a || !b) continue;
      const id = lineIdOf(bedKey, edge);
      edges[id] = edge;
      lines.push({ id, a: [a.x, a.y], b: [b.x, b.y], status: edge.status });
    }
  }
  return { lines, edges, truncated };
}

export function useCompanionEdges(siteKey: string, bedKeys: readonly string[], enabled: boolean): UseCompanionEdges {
  const [generation, setGeneration] = useState(0);
  const [cache, setCache] = useState<BedCache>({ siteKey, generation: 0, beds: NO_BEDS });
  const inFlight = useRef(new Map<string, AbortController>());
  const queue = useRef<string[]>([]);
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

  // Off: every read on its way or queued is cancelled and the answers are dropped (a new round).
  useEffect(() => {
    if (!enabled) return undefined;
    return () => {
      abortAll();
      setGeneration((current) => current + 1);
    };
  }, [enabled, abortAll]);

  // Another site, or unmount: the reads of the old site are cancelled.
  useEffect(() => abortAll, [siteKey, abortAll]);

  // A stable signature: panning inside the same set of beds does not re-run the loader.
  const signature = useMemo(() => [...new Set(bedKeys)].sort().join('|'), [bedKeys]);
  const beds = cache.siteKey === siteKey && cache.generation === generation ? cache.beds : NO_BEDS;

  const pump = useCallback(() => {
    const run = (): void => {
      while (inFlight.current.size < COMPANION_CONCURRENCY && queue.current.length > 0) {
        const bedKey = queue.current.shift() as string;
        const controller = new AbortController();
        inFlight.current.set(bedKey, controller);
        requests.current += 1;
        getCompanionEdges(bedKey, controller.signal)
          .then((answer) => {
            if (controller.signal.aborted) return;
            inFlight.current.delete(bedKey);
            setCache((previous) => {
              const same = previous.siteKey === siteKey && previous.generation === generation;
              return { siteKey, generation, beds: { ...(same ? previous.beds : NO_BEDS), [bedKey]: answer } };
            });
            run();
          })
          .catch((error: unknown) => {
            if (controller.signal.aborted) return;
            inFlight.current.delete(bedKey);
            failed.current.add(bedKey);
            // The layer is an enhancement of the plan: a failed bed draws no lines, silently in the UI.
            captureHandledError(error, { area: 'garden-plan-companion-edges', bedKey });
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
    queue.current =
      !enabled || signature === ''
        ? []
        : signature
            .split('|')
            .filter((bedKey) => !(bedKey in beds) && !inFlight.current.has(bedKey) && !failed.current.has(bedKey));
    pump();
  }, [enabled, signature, beds, pump]);

  // Only the beds in view now are drawn: a cached bed that left the view or fell below marker LOD draws nothing.
  const derived = useMemo(() => {
    if (!enabled || beds === NO_BEDS || signature === '') return null;
    return companionLinesOf(beds, signature.split('|'));
  }, [enabled, beds, signature]);
  const requestCount = useCallback(() => requests.current, []);
  return useMemo(
    () => ({
      lines: derived?.lines ?? NO_LINES,
      edges: derived?.edges ?? NO_EDGES,
      truncated: derived?.truncated ?? false,
      requestCount,
      refresh,
    }),
    [derived, requestCount, refresh],
  );
}
