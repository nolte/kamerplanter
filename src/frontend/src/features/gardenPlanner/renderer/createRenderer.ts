/**
 * The one place that picks a plan renderer (REQ-053 D-01, GP-NFR-009): SVG for every plan, Konva for a plan with at
 * least {@link KONVA_MIN_PLAN_OBJECTS} objects. The Konva renderer is its own chunk (GP-NFR-003: ≤ 200 KB gzip, only
 * for this chunk) and loads only when such a plan opens; until it is there - and for good when it fails to load - the
 * plan is drawn by SVG, so a plan never waits for, or breaks on, the second renderer.
 */
import { useEffect, useMemo, useState } from 'react';
import type { PlanModel } from '../model/planModel';
import { SvgPlanRenderer } from './SvgPlanRenderer';
import type { PlanRenderer } from './types';

/**
 * From this many plan objects (beds and other locations + garden objects + slots, i.e. markers) the plan is drawn by
 * Konva. WP 9.6 (`.audits/req-053/renderer-measurement-2026-11-08.md`) measured the SVG renderer's drag frame time on
 * two plans and both missed GP-NFR-033 on every profile: the smaller one, 30 beds with 3 000 slots (3 030 objects),
 * at p95 33.4 ms on the laptop (budget 16) and 183.3 ms on the phone profile (budget 33); the "large" class (5 250
 * objects) at 50.1 ms and 666.7 ms. 3 000 is therefore the lowest measured count at which SVG fails the budget, and it
 * is also the count D-01/GP-NFR-013 names. No plan below it was measured, so below it SVG stays - the renderer that
 * carries the full DOM semantics.
 */
export const KONVA_MIN_PLAN_OBJECTS = 3000;

export type RendererKind = 'svg' | 'konva';

/** What decides the renderer: every drawable object the plan stores, culled or not. */
export function planObjectCount(model: PlanModel | null | undefined): number {
  if (!model) return 0;
  return (
    Object.keys(model.locations).length + Object.keys(model.gardenObjects).length + Object.keys(model.slots).length
  );
}

export function rendererKindFor(objectCount: number): RendererKind {
  return objectCount >= KONVA_MIN_PLAN_OBJECTS ? 'konva' : 'svg';
}

export function createSvgRenderer(): PlanRenderer {
  return new SvgPlanRenderer();
}

/** Loads the Konva chunk and builds its renderer; a test injects its own. */
export type KonvaRendererLoader = () => Promise<PlanRenderer>;

export const loadKonvaRenderer: KonvaRendererLoader = () =>
  import('./KonvaPlanRenderer').then(({ KonvaPlanRenderer }) => new KonvaPlanRenderer());

/**
 * The renderer for `model`. SVG at once; once the plan reaches the threshold the Konva chunk loads and its renderer
 * takes over. The choice is latched: a plan that shrinks below the threshold while open keeps Konva, so an edit never
 * swaps the drawing surface back and forth. A chunk that fails to load leaves the plan on SVG.
 */
export function usePlanRenderer(
  model: PlanModel | null | undefined,
  loader: KonvaRendererLoader = loadKonvaRenderer,
): PlanRenderer {
  const svg = useMemo(() => createSvgRenderer(), []);
  const [konvaWanted, setKonvaWanted] = useState(false);
  const [konva, setKonva] = useState<PlanRenderer | null>(null);
  const wanted = rendererKindFor(planObjectCount(model)) === 'konva';
  if (wanted && !konvaWanted) setKonvaWanted(true);

  useEffect(() => {
    if (!konvaWanted) return;
    let alive = true;
    loader().then(
      (renderer) => {
        if (alive) setKonva(renderer);
      },
      (error: unknown) => {
        // The SVG renderer stays: slower on this plan, but complete.
        console.warn('[garden-plan] the Konva renderer did not load; the plan stays on SVG', error);
      },
    );
    return () => {
      alive = false;
    };
  }, [konvaWanted, loader]);

  return konva ?? svg;
}
