import { describe, expect, it } from 'vitest';
import { hitTestAll } from './hitTest';
import { largePlacedPlan, NO_SELECTION, viewportAt } from './rendererTestKit';
import { buildScene } from './scene';

/**
 * GP-NFR-034 / GP-NFR-033 (benchmark half): a frame's scene and a hit test on the "large" plan
 * stay far inside the 16 ms frame budget. Wall-clock bounds run only in the benchmark lane, never in
 * the shared CI suite where a loaded runner makes them flaky:
 *
 *     GP_BENCHMARK=1 npx vitest run src/features/gardenPlanner/renderer/renderer.benchmark.test.ts
 *
 * The always-on half (counts, not time) is in `SvgPlanRenderer.test.tsx` (GP-ACC-033).
 */
const RUNS = 100;
const BUDGET_MS = 16;

function median(values: number[]): number {
  return [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)];
}

describe.runIf(process.env.GP_BENCHMARK === '1')('renderer frame cost on a large plan', () => {
  const model = largePlacedPlan();
  const view = (i: number) => viewportAt((i * 0.7) % 60, 30 + (i % 50), 36, 1000, 1000);

  it('builds a scene within one frame (median)', () => {
    buildScene(model, view(0), NO_SELECTION, {}); // warm the model caches, as a mounted editor has
    const times = Array.from({ length: RUNS }, (_, i) => {
      const start = performance.now();
      buildScene(model, view(i), NO_SELECTION, {});
      return performance.now() - start;
    });
    expect(median(times)).toBeLessThanOrEqual(BUDGET_MS);
  });

  it('answers a hit test within one frame (median)', () => {
    hitTestAll(model, view(0), [500, 500]);
    const times = Array.from({ length: RUNS }, (_, i) => {
      const start = performance.now();
      hitTestAll(model, view(i), [500, 500]);
      return performance.now() - start;
    });
    expect(median(times)).toBeLessThanOrEqual(BUDGET_MS);
  });
});
