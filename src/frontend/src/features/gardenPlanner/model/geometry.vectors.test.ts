import { describe, expect, it } from 'vitest';
import {
  areaM2,
  boundingBox,
  centroid,
  contains,
  isSimplePolygon,
  overlaps,
  parseGeometry,
  shoelaceArea,
  toLocalShape,
  toShape,
  transformBedToPlan,
  transformPlanToBed,
  validateGeometry,
  type GeometryFrame,
} from './geometry';
import type { Point } from './types';
import { loadVectors, type VectorCase } from '@/test/gardenPlanVectors';

/**
 * The TypeScript port runs against the same vector file as the Python reference
 * (`tests/unit/domain/calculators/test_geometry_vectors.py`, REQ-053 §19.6). A test that copied the
 * cases inline would certify nothing.
 */
const ALL_VECTORS = loadVectors();
/** The planting-layout operations run in `layout.vectors.test.ts`; `adjacency` is derived server-side only (WP 3.3); `plant_state` runs in `plantState.vectors.test.ts`; `site_fit` runs in `siteFit.vectors.test.ts`; `overdue` runs in `overdue.vectors.test.ts`. */
const LAYOUT_OPERATIONS = new Set(['layout', 'layout_error', 'adjacency', 'plant_state', 'site_fit', 'overdue']);
const VECTORS = {
  ...ALL_VECTORS,
  cases: ALL_VECTORS.cases.filter((vector) => !LAYOUT_OPERATIONS.has(vector.operation)),
};

type Input = Record<string, unknown>;

function parsed(raw: unknown, frame: GeometryFrame = 'plan') {
  const geometry = parseGeometry(raw, frame);
  if (geometry === null) throw new Error(`vector geometry does not parse: ${JSON.stringify(raw)}`);
  return geometry;
}

function expectClose(actual: unknown, expected: unknown, tolerance: number): void {
  if (typeof expected === 'number') {
    expect(typeof actual).toBe('number');
    expect(Math.abs((actual as number) - expected)).toBeLessThanOrEqual(tolerance);
  } else if (Array.isArray(expected)) {
    expect(Array.isArray(actual)).toBe(true);
    expect((actual as unknown[]).length).toBe(expected.length);
    expected.forEach((item, index) => expectClose((actual as unknown[])[index], item, tolerance));
  } else if (expected !== null && typeof expected === 'object') {
    const record = expected as Record<string, unknown>;
    expect(Object.keys(actual as object).sort()).toEqual(Object.keys(record).sort());
    for (const [key, value] of Object.entries(record)) {
      expectClose((actual as Record<string, unknown>)[key], value, tolerance);
    }
  } else {
    expect(actual).toStrictEqual(expected);
  }
}

function run(vector: VectorCase): unknown {
  const input = vector.input as Input;
  const tolerance = (input.tolerance_m as number | undefined) ?? 0.01;
  switch (vector.operation) {
    case 'area':
      return areaM2(parsed(input.geometry));
    case 'resolved_area': {
      const shape = toShape(parsed(input.geometry));
      if (shape.kind !== 'vertices') throw new Error('resolved_area needs a vertex shape');
      return Number(shoelaceArea(shape.vertices).toFixed(3));
    }
    case 'bbox':
      return boundingBox(parsed(input.geometry));
    case 'centroid':
      return centroid(parsed(input.geometry));
    case 'is_simple': {
      const geometry = parsed(input.geometry);
      if (geometry.kind !== 'polygon') throw new Error('is_simple needs a polygon');
      return isSimplePolygon(geometry.points);
    }
    case 'validate':
      return validateGeometry(parsed(input.geometry));
    case 'contains': {
      const mode = input.mode as 'plan' | 'bed';
      const parentGeometry = parsed(input.parent);
      const parent = mode === 'bed' ? toLocalShape(parentGeometry) : toShape(parentGeometry);
      const child = toShape(parsed(input.child, mode === 'bed' ? 'bed' : 'plan'));
      return contains(parent, child, {
        toleranceM: tolerance,
        insetM: (input.inset_m as number | undefined) ?? 0,
      });
    }
    case 'overlaps':
      return overlaps(toShape(parsed(input.a)), toShape(parsed(input.b)), {
        toleranceM: tolerance,
      });
    case 'bed_to_plan':
      return transformBedToPlan(input.point as Point, parsed(input.bed));
    case 'plan_to_bed':
      return transformPlanToBed(input.point as Point, parsed(input.bed));
    case 'validate_model': {
      const frame = (input.frame as GeometryFrame | undefined) ?? 'plan';
      const geometry = parseGeometry(input.geometry, frame);
      if (geometry === null) return { valid: false };
      const expected = vector.expected as Record<string, unknown>;
      return 'normalized' in expected ? { valid: true, normalized: geometry } : { valid: true };
    }
    default:
      throw new Error(`unknown operation ${vector.operation} in vector ${vector.id}`);
  }
}

describe('garden-plan-vectors.json', () => {
  it('has unique ids', () => {
    const ids = ALL_VECTORS.cases.map((vector) => vector.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('exercises exactly the documented operations', () => {
    expect(new Set(VECTORS.cases.map((vector) => vector.operation))).toEqual(
      new Set(Object.keys(VECTORS.operations).filter((name) => !LAYOUT_OPERATIONS.has(name))),
    );
  });

  it('keeps the acceptance criteria GP-ACC-003 and GP-ACC-004 pinned', () => {
    const specs = VECTORS.cases.map((vector) => vector.spec).join(' ');
    expect(specs).toContain('GP-ACC-003');
    expect(specs).toContain('GP-ACC-004');
  });
});

describe('geometry port against the shared vectors', () => {
  it.each(VECTORS.cases.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    expectClose(run(vector), vector.expected, vector.tolerance ?? VECTORS.default_tolerance);
  });
});
