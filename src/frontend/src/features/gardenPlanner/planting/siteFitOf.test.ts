import { describe, expect, it } from 'vitest';
import { species } from './plantingTestKit';
import { siteAxesOf, siteFitOf } from './siteFitOf';

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

describe('siteAxesOf', () => {
  const frail = species('sp_f', 'Frail', {
    frost_sensitivity: 'sensitive',
    support_required: true,
    waterlogging_tolerance: 'sensitive',
  });

  it('names the three hints in the fixed order, independent of the light requirement', () => {
    expect(siteAxesOf(frail, { frostRisk: 'high', windExposure: 'exposed', drainage: 'poor' })).toStrictEqual([
      'frost_mismatch',
      'wind_support_needed',
      'waterlogging_risk',
    ]);
  });

  it('has nothing to say without a species or a bed, or where either side is unknown', () => {
    expect(siteAxesOf(undefined, { frostRisk: 'high' })).toStrictEqual([]);
    expect(siteAxesOf(frail, undefined)).toStrictEqual([]);
    expect(siteAxesOf(frail, { frostRisk: 'unknown', windExposure: 'unknown', drainage: 'unknown' })).toStrictEqual([]);
    expect(siteAxesOf(species('sp_x', 'X'), { frostRisk: 'high', windExposure: 'exposed', drainage: 'poor' })).toStrictEqual([]);
  });
});
