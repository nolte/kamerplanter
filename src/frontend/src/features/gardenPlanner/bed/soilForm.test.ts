import { describe, expect, it } from 'vitest';
import type { Substrate } from '@/api/types';
import { bedSummary } from './bedTestKit';
import type { TFunction } from 'i18next';
import { EMPTY_SOIL_FORM, buildSoilFormSchema, formToSoil, soilToForm, substrateDefaults } from './soilForm';

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
      ec_method: null,
      humus_percent: null,
      target_ph: null,
      notes: null,
    });
  });

  it('sends back what the form does not show, so saving never erases what a soil analysis wrote (WP 8.8)', () => {
    const stored = {
      ...bedSummary().soil_profile!,
      ec_ms_cm: 0.4,
      ec_method: 'ratio_1_5' as const,
      caco3_percent: 2,
      stone_content_class: 'few' as const,
      last_analysis_at: '2026-03-01T09:00:00Z',
      target_ph: 6.2,
    };
    const back = formToSoil({ ...soilToForm(stored), drainage: 'poor' }, stored);
    expect(back).toMatchObject({
      drainage: 'poor',
      ec_ms_cm: 0.4,
      ec_method: 'ratio_1_5',
      caco3_percent: 2,
      stone_content_class: 'few',
      last_analysis_at: '2026-03-01T09:00:00Z',
      target_ph: 6.2,
    });
    // the EC method goes with its value: no value, no method
    expect(formToSoil({ ...soilToForm(stored), ec_ms_cm: null }, stored).ec_method).toBeNull();
  });

  it('asks for the EC method as soon as an EC value is set (U-002)', () => {
    const schema = buildSoilFormSchema(((key: string) => key) as unknown as TFunction);
    const missing = schema.safeParse({ ...EMPTY_SOIL_FORM, ec_ms_cm: 0.8 });
    expect(missing.success).toBe(false);
    expect(missing.error?.issues[0]?.path).toEqual(['ec_method']);
    expect(schema.safeParse({ ...EMPTY_SOIL_FORM, ec_ms_cm: 0.8, ec_method: 'sensor' }).success).toBe(true);
    expect(schema.safeParse(EMPTY_SOIL_FORM).success).toBe(true);
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
