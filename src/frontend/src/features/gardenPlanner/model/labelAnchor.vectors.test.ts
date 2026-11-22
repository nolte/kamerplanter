import { describe, expect, it } from 'vitest';
import { loadVectors } from '@/test/gardenPlanVectors';
import { parseGeometry } from './geometry';
import { labelAnchor, truncateLabel } from './labelAnchor';
import type { Geometry, Point } from './types';

/**
 * The TypeScript port of `label_anchor` (GP-UX-047, GP-FR-003, #2490) runs against the same vector file as the
 * Python reference (`tests/unit/domain/calculators/test_label_anchor_vectors.py`), so the editor names a bed on the
 * point the PDF does. A test that copied the cases inline would certify nothing.
 */
const VECTORS = loadVectors();
const CASES = VECTORS.cases.filter((vector) => vector.operation === 'label_anchor');
const TRUNCATE_CASES = VECTORS.cases.filter((vector) => vector.operation === 'label_truncate');

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

/** SCR-004: the editor shortens a name where the PDF writer (`plan_svg_engine._truncate`) does - by code points. */
describe('label_truncate vectors (shared with the PDF writer)', () => {
  it('the operation is documented and holds a name outside the BMP', () => {
    expect(VECTORS.operations).toHaveProperty('label_truncate');
    const texts = TRUNCATE_CASES.map((vector) => vector.input.text as string);
    expect(texts.some((text) => Array.from(text).some((char) => (char.codePointAt(0) ?? 0) > 0xffff))).toBe(true);
  });

  it.each(TRUNCATE_CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const { text, max_chars: maxChars } = vector.input as { text: string; max_chars: number };
    expect(truncateLabel(text, maxChars)).toBe(vector.expected);
  });
});
