import { describe, expect, it } from 'vitest';
import { computePlantState, type OpenTask } from './plantState';

/**
 * GP-NFR-073: the state of 5 000 plants is computed in <= 50 ms on the client.
 *
 * The wall-clock bound runs only in the benchmark lane, never in the shared CI suite where a loaded runner
 * would make it flaky:
 *
 *     GP_BENCHMARK=1 npx vitest run src/features/gardenPlanner/model/plantState.benchmark.test.ts
 *
 * The always-on test asserts what does not depend on the clock: 5 000 plants produce 5 000 states, each of them
 * the one the same input gives alone (the function is pure, so the batch cannot differ from the single call).
 */
const PLANTS = 5000;
const BUDGET_MS = 50;
const NOW = '2026-06-10T12:00:00Z';

function inputs(index: number) {
  const tasks: OpenTask[] = [
    { category: 'watering', due: index % 3 === 0 ? '2026-06-10' : '2026-06-08' },
    { category: 'pruning', due: '2026-06-20' },
  ];
  return {
    phase: {
      key: `ph_${index % 5}`,
      started_on: '2026-05-01',
      typical_days: 30 + (index % 40),
      allows_harvest: index % 7 === 0,
      is_terminal: false,
    },
    tasks,
    options: { open_findings: index % 11 === 0 ? 1 : 0, frost_risk: index % 13 === 0, harvest_batches: index % 17 === 0 ? 1 : 0, now: NOW },
  };
}

function computeAll(): ReturnType<typeof computePlantState>[] {
  const plant = { kind: 'plant', removed_on: null, termination_type: null } as const;
  return Array.from({ length: PLANTS }, (_, index) => {
    const { phase, tasks, options } = inputs(index);
    return computePlantState(plant, phase, tasks, options);
  });
}

describe('plant state of a large bed', () => {
  it('computes one state per plant, identical to the single call', () => {
    const states = computeAll();
    expect(states).toHaveLength(PLANTS);
    const { phase, tasks, options } = inputs(1234);
    expect(states[1234]).toEqual(
      computePlantState({ kind: 'plant', removed_on: null, termination_type: null }, phase, tasks, options),
    );
    expect(states.some((state) => state.attention.length > 0)).toBe(true);
  });

  it.runIf(process.env.GP_BENCHMARK === '1')(`takes at most ${BUDGET_MS} ms for ${PLANTS} plants`, () => {
    computeAll(); // warm-up
    const start = performance.now();
    computeAll();
    expect(performance.now() - start).toBeLessThanOrEqual(BUDGET_MS);
  });
});
