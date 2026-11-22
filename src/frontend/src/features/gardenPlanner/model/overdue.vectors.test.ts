import { describe, expect, it } from 'vitest';
import { isOverdue } from './overdue';
import { loadVectors } from '@/test/gardenPlanVectors';

/**
 * The TypeScript twin of the overdue rule runs against the same vector file as the Python reference
 * (`tests/unit/domain/calculators/test_overdue_vectors.py`, #2461).
 */
const VECTORS = loadVectors();
const CASES = VECTORS.cases.filter((vector) => vector.operation === 'overdue');

describe('overdue vectors', () => {
  it('carries the operation and the boundary cases', () => {
    expect(VECTORS.operations).toHaveProperty('overdue');
    const ids = CASES.map((vector) => vector.id);
    expect(ids).toEqual(
      expect.arrayContaining(['overdue-due-today-0000', 'overdue-due-today-2359', 'overdue-due-yesterday-2359']),
    );
  });

  it.each(CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const input = vector.input as { now: string; due: string | null };
    expect(isOverdue(input.due, input.now)).toBe(vector.expected);
  });
});
