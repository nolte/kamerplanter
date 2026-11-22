import { describe, expect, it } from 'vitest';
import {
  areaDoseTotal,
  gPerM2ToKgPerHa,
  lPerM2ToMm,
  nitrogenApproximation,
  roundHalfUp,
} from './areaDose';
import { loadVectors } from '@/test/gardenPlanVectors';

/**
 * The TypeScript port of the area doses runs against the same vector file as the Python reference
 * (`tests/unit/domain/calculators/test_area_dose_vectors.py`, REQ-053 GP-FR-123, WP 8.9).
 */
const VECTORS = loadVectors();
const OPERATIONS = ['area_dose', 'nitrogen_approximation', 'unit_identity'];
const CASES = VECTORS.cases.filter((vector) => OPERATIONS.includes(vector.operation));

function run(operation: string, input: Record<string, unknown>): Record<string, unknown> | null {
  if (operation === 'area_dose') {
    const total = areaDoseTotal(
      input.quantity as number | null,
      input.unit as string | null,
      input.area_m2 as number | null,
    );
    return {
      quantity_total: total?.quantityTotal ?? null,
      quantity_total_unit: total?.quantityTotalUnit ?? null,
      display_total: total?.displayTotal ?? null,
    };
  }
  if (operation === 'nitrogen_approximation') {
    const result = nitrogenApproximation(
      input.rate_g_per_m2 as number,
      input.n_percent as number | null,
    );
    return result && { g_n_per_m2: result.gNPerM2, kg_n_per_ha: result.kgNPerHa };
  }
  const value = input.value as number;
  return input.unit === 'g_per_m2'
    ? { kg_per_ha: gPerM2ToKgPerHa(value) }
    : { mm: lPerM2ToMm(value) };
}

describe('area dose vectors', () => {
  it('carries the operations and the acceptance numbers', () => {
    for (const operation of OPERATIONS) expect(VECTORS.operations).toHaveProperty(operation);
    expect(CASES.map((vector) => vector.id)).toEqual(
      expect.arrayContaining([
        'area-dose-g-bed-3x1.2',
        'area-dose-l-bed-3x1.2',
        'area-dose-no-area',
        'nitrogen-horn-shavings-13',
        'unit-g-per-m2-is-10-kg-per-ha',
        'unit-l-per-m2-is-1-mm',
      ]),
    );
  });

  it.each(CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const actual = run(vector.operation, vector.input);
    const expected = vector.expected as Record<string, unknown> | null;
    if (expected === null) {
      expect(actual).toBeNull();
      return;
    }
    expect(Object.keys(actual ?? {}).sort()).toEqual(Object.keys(expected).sort());
    for (const [name, value] of Object.entries(expected)) {
      if (typeof value === 'number') expect(actual?.[name]).toBeCloseTo(value, 6);
      else expect(actual?.[name]).toBe(value);
    }
  });
});

/** Review U-001 as properties over a spread of rates and areas, not only the vector values. */
describe('unit identities', () => {
  const samples: number[] = [];
  for (let i = 1; i <= 400; i += 1) samples.push(Number((i * 0.731 + (i % 7) * 13.37).toFixed(4)));

  it('1 g/m² is 10 kg/ha for every rate', () => {
    for (const rate of samples) {
      expect(gPerM2ToKgPerHa(rate)).toBeCloseTo(rate * 10, 9);
      expect(gPerM2ToKgPerHa(rate) / gPerM2ToKgPerHa(1)).toBeCloseTo(rate, 9);
    }
  });

  it('1 L/m² is 1 mm for every rate', () => {
    for (const rate of samples) expect(lPerM2ToMm(rate)).toBe(rate);
  });

  it('the total is rate × area within its rounding, and a bed without area never has one', () => {
    for (const rate of samples) {
      for (const area of [0.5, 1, 3.6, 12.25]) {
        const total = areaDoseTotal(rate, 'g_per_m2', area);
        expect(total?.quantityTotalUnit).toBe('g');
        expect(Math.abs((total?.quantityTotal ?? Number.NaN) - rate * area)).toBeLessThanOrEqual(
          0.0005 + 1e-9,
        );
      }
      expect(areaDoseTotal(rate, 'g_per_m2', 0)).toBeNull();
      expect(areaDoseTotal(rate, 'l_per_m2', -1)).toBeNull();
      expect(areaDoseTotal(rate, 'l_per_m2', null)).toBeNull();
    }
  });

  it('kg N/ha is ten times g N/m² within the rounding', () => {
    for (const rate of samples) {
      const result = nitrogenApproximation(rate, 13);
      const unrounded = (rate * 13) / 100;
      expect(Math.abs((result?.gNPerM2 ?? Number.NaN) - unrounded)).toBeLessThanOrEqual(
        0.05 + 1e-9,
      );
      expect(Math.abs((result?.kgNPerHa ?? Number.NaN) - unrounded * 10)).toBeLessThanOrEqual(
        0.5 + 1e-9,
      );
    }
  });

  it('rounds ties away from zero on the exact binary value, like the Python reference', () => {
    expect(roundHalfUp(1.25, 1)).toBe(1.3);
    expect(roundHalfUp(2.5, 0)).toBe(3);
    expect(roundHalfUp(1.005, 2)).toBe(1);
    expect(Object.is(roundHalfUp(-0.0001, 1), 0)).toBe(true);
  });
});
