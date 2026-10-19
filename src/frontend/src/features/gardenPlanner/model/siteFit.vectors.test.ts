import { describe, expect, it } from 'vitest';
import { assessSiteFit } from './siteFit';
import { loadVectors } from '@/test/gardenPlanVectors';

/**
 * The TypeScript port of `site_fit` runs against the same vector file as the Python reference
 * (`tests/unit/domain/calculators/test_site_fit_vectors.py`, REQ-053 §19.6). A test that copied the
 * cases inline would certify nothing; the GP-ACC-053 cases are pinned by id so the proof cannot be
 * dropped quietly.
 */
const VECTORS = loadVectors();
const CASES = VECTORS.cases.filter((vector) => vector.operation === 'site_fit');

const GP_ACC_053: Record<string, string> = {
  'site-fit-sunnier-two-steps': 'poor',
  'site-fit-shadier-two-steps': 'poor',
  'site-fit-shadier-one-step-covered': 'marginal',
  'site-fit-shadier-one-step-tolerance-unknown': 'marginal',
  'site-fit-unknown-bed': 'unknown',
  'site-fit-unknown-requirement': 'unknown',
};

describe('site_fit vectors (shared with the Python reference)', () => {
  it('the operation is documented and has cases', () => {
    expect(VECTORS.operations).toHaveProperty('site_fit');
    expect(CASES.length).toBeGreaterThan(0);
  });

  it.each(CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const { sun_exposure, light_requirement, shade_tolerance } = vector.input as {
      sun_exposure: string;
      light_requirement: string | null;
      shade_tolerance: string | null;
    };
    const result = assessSiteFit(sun_exposure, light_requirement, shade_tolerance);

    expect({ fit: result.fit, reason: result.reason }).toStrictEqual(vector.expected);
  });

  it('keeps the cases GP-ACC-053 names', () => {
    const byId = new Map(CASES.map((vector) => [vector.id, vector]));
    for (const [id, fit] of Object.entries(GP_ACC_053)) {
      expect((byId.get(id)?.expected as { fit: string } | undefined)?.fit).toBe(fit);
    }
  });

  it('covers every cell of the bed x demand matrix', () => {
    const covered = new Set(
      CASES.map((vector) => {
        const input = vector.input as { sun_exposure: string; light_requirement: string | null };
        return `${input.sun_exposure}|${input.light_requirement}`;
      }),
    );
    for (const bed of ['full_sun', 'partial_shade', 'shade', 'deep_shade']) {
      for (const demand of ['full_sun', 'partial_shade', 'shade']) {
        expect(covered, `${bed} x ${demand}`).toContain(`${bed}|${demand}`);
      }
    }
  });
});

describe('site_fit rules stated apart from the file', () => {
  it('never derives the requirement from the tolerance (E-05)', () => {
    expect(assessSiteFit('full_sun', null, 'deep_shade').fit).toBe('unknown');
  });

  it('treats a requirement outside the enum as missing', () => {
    expect(assessSiteFit('full_sun', 'deep_shade', null).fit).toBe('unknown');
  });

  it('treats a value that is not a step as missing, also an inherited property name', () => {
    expect(assessSiteFit('constructor', 'full_sun', null).fit).toBe('unknown');
    expect(assessSiteFit('toString', 'full_sun', null).reason).toBe('bed_unknown');
    expect(assessSiteFit('full_sun', 'constructor', null).reason).toBe('requirement_unknown');
    expect(assessSiteFit('partial_shade', 'full_sun', '__proto__').reason).toBe('tolerance_unknown');
  });

  it('reports the steps, negative when the bed is shadier', () => {
    expect(assessSiteFit('shade', 'partial_shade', 'shade').steps).toBe(-1);
    expect(assessSiteFit('full_sun', 'shade', null).steps).toBe(2);
  });
});
