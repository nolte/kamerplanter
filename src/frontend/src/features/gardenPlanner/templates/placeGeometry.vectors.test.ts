import { describe, expect, it } from 'vitest';
import { loadVectors } from '@/test/gardenPlanVectors';
import type { Geometry, Point } from '../model/types';
import { placeGeometry } from './placeGeometry';

/**
 * The TypeScript port of `place_geometry` (the template ghost, GP-FR-044) runs against the same vector file as the
 * Python reference (`tests/unit/domain/calculators/test_template_placement_vectors.py`, REQ-053 §19.6, #2536). A
 * test that copied the cases inline would certify nothing.
 */
const VECTORS = loadVectors();
const CASES = VECTORS.cases.filter((vector) => vector.operation === 'place_geometry');

/** Numbers within `tolerance`, everything else exact; recurses into arrays and objects. */
function expectClose(actual: unknown, expected: unknown, tolerance: number): void {
  if (typeof expected === 'number') {
    expect(typeof actual).toBe('number');
    expect(Math.abs((actual as number) - expected)).toBeLessThanOrEqual(tolerance);
  } else if (Array.isArray(expected)) {
    expect(Array.isArray(actual)).toBe(true);
    expect((actual as unknown[]).length).toBe(expected.length);
    expected.forEach((item, index) => expectClose((actual as unknown[])[index], item, tolerance));
  } else if (typeof expected === 'object' && expected !== null) {
    expect(typeof actual).toBe('object');
    expect(Object.keys(actual as object).sort()).toEqual(Object.keys(expected).sort());
    for (const [key, value] of Object.entries(expected)) {
      expectClose((actual as Record<string, unknown>)[key], value, tolerance);
    }
  } else {
    expect(actual).toEqual(expected);
  }
}

describe('place_geometry vectors (shared with the Python reference)', () => {
  it('the operation is documented and covers every bed shape', () => {
    expect(VECTORS.operations).toHaveProperty('place_geometry');
    const kinds = new Set(CASES.map((vector) => (vector.input.geometry as Geometry).kind));
    expect(kinds).toEqual(new Set(['rect', 'circle', 'polygon']));
  });

  it.each(CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const { geometry, origin, rotation_deg } = vector.input as {
      geometry: Geometry;
      origin: Point;
      rotation_deg: number;
    };
    const placed = placeGeometry(geometry, origin, rotation_deg);
    expectClose(placed, vector.expected, vector.tolerance ?? VECTORS.default_tolerance);
  });
});
