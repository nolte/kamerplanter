import { describe, expect, it } from 'vitest';
import { parseGeometry } from './geometry';
import { edgeDistanceM, nearestWaterSourceM, waterSourceGeometries } from './geometryDistance';
import type { GardenObject, Geometry } from './types';
import { loadVectors } from '@/test/gardenPlanVectors';

/**
 * The TypeScript port of the edge-to-edge distance runs against the same vector file as the Python reference
 * (`tests/unit/domain/calculators/test_geometry_distance_vectors.py`, REQ-053 GP-FR-167, §19.6). A test that copied
 * the cases inline would certify nothing.
 */
const VECTORS = loadVectors();
const OPERATIONS = ['edge_distance', 'nearest_water_source'];
const CASES = VECTORS.cases.filter((vector) => OPERATIONS.includes(vector.operation));
const EDGE_CASES = CASES.filter((vector) => vector.operation === 'edge_distance');

function geometryOf(raw: unknown, id: string): Geometry {
  const geometry = parseGeometry(raw);
  if (geometry === null) throw new Error(`vector geometry does not parse: ${id}`);
  return geometry;
}

function run(id: string, operation: string, input: Record<string, unknown>): number | null {
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
    const expected = vector.expected as number | null;
    const tolerance = vector.tolerance ?? VECTORS.default_tolerance;

    if (expected === null) expect(actual).toBeNull();
    else expect(Math.abs((actual ?? Number.NaN) - expected)).toBeLessThanOrEqual(tolerance);
  });

  it.each(EDGE_CASES.map((vector) => [vector.id, vector] as const))('%s is symmetric', (id, vector) => {
    const a = geometryOf(vector.input.a, id);
    const b = geometryOf(vector.input.b, id);
    expect(edgeDistanceM(a, b)).toBe(edgeDistanceM(b, a));
  });
});

describe('waterSourceGeometries (GP-FR-167)', () => {
  const object = (key: string, objectType: string, offSite = false): GardenObject =>
    ({
      key,
      site_key: 'site_1',
      object_type: objectType,
      label: key,
      geometry: { kind: 'point', origin: [1, 1] },
      props: {},
      off_site: offSite,
      locked: false,
      z_order: 0,
    }) as unknown as GardenObject;

  it('keeps the water sources of the garden and leaves out scenery outside the boundary and other objects', () => {
    const sources = waterSourceGeometries([
      object('tap', 'water_source'),
      object('neighbour', 'water_source', true),
      object('tree', 'tree'),
    ]);
    expect(sources).toHaveLength(1);
  });
});
