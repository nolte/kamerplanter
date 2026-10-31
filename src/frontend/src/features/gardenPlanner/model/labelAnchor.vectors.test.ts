import { describe, expect, it } from 'vitest';
import { loadVectors } from '@/test/gardenPlanVectors';
import { parseGeometry } from './geometry';
import { labelAnchor } from './labelAnchor';
import type { Geometry, Point } from './types';

/**
 * The TypeScript port of `label_anchor` (GP-UX-047, GP-FR-003, #2490) runs against the same vector file as the
 * Python reference (`tests/unit/domain/calculators/test_label_anchor_vectors.py`), so the editor names a bed on the
 * point the PDF does. A test that copied the cases inline would certify nothing.
 */
const VECTORS = loadVectors();
const CASES = VECTORS.cases.filter((vector) => vector.operation === 'label_anchor');

describe('label_anchor vectors (shared with the Python reference)', () => {
  it('the operation is documented and covers every geometry kind', () => {
    expect(VECTORS.operations).toHaveProperty('label_anchor');
    const kinds = new Set(CASES.map((vector) => (vector.input.geometry as Geometry).kind));
    expect(kinds).toEqual(new Set(['rect', 'circle', 'polygon', 'polyline', 'point']));
  });

  it.each(CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const geometry = parseGeometry(vector.input.geometry);
    if (geometry === null) throw new Error(`vector geometry does not parse: ${vector.id}`);
    const expected = vector.expected as { point: Point; width_m: number };
    const tolerance = vector.tolerance ?? VECTORS.default_tolerance;

    const actual = labelAnchor(geometry);

    expect(Object.keys(expected).sort()).toEqual(['point', 'width_m']);
    expect(Math.abs(actual.point[0] - expected.point[0])).toBeLessThanOrEqual(tolerance);
    expect(Math.abs(actual.point[1] - expected.point[1])).toBeLessThanOrEqual(tolerance);
    expect(Math.abs(actual.widthM - expected.width_m)).toBeLessThanOrEqual(tolerance);
  });
});
