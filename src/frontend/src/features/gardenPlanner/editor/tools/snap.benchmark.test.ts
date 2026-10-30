import { describe, expect, it } from 'vitest';
import { largePlan } from '@/test/gardenPlanFixtures';
import { anchor, boundingBox } from '../../model/geometry';
import type { Point } from '../../model/types';
import { snapCandidates } from '../../renderer/planIndex';
import { moveSources, resolveMoveSnap, resolveSnap, type SnapOptions } from './snap';

/**
 * GP-NFR-034 (drag hot path, #2536): the snap of one pointer move of a drag - all bounding-box corners of the
 * moved bed against the corners and edges of the 450 other objects of the "large" plan - stays a small part of
 * the 16 ms frame. Wall-clock bounds run only in the benchmark lane:
 *
 *     GP_BENCHMARK=1 npx vitest run snap.benchmark
 */
const RUNS = 200;
const BUDGET_MS = 1;

function median(values: number[]): number {
  return [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)];
}

describe.runIf(process.env.GP_BENCHMARK === '1')('snap of a drag on a large plan', () => {
  const model = largePlan();
  const moved = model.locations.loc_0.geometry!;
  const candidates = snapCandidates(model, new Set(['loc_0']));
  const options: SnapOptions = { gridM: 0.1, gridEnabled: true, bypass: false, pxPerM: 40, candidates };
  const reference = anchor(moved);
  const sources = moveSources(boundingBox(moved), reference);
  const rawDelta = (i: number): Point => [(i % 40) * 1.03, Math.floor(i / 40) * 2.07];

  it('resolves the move snap of every bbox corner within budget (median)', () => {
    expect(candidates.corners.length).toBeGreaterThan(1500); // the case is what it claims
    resolveMoveSnap(sources, reference, rawDelta(0), options);
    const times = Array.from({ length: RUNS }, (_, i) => {
      const start = performance.now();
      resolveMoveSnap(sources, reference, rawDelta(i), options);
      return performance.now() - start;
    });
    console.info(`move snap median ${median(times).toFixed(4)} ms`);
    expect(median(times)).toBeLessThanOrEqual(BUDGET_MS);
  });

  it('resolves a single point snap within budget (median)', () => {
    resolveSnap(reference, options);
    const times = Array.from({ length: RUNS }, (_, i) => {
      const delta = rawDelta(i);
      const start = performance.now();
      resolveSnap([reference[0] + delta[0], reference[1] + delta[1]], options);
      return performance.now() - start;
    });
    console.info(`point snap median ${median(times).toFixed(4)} ms`);
    expect(median(times)).toBeLessThanOrEqual(BUDGET_MS);
  });
});
