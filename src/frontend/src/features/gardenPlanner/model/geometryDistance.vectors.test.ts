import { describe, expect, it } from 'vitest';
import { parseGeometry } from './geometry';
import { edgeDistanceM, isWaterSource, nearestWaterSourceM } from './geometryDistance';
import type { Geometry } from './types';
import { loadVectors } from '@/test/gardenPlanVectors';

/**
 * The TypeScript port of the edge-to-edge distance runs against the same vector file as the Python reference
 * (`tests/unit/domain/calculators/test_geometry_distance_vectors.py`, REQ-053 GP-FR-167, §19.6). A test that copied
 * the cases inline would certify nothing.
 */
const VECTORS = loadVectors();
const OPERATIONS = ['edge_distance', 'nearest_water_source', 'is_water_source'];
const CASES = VECTORS.cases.filter((vector) => OPERATIONS.includes(vector.operation));
const EDGE_CASES = CASES.filter((vector) => vector.operation === 'edge_distance');

function geometryOf(raw: unknown, id: string): Geometry {
  const geometry = parseGeometry(raw);
  if (geometry === null) throw new Error(`vector geometry does not parse: ${id}`);
  return geometry;
}

function run(id: string, operation: string, input: Record<string, unknown>): number | boolean | null {
  if (operation === 'is_water_source') return isWaterSource(input.object_type as string, input.off_site as boolean);
  if (operation === 'edge_distance') return edgeDistanceM(geometryOf(input.a, id), geometryOf(input.b, id));
  const bed = input.bed === null ? null : geometryOf(input.bed, id);
  const sources = (input.sources as unknown[]).map((raw) => geometryOf(raw, id));
  return nearestWaterSourceM(bed, sources);
}

describe('geometry distance vectors (shared with the Python reference)', () => {
  it('the operations are documented and have cases', () => {
    for (const operation of OPERATIONS) expect(VECTORS.operations).toHaveProperty(operation);
    expect(new Set(CASES.map((vector) => vector.operation))).toEqual(new Set(OPERATIONS));
  });

  it.each(CASES.map((vector) => [vector.id, vector] as const))('%s', (id, vector) => {
    const actual = run(id, vector.operation, vector.input);
    const expected = vector.expected as number | boolean | null;
    const tolerance = vector.tolerance ?? VECTORS.default_tolerance;

    if (expected === null || typeof expected === 'boolean') expect(actual).toBe(expected);
    else expect(Math.abs((typeof actual === 'number' ? actual : Number.NaN) - expected)).toBeLessThanOrEqual(tolerance);
  });

  it.each(EDGE_CASES.map((vector) => [vector.id, vector] as const))('%s is symmetric', (id, vector) => {
    const a = geometryOf(vector.input.a, id);
    const b = geometryOf(vector.input.b, id);
    expect(edgeDistanceM(a, b)).toBe(edgeDistanceM(b, a));
  });
});
