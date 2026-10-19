import { describe, expect, it } from 'vitest';
import { parseGeometry } from './geometry';
import { computeLayout, type EntryLayout } from './layout';

/**
 * GP-NFR-036 / GP-NFR-040 (benchmark half): the layout preview of 200 positions in a polygon bed takes
 * <= 50 ms on the client (the Python reference has <= 100 ms server side, see
 * `test_plan_calculators_benchmark.py`). Judged on the median of 100 runs after a warm-up, like the
 * `applyOperation` benchmark.
 *
 * The wall-clock bound runs only in the benchmark lane (`npm run test:bench`, the `Garden planner
 * benchmarks` job), never in the shared suite where a loaded runner would make it flaky. The always-on test
 * asserts what does not depend on the clock: the layout really is 200 positions, all inside the bed - a
 * benchmark of a layout that returned early would pass at any speed.
 */
const RUNS = 100;
const BUDGET_MS = 50;
const POSITIONS = 200;

const BED = parseGeometry(
  {
    kind: 'polygon',
    points: [
      [0, 0],
      [10, 0],
      [10, 6],
      [6, 10],
      [0, 10],
    ],
  },
  'plan',
);
const ENTRY: EntryLayout = { layout_strategy: 'grid', spacing_cm: 60 };

function layout() {
  if (BED === null) throw new Error('the benchmark bed does not parse');
  return computeLayout(BED, ENTRY, POSITIONS);
}

describe('computeLayout of 200 positions in a polygon bed', () => {
  it('returns exactly 200 positions inside the bed', () => {
    const result = layout();
    expect(result.count).toBe(POSITIONS);
    const points = result.slots.flatMap((slot) => (slot.point ? [slot.point] : []));
    expect(points).toHaveLength(POSITIONS);
    // The bed's right-hand edge cuts the corner from (10, 6) to (6, 10): x + y <= 16.
    expect(points.every(([x, y]) => x > 0 && y > 0 && x < 10 && y < 10 && x + y <= 16)).toBe(true);
  });

  it.runIf(process.env.GP_BENCHMARK === '1')(
    `has a median of <= ${BUDGET_MS} ms (GP-NFR-036)`,
    () => {
      for (let warm = 0; warm < 10; warm += 1) layout();
      const samples: number[] = [];
      for (let run = 0; run < RUNS; run += 1) {
        const start = performance.now();
        layout();
        samples.push(performance.now() - start);
      }
      samples.sort((a, b) => a - b);
      const median = samples[Math.floor(samples.length / 2)];
      console.info(
        `computeLayout(200) median ${median.toFixed(3)} ms, max ${samples[samples.length - 1].toFixed(3)} ms`,
      );
      expect(median).toBeLessThanOrEqual(BUDGET_MS);
    },
  );
});
