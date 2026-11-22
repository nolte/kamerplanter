import { describe, expect, it } from 'vitest';
import { computeLayout, LayoutError, type EntryLayout, type LayoutResult } from './layout';
import { parseGeometry } from './geometry';
import { loadVectors, type VectorCase } from '@/test/gardenPlanVectors';

/**
 * The TypeScript port of the planting layout runs against the same vector file as the Python
 * reference (`tests/unit/domain/calculators/test_planting_layout_vectors.py`, REQ-053 §19.6). A test
 * that copied the cases inline would certify nothing; GP-ACC-017/018/043 are pinned by id.
 */
const VECTORS = loadVectors();
const LAYOUT_CASES = VECTORS.cases.filter(
  (vector) => vector.operation === 'layout' || vector.operation === 'layout_error',
);

function bedOf(vector: VectorCase) {
  const bed = parseGeometry((vector.input as { bed: unknown }).bed, 'plan');
  if (bed === null) throw new Error(`vector bed does not parse: ${vector.id}`);
  return bed;
}

function entryOf(vector: VectorCase): { entry: EntryLayout; maxCount: number | null } {
  const { max_count: maxCount, ...entry } = (
    vector.input as { entry: EntryLayout & { max_count?: number } }
  ).entry;
  return { entry, maxCount: maxCount ?? null };
}

function view(result: LayoutResult) {
  const positions = result.slots.filter((slot) => slot.point !== null);
  return {
    count: result.count,
    capacity_max: result.capacity_max,
    warnings: result.warnings.map((warning) => warning.code),
    points: positions.map((slot) => slot.point),
    row_indices: positions.map((slot) => slot.row_index),
    zones: result.slots
      .filter((slot) => slot.outline !== null)
      .map((slot) => ({ outline: slot.outline, capacity_plants: slot.capacity_plants })),
  };
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

describe('layout vectors in garden-plan-vectors.json', () => {
  it('document and exercise both layout operations', () => {
    expect(new Set(LAYOUT_CASES.map((vector) => vector.operation))).toEqual(
      new Set(['layout', 'layout_error']),
    );
    expect(Object.keys(VECTORS.operations)).toEqual(
      expect.arrayContaining(['layout', 'layout_error']),
    );
  });

  it('keep GP-ACC-017, GP-ACC-018 and GP-ACC-043 pinned', () => {
    const byId = new Map(LAYOUT_CASES.map((vector) => [vector.id, vector] as const));
    expect(byId.get('layout-001-acc-017-rows-rect')?.spec).toContain('GP-ACC-017');
    expect(byId.get('layout-003-acc-018-triangle-grid')?.spec).toContain('GP-ACC-018');
    expect(byId.get('layout-error-001-acc-043-too-many-positions')?.spec).toContain('GP-ACC-043');
  });
});

describe('layout port against the shared vectors', () => {
  it.each(LAYOUT_CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const bed = bedOf(vector);
    const { entry, maxCount } = entryOf(vector);
    if (vector.operation === 'layout') {
      expectClose(
        view(computeLayout(bed, entry, maxCount)),
        vector.expected,
        VECTORS.default_tolerance,
      );
      return;
    }
    const expected = vector.expected as { code: string; estimated?: number };
    let thrown: unknown = null;
    try {
      computeLayout(bed, entry, maxCount);
    } catch (error) {
      thrown = error;
    }
    expect(thrown).toBeInstanceOf(LayoutError);
    expect((thrown as LayoutError).code).toBe(expected.code);
    if (expected.estimated !== undefined)
      expect((thrown as LayoutError).estimated).toBe(expected.estimated);
  });
});

describe('GP-ACC-017/018/043 stated from the requirement text', () => {
  it('GP-ACC-017: three rows of ten positions', () => {
    const bed = parseGeometry(
      { kind: 'rect', origin: [2, 3.5], width_m: 3, length_m: 1.2, rotation_deg: 0 },
      'plan',
    );
    if (bed === null) throw new Error('bed does not parse');
    const result = computeLayout(bed, {
      layout_strategy: 'rows',
      spacing_cm: 30,
      row_spacing_cm: 40,
      edge_margin_along_cm: 15,
      edge_margin_across_cm: 15,
    });
    expect(result.count).toBe(30);
    const ys = [...new Set(result.slots.map((slot) => slot.point?.[1]))];
    ys.forEach((y, index) => expect(y).toBeCloseTo([0.15, 0.55, 0.95][index], 3));
  });

  it('GP-ACC-043: refuses a 1000 x 1000 m bed at 5 cm before generating points', () => {
    const bed = parseGeometry(
      { kind: 'rect', origin: [0, 0], width_m: 1000, length_m: 1000, rotation_deg: 0 },
      'plan',
    );
    if (bed === null) throw new Error('bed does not parse');
    const started = performance.now();
    expect(() => computeLayout(bed, { layout_strategy: 'grid', spacing_cm: 5 })).toThrow(
      LayoutError,
    );
    expect(performance.now() - started).toBeLessThan(50);
  });
});
