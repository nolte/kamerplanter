import { describe, expect, it } from 'vitest';
import {
  ATTENTION_PRIORITY,
  LIFECYCLES,
  computePlantState,
  type OpenTask,
  type PhaseFacts,
  type PlantFacts,
} from './plantState';
import { loadVectors, type VectorCase } from '@/test/gardenPlanVectors';

/**
 * The TypeScript port of the plant state runs against the same vector file as the Python reference
 * (`tests/unit/domain/calculators/test_plant_state_vectors.py`, REQ-053 §19.6, GP-ACC-050). A test that
 * copied the cases inline would certify nothing.
 */
const VECTORS = loadVectors();
const CASES = VECTORS.cases.filter((vector) => vector.operation === 'plant_state');

interface PlantStateInput {
  now: string;
  plant: PlantFacts;
  phase: PhaseFacts | null;
  tasks: OpenTask[];
  open_findings: number;
  frost_risk: boolean;
  harvest_batches: number;
}

function run(vector: VectorCase) {
  const input = vector.input as unknown as PlantStateInput;
  return computePlantState(input.plant, input.phase, input.tasks, {
    open_findings: input.open_findings,
    frost_risk: input.frost_risk,
    harvest_batches: input.harvest_batches,
    now: input.now,
  });
}

function expectClose(actual: unknown, expected: unknown, tolerance: number, path = ''): void {
  if (typeof expected === 'number' && !Number.isInteger(expected)) {
    expect(typeof actual, path).toBe('number');
    expect(Math.abs((actual as number) - expected), path).toBeLessThanOrEqual(tolerance);
  } else if (Array.isArray(expected)) {
    expect(Array.isArray(actual), path).toBe(true);
    expect((actual as unknown[]).length, path).toBe(expected.length);
    expected.forEach((item, index) =>
      expectClose((actual as unknown[])[index], item, tolerance, `${path}[${index}]`),
    );
  } else if (expected !== null && typeof expected === 'object') {
    const keys = Object.keys(expected);
    expect(Object.keys(actual as object).sort(), path).toEqual(keys.sort());
    for (const key of keys) {
      expectClose(
        (actual as Record<string, unknown>)[key],
        (expected as Record<string, unknown>)[key],
        tolerance,
        `${path}.${key}`,
      );
    }
  } else {
    expect(actual, path).toEqual(expected);
  }
}

describe('plant state calculator against the shared vectors', () => {
  it('finds the operation in the vector file', () => {
    expect(VECTORS.operations).toHaveProperty('plant_state');
    expect(CASES.length).toBeGreaterThanOrEqual(20);
  });

  it.each(CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    expectClose(run(vector), vector.expected, vector.tolerance ?? VECTORS.default_tolerance);
  });

  it('exercises every lifecycle and every attention reason', () => {
    const expected = CASES.map((vector) => vector.expected as ReturnType<typeof run>);
    expect(new Set(expected.map((state) => state.lifecycle))).toEqual(new Set(LIFECYCLES));
    expect(new Set(expected.flatMap((state) => state.attention.map((item) => item.reason)))).toEqual(
      new Set(ATTENTION_PRIORITY),
    );
  });

  it('GP-ACC-050 stated from the spec: a flowering plant with two overdue tasks and an open finding', () => {
    const state = computePlantState(
      { kind: 'plant', removed_on: null, termination_type: null },
      { key: 'bloom', started_on: '2026-05-01', typical_days: 60, allows_harvest: false, is_terminal: false },
      [
        { category: 'watering', due: '2026-06-01' },
        { category: 'pruning', due: '2026-06-02' },
      ],
      { open_findings: 1, frost_risk: false, harvest_batches: 0, now: '2026-06-10T08:00:00Z' },
    );
    expect(state.lifecycle).toBe('active');
    expect(state.attention.map((item) => item.reason)).toEqual(['problem', 'overdue']);
  });
});
