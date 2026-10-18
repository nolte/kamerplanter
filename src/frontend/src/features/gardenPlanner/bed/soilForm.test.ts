import { describe, expect, it } from 'vitest';
import type { Substrate } from '@/api/types';
import { bedSummary } from './bedTestKit';
import { EMPTY_SOIL_FORM, formToSoil, soilToForm, substrateDefaults } from './soilForm';

describe('soil profile form mapping (GP-FR-120/121)', () => {
  it('round-trips a stored profile', () => {
    const profile = bedSummary().soil_profile!;
    const back = formToSoil(soilToForm(profile));
    expect(back).toMatchObject({
      growing_medium_kind: 'native_soil',
      soil_texture: 'loam',
      drainage: 'good',
      site_water_regime: 'fresh',
      conditions: ['stony'],
      ph: 6.5,
      ph_method: 'cacl2',
    });
  });

  it('keeps everything unknown for a bed without a profile - nothing is invented', () => {
    expect(soilToForm(null)).toEqual(EMPTY_SOIL_FORM);
    expect(formToSoil(EMPTY_SOIL_FORM)).toEqual({
      growing_medium_kind: null,
      soil_texture: 'unknown',
      drainage: 'unknown',
      site_water_regime: 'unknown',
      conditions: [],
      substrate_key: null,
      ph: null,
      ph_method: null,
      ec_ms_cm: null,
      humus_percent: null,
      notes: null,
    });
  });

  it('drops a substrate unless the filling is a substrate one, and a method without a pH', () => {
    const native = formToSoil({
      ...EMPTY_SOIL_FORM,
      growing_medium_kind: 'native_soil',
      substrate_key: 'sub_1',
      ph_method: 'h2o',
    });
    expect(native.substrate_key).toBeNull();
    expect(native.ph_method).toBeNull();
    const mix = formToSoil({ ...EMPTY_SOIL_FORM, growing_medium_kind: 'raised_bed_mix', substrate_key: 'sub_1' });
    expect(mix.substrate_key).toBe('sub_1');
  });

  it('never sends a value outside the closed lists', () => {
    const soil = formToSoil({ ...EMPTY_SOIL_FORM, soil_texture: 'granite', conditions: ['stony', 'haunted'] });
    expect(soil.soil_texture).toBe('unknown');
    expect(soil.conditions).toEqual(['stony']);
  });

  it('pre-fills pH and EC from the substrate only where the bed has no measurement (GP-FR-121)', () => {
    const substrate = { key: 'sub_1', ph_base: 6.2, ec_base_ms: 0.8 } as Substrate;
    expect(substrateDefaults(substrate, { ph: null, ec_ms_cm: null })).toEqual({ ph: 6.2, ec_ms_cm: 0.8 });
    expect(substrateDefaults(substrate, { ph: 7.1, ec_ms_cm: null })).toEqual({ ph: 7.1, ec_ms_cm: 0.8 });
    expect(substrateDefaults(undefined, { ph: null, ec_ms_cm: null })).toEqual({ ph: null, ec_ms_cm: null });
  });
});
