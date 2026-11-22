import { act, render, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { PlanSlot } from '../model/types';
import {
  KONVA_MIN_PLAN_OBJECTS,
  loadKonvaRenderer,
  planObjectCount,
  rendererKindFor,
  usePlanRenderer,
  type KonvaRendererLoader,
} from './createRenderer';
import { HeadlessPlanRenderer } from './HeadlessPlanRenderer';
import { PlaceholderPlanRenderer } from './PlaceholderPlanRenderer';
import { KonvaPlanRenderer } from './KonvaPlanRenderer';
import { TEST_LABELS, bed, gardenObject, normalizePlan, planResponse, type PlanModel } from './rendererTestKit';
import { SvgPlanRenderer } from './SvgPlanRenderer';
import type { PlanRenderer } from './types';

/** A plan of `beds` beds, `objects` garden objects and `slots` slots. */
function planOf(beds: number, objects: number, slots: number): PlanModel {
  const slotList: PlanSlot[] = Array.from({ length: slots }, (_, i) => ({
    key: `s${i}`,
    slot_id: `S${i}`,
    location_key: 'b0',
    plan_geometry: { origin: [0.1 + (i % 10) * 0.1, 0.1 + Math.floor(i / 10) * 0.01] },
  }));
  return normalizePlan(
    planResponse({
      locations: Array.from({ length: beds }, (_, i) => bed(`b${i}`, i * 2, 0)),
      garden_objects: Array.from({ length: objects }, (_, i) => gardenObject(`g${i}`, i * 3, 20)),
      slots: slotList,
      plants: [],
    }),
  );
}

describe('renderer choice by plan size (D-01, WP 9.6 threshold)', () => {
  it('counts beds, garden objects and slots', () => {
    expect(planObjectCount(planOf(30, 2, 3000))).toBe(3032);
    expect(planObjectCount(null)).toBe(0);
  });

  it('switches to Konva at 3 000 objects: the smallest plan WP 9.6 measured over the drag budget', () => {
    expect(KONVA_MIN_PLAN_OBJECTS).toBe(3000);
    expect(rendererKindFor(KONVA_MIN_PLAN_OBJECTS - 1)).toBe('svg');
    expect(rendererKindFor(KONVA_MIN_PLAN_OBJECTS)).toBe('konva');
    // The measured plans: 30 beds x 100 slots (3 030) and the "large" class 250 x 20 (5 250).
    expect(rendererKindFor(planObjectCount(planOf(30, 0, 3000)))).toBe('konva');
    expect(rendererKindFor(planObjectCount(planOf(30, 0, 2969)))).toBe('svg');
  });

  it('builds the real Konva renderer from its chunk', async () => {
    expect(await loadKonvaRenderer()).toBeInstanceOf(KonvaPlanRenderer);
  });
});

describe('usePlanRenderer', () => {
  const small = planOf(2, 0, 10);
  const large = planOf(30, 0, 3000);

  it('draws a small plan with SVG and never loads the Konva chunk', () => {
    const loader = vi.fn<KonvaRendererLoader>();
    const { result, rerender } = renderHook(({ model }) => usePlanRenderer(model, undefined, loader), {
      initialProps: { model: small as PlanModel | null },
    });
    expect(result.current).toBeInstanceOf(SvgPlanRenderer);
    const first = result.current;
    rerender({ model: null });
    expect(result.current).toBe(first);
    expect(loader).not.toHaveBeenCalled();
  });

  it('starts on a placeholder, then hands a large plan to the loaded renderer and keeps it when the plan shrinks', async () => {
    const konva: PlanRenderer = new HeadlessPlanRenderer();
    const loader = vi.fn<KonvaRendererLoader>(() => Promise.resolve(konva));
    const { result, rerender } = renderHook(({ model }) => usePlanRenderer(model, undefined, loader), {
      initialProps: { model: large },
    });
    // No throwaway SVG drawing of a large plan: a placeholder holds its place until the chunk is there.
    expect(result.current).toBeInstanceOf(PlaceholderPlanRenderer);
    await waitFor(() => expect(result.current).toBe(konva));
    rerender({ model: small });
    expect(result.current).toBe(konva); // latched: an edit never swaps the surface back
    expect(loader).toHaveBeenCalledTimes(1);
  });

  it('keeps the renderer a plan opened with when an edit takes it across the threshold (no swap mid-session)', () => {
    const loader = vi.fn<KonvaRendererLoader>(() => Promise.resolve(new HeadlessPlanRenderer()));
    const { result, rerender } = renderHook(({ model }) => usePlanRenderer(model, undefined, loader), {
      initialProps: { model: small },
    });
    const svg = result.current;
    expect(svg).toBeInstanceOf(SvgPlanRenderer);
    rerender({ model: large }); // same site, grown past 3 000 objects by an edit
    expect(result.current).toBe(svg);
    expect(loader).not.toHaveBeenCalled();
  });

  it('decides afresh for another plan in the same mounted page, but never swaps on an edit of the same one', async () => {
    const konva: PlanRenderer = new HeadlessPlanRenderer();
    const loader = vi.fn<KonvaRendererLoader>(() => Promise.resolve(konva));
    const otherSmall = normalizePlan(planResponse({ ...planResponse(), site_key: 'site_2', slots: [], plants: [] }));
    const { result, rerender } = renderHook(({ model }) => usePlanRenderer(model, undefined, loader), {
      initialProps: { model: large },
    });
    await waitFor(() => expect(result.current).toBe(konva));
    rerender({ model: small }); // same site, smaller after an edit
    expect(result.current).toBe(konva);
    rerender({ model: otherSmall }); // the route's `:key` changed: a small site
    expect(result.current).toBeInstanceOf(SvgPlanRenderer);
    rerender({ model: large }); // back to the large site: opened again, decided again
    expect(result.current).toBe(konva);
  });

  it('decides afresh on a new load of the same plan, and keeps the choice while that load is under way', async () => {
    const konva: PlanRenderer = new HeadlessPlanRenderer();
    const loader = vi.fn<KonvaRendererLoader>(() => Promise.resolve(konva));
    const { result, rerender } = renderHook(({ model, identity }) => usePlanRenderer(model, identity, loader), {
      initialProps: { model: small, identity: 'site_1#r1' as string | null },
    });
    const svg = result.current;
    expect(svg).toBeInstanceOf(SvgPlanRenderer);
    rerender({ model: large, identity: 'site_1#r1' }); // an edit of the opened plan: no swap
    expect(result.current).toBe(svg);
    rerender({ model: small, identity: null }); // a reload under way still shows the old plan
    expect(result.current).toBe(svg);
    rerender({ model: large, identity: 'site_1#r2' }); // the reload brought 3 000+ objects (an import)
    await waitFor(() => expect(result.current).toBe(konva));
    rerender({ model: small, identity: 'site_1#r2' }); // edited below the threshold: still no swap
    expect(result.current).toBe(konva);
    rerender({ model: small, identity: null }); // the next reload under way, the edited plan still shown: no swap
    expect(result.current).toBe(konva);
  });

  it('stays on SVG when the Konva chunk fails to load', async () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    const failure = new Error('chunk load failed');
    const loader = vi.fn<KonvaRendererLoader>(() => Promise.reject(failure));
    const { result } = renderHook(() => usePlanRenderer(large, undefined, loader));
    expect(result.current).toBeInstanceOf(PlaceholderPlanRenderer);
    await waitFor(() => expect(warn).toHaveBeenCalledWith(expect.stringContaining('stays on SVG'), failure));
    await act(async () => undefined);
    expect(result.current).toBeInstanceOf(SvgPlanRenderer);
    expect(loader).toHaveBeenCalledTimes(1);
    warn.mockRestore();
  });
});

describe('PlaceholderPlanRenderer', () => {
  it('holds the plan its size while the Konva chunk loads, busy and named, and still hit-tests by the model', () => {
    const placeholder = new PlaceholderPlanRenderer();
    const viewport = { originM: [0, 10] as [number, number], pxPerM: 100, widthPx: 800, heightPx: 600 };
    const { getByTestId } = render(
      <>{placeholder.render(planOf(1, 0, 0), viewport, { selectedKeys: new Set() }, { labels: TEST_LABELS })}</>,
    );
    const node = getByTestId('garden-plan-renderer-loading');
    expect(node).toHaveAttribute('aria-busy', 'true');
    expect(node).toHaveAttribute('aria-label', 'Plan');
    expect(document.querySelector('[data-testid="garden-plan-svg"]')).toBeNull(); // no throwaway SVG drawing
    expect(placeholder.hitTest([60, 900])).toBe('b0'); // bed b0 at (0, 0), 1.2 x 2 m
  });
});
