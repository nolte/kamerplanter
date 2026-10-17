import { describe, expect, it } from 'vitest';
import { largePlan } from '@/test/gardenPlanFixtures';
import { applyOperation } from './applyOperation';
import type { PlanOperation } from './types';

/**
 * GP-ACC-033 (benchmark half): on the "large" class - 150 beds, 300 objects, 3 000 slots, 2 000
 * plants - `applyOperation(move)` run 100 times has a median of <= 1 ms.
 *
 * The 1 ms bound is a wall-clock assertion, so it runs only in the benchmark lane, never in the
 * shared CI suite where a loaded runner would make it flaky:
 *
 *     GP_BENCHMARK=1 npx vitest run src/features/gardenPlanner/model/applyOperation.benchmark.test.ts
 *
 * The always-on test below asserts the part that does not depend on the clock: the 100 moves
 * produce the right plan and leave the untouched entity maps shared (which is *why* the budget
 * holds - a move copies one map of 150 keys, never the 5 000 entities).
 */
const RUNS = 100;
const BENCHMARK_BUDGET_MS = 1;

function moveOps(): PlanOperation[] {
  return Array.from({ length: RUNS }, (_, run) => ({
    op: 'update_geometry',
    entity: 'location',
    key: `loc_${run % 150}`,
    geometry: {
      kind: 'rect',
      origin: [run * 0.1, 2],
      width_m: 1.2,
      length_m: 2,
      rotation_deg: (run * 7) % 360,
    },
  }));
}

describe('applyOperation(move) on a large plan', () => {
  it('moves 100 beds and shares every map it does not touch', () => {
    const start = largePlan();
    let plan = start;
    for (const op of moveOps()) plan = applyOperation(plan, op).plan;
    expect(Object.keys(start.slots)).toHaveLength(3000);
    expect(Object.keys(start.plants)).toHaveLength(2000);
    expect(plan.slots).toBe(start.slots);
    expect(plan.plants).toBe(start.plants);
    expect(plan.gardenObjects).toBe(start.gardenObjects);
    expect(plan.locations.loc_99.geometry).toMatchObject({
      origin: [9.9, 2],
      rotation_deg: 693 % 360,
    });
    expect(start.locations.loc_99.geometry).toMatchObject({ origin: [(99 % 15) * 3, 4 * 6] });
  });

  it.runIf(process.env.GP_BENCHMARK === '1')(
    `has a median of <= ${BENCHMARK_BUDGET_MS} ms (GP-ACC-033)`,
    () => {
      const start = largePlan();
      const ops = moveOps();
      for (const op of ops.slice(0, 20)) applyOperation(start, op); // warm-up
      const samples: number[] = [];
      for (const op of ops) {
        const t0 = performance.now();
        applyOperation(start, op);
        samples.push(performance.now() - t0);
      }
      samples.sort((a, b) => a - b);
      const median = samples[Math.floor(samples.length / 2)];
      console.info(
        `applyOperation(move) median ${median.toFixed(4)} ms, max ${samples[samples.length - 1].toFixed(4)} ms`,
      );
      expect(median).toBeLessThanOrEqual(BENCHMARK_BUDGET_MS);
    },
  );
});
