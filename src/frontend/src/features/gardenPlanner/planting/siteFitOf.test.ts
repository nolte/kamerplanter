import { describe, expect, it } from 'vitest';
import { species } from './plantingTestKit';
import { siteFitOf } from './siteFitOf';

describe('siteFitOf', () => {
  it('compares the bed with the light requirement and passes the tolerance along', () => {
    const tomato = species('sp_t', 'Tomato', { light_requirement: 'full_sun', shade_tolerance: 'partial_shade' });

    expect(siteFitOf(tomato, 'partial_shade')).toMatchObject({
      lightRequirement: 'full_sun',
      shadeTolerance: 'partial_shade',
      result: { fit: 'marginal', reason: 'tolerated' },
    });
  });

  it('has nothing to say without a species, without a requirement or on an unknown bed (GP-FR-160)', () => {
    const tomato = species('sp_t', 'Tomato', { light_requirement: 'full_sun' });

    expect(siteFitOf(undefined, 'shade')).toBeNull();
    expect(siteFitOf(species('sp_x', 'X'), 'shade')).toBeNull();
    expect(siteFitOf(tomato, 'unknown')).toBeNull();
  });

  it('never reads the tolerance as the requirement (E-05)', () => {
    expect(siteFitOf(species('sp_x', 'X', { shade_tolerance: 'deep_shade' }), 'shade')).toBeNull();
  });
});
