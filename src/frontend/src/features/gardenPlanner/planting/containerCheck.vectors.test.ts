import { describe, expect, it } from 'vitest';
import type { Species } from '@/api/types';
import { loadVectors } from '@/test/gardenPlanVectors';
import { containerCheck } from './plantingLogic';

/**
 * The pot-volume warning of the planting dialog runs against the same vectors as the server's check
 * (`tests/unit/domain/calculators/test_container_volume_vectors.py`, REQ-053 §9.2a W-016.5, WP 10.11).
 */
const VECTORS = loadVectors();
const CASES = VECTORS.cases.filter((vector) => vector.operation === 'container_volume');

describe('container volume vectors', () => {
  it('carries the operation and the boundary cases', () => {
    expect(VECTORS.operations).toHaveProperty('container_volume');
    expect(CASES.map((vector) => vector.id)).toEqual(
      expect.arrayContaining([
        'container-volume-below-range',
        'container-volume-equal-lower-bound',
        'container-volume-no-recommendation',
        'container-volume-zero-recommendation',
        'container-volume-young-phase-seedling',
        'container-volume-young-phase-rooting',
        'container-volume-hydro',
        'container-volume-nft',
        'container-volume-ebb-flow',
      ]),
    );
  });

  it.each(CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const input = vector.input as {
      container_volume_l: number | null;
      recommended_container_volume_l: string | number | null;
      phase_code?: string;
      irrigation_system?: string;
    };
    const species = { recommended_container_volume_l: input.recommended_container_volume_l } as unknown as Species;
    const check = containerCheck(input.container_volume_l === null ? '' : String(input.container_volume_l), species, {
      phaseCode: input.phase_code ?? null,
      irrigationSystem: input.irrigation_system ?? null,
    });
    expect({ volume_below: check.volumeBelow, recommended_l: check.recommendedL }).toEqual(vector.expected);
  });
});
