import { describe, expect, it } from 'vitest';
import { parseGeometry } from './geometry';
import { assessReach, reachAccess, REACH_BOTH_SIDES_M, REACH_ONE_SIDE_M } from './reach';
import { loadVectors } from '@/test/gardenPlanVectors';

/**
 * The TypeScript port of `reach` runs against the same vector file as the Python reference
 * (`tests/unit/domain/calculators/test_reach_vectors.py`, REQ-053 GP-FR-166, §19.6). A test that copied the
 * cases inline would certify nothing; the acceptance cases of #2666 are pinned by id.
 */
const VECTORS = loadVectors();
const CASES = VECTORS.cases.filter((vector) => vector.operation === 'reach');

const ACCEPTANCE: Record<string, boolean> = {
  'reach-rect-1-3-no-access': true,
  'reach-rect-1-2-both-sides-ns': false,
  'reach-rect-1-3-both-sides': true,
};

interface ReachInput {
  geometry: unknown;
  access_sides: string[] | null;
  both_sides_m?: number;
  one_side_m?: number;
}

interface ReachExpected {
  hint: boolean;
  reason: string;
  access: string;
  threshold_m: number;
  width_m: number | null;
}

describe('reach vectors (shared with the Python reference)', () => {
  it('the operation is documented and has cases', () => {
    expect(VECTORS.operations).toHaveProperty('reach');
    expect(CASES.length).toBeGreaterThan(0);
  });

  it.each(CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const input = vector.input as unknown as ReachInput;
    const expected = vector.expected as ReachExpected;
    const tolerance = vector.tolerance ?? VECTORS.default_tolerance;
    const geometry = input.geometry === null ? null : parseGeometry(input.geometry);
    if (input.geometry !== null && geometry === null) throw new Error(`vector geometry does not parse: ${vector.id}`);

    const result = assessReach(geometry, input.access_sides, {
      bothSidesM: input.both_sides_m,
      oneSideM: input.one_side_m,
    });

    expect({ hint: result.hint, reason: result.reason, access: result.access }).toStrictEqual({
      hint: expected.hint,
      reason: expected.reason,
      access: expected.access,
    });
    expect(Math.abs(result.thresholdM - expected.threshold_m)).toBeLessThanOrEqual(tolerance);
    if (expected.width_m === null) expect(result.widthM).toBeNull();
    else expect(Math.abs((result.widthM ?? Number.NaN) - expected.width_m)).toBeLessThanOrEqual(tolerance);
  });

  it('keeps the acceptance cases of #2666', () => {
    const byId = new Map(CASES.map((vector) => [vector.id, vector]));
    for (const [id, hint] of Object.entries(ACCEPTANCE)) {
      expect((byId.get(id)?.expected as ReachExpected | undefined)?.hint).toBe(hint);
    }
  });
});

describe('reach rules stated apart from the file', () => {
  it('uses the confirmed defaults', () => {
    expect([REACH_BOTH_SIDES_M, REACH_ONE_SIDE_M]).toStrictEqual([1.2, 0.6]);
  });

  it('reads only an opposite pair as both sides', () => {
    expect(reachAccess([])).toBe('unknown');
    expect(reachAccess(undefined)).toBe('unknown');
    expect(reachAccess(['N', 'E'])).toBe('one');
    expect(reachAccess(['W', 'E'])).toBe('both');
    expect(reachAccess(['N', 'E', 'S'])).toBe('both');
  });

  it('never throws on missing data', () => {
    expect(assessReach(null, null)).toStrictEqual({
      hint: false,
      reason: 'width_unknown',
      access: 'unknown',
      thresholdM: 0.6,
      widthM: null,
    });
  });
});
