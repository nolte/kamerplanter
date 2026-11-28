/**
 * What the soil-hazard form offers, read from the server's `soil_hazard_scope` (#2888 F-20, O3/O5): the page never
 * recomputes the rule - a shelf under a hydroponic room is `hydroponic` because the server says so.
 */
import { describe, expect, it } from 'vitest';
import { recordableSoilHazards, SOIL_HAZARDS, soilHazardsUnavailable } from './soilHazardTypes';

describe('soilHazardsUnavailable', () => {
  it.each(['container', 'hydroponic'] as const)('answers %s as the refusal it is', (scope) => {
    expect(soilHazardsUnavailable(scope)).toBe(scope);
  });

  it.each(['all', 'juglone_only'] as const)('lets a %s location carry one', (scope) => {
    expect(soilHazardsUnavailable(scope)).toBeNull();
  });
});

describe('recordableSoilHazards', () => {
  it('offers every hazard at a bed', () => {
    expect(recordableSoilHazards('all')).toEqual(SOIL_HAZARDS);
  });

  it('offers juglone only at an area that is no bed', () => {
    expect(recordableSoilHazards('juglone_only')).toEqual(['juglone']);
  });

  it.each(['container', 'hydroponic'] as const)('offers nothing at a %s location', (scope) => {
    expect(recordableSoilHazards(scope)).toEqual([]);
  });
});
