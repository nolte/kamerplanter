import { describe, expect, it } from 'vitest';
import { formToTentRulesPatch, tentRulesToForm } from './tentRulesForm';

describe('tent rules form (W-016)', () => {
  it('reads the stored values, empty as null', () => {
    expect(tentRulesToForm(undefined, null)).toEqual({
      adjacency_factor: null,
      lamp_height_cm: null,
      canopy_distance_cm: null,
    });
    expect(tentRulesToForm(2, { lamp_height_cm: 180 })).toEqual({
      adjacency_factor: 2,
      lamp_height_cm: 180,
      canopy_distance_cm: null,
    });
  });

  it('clears the lighting when no value is left', () => {
    expect(
      formToTentRulesPatch({ adjacency_factor: null, lamp_height_cm: null, canopy_distance_cm: null }, { lamp_height_cm: 1 }),
    ).toEqual({ adjacency_factor: null, lighting: null });
  });

  it('sends only the values set, and the stored footprint with them', () => {
    const fixture = { kind: 'circle', origin: [0.5, 0.5], radius_m: 0.3 };
    expect(
      formToTentRulesPatch(
        { adjacency_factor: 1.2, lamp_height_cm: null, canopy_distance_cm: 30 },
        { fixture_geometry: fixture },
      ),
    ).toEqual({ adjacency_factor: 1.2, lighting: { canopy_distance_cm: 30, fixture_geometry: fixture } });
  });
});
