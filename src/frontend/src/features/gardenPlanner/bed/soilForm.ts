import { z } from 'zod';
import type { Substrate } from '@/api/types';
import {
  GROWING_MEDIUM_KINDS,
  PH_METHODS,
  SITE_WATER_REGIMES,
  SOIL_CONDITIONS,
  SOIL_DRAINAGES,
  SOIL_TEXTURES,
  type GrowingMediumKind,
  type PhMethod,
  type SoilCondition,
  type SoilProfile,
} from './types';

/** The form works on strings (`''` = not set) so every select stays controlled. */
export const soilFormSchema = z.object({
  growing_medium_kind: z.string(),
  soil_texture: z.string(),
  drainage: z.string(),
  site_water_regime: z.string(),
  conditions: z.array(z.string()),
  substrate_key: z.string(),
  ph: z.number().min(0).max(14).nullable(),
  ph_method: z.string(),
  ec_ms_cm: z.number().min(0).nullable(),
  humus_percent: z.number().min(0).max(100).nullable(),
  notes: z.string().max(4000),
});

export type SoilFormData = z.infer<typeof soilFormSchema>;

export const EMPTY_SOIL_FORM: SoilFormData = {
  growing_medium_kind: '',
  soil_texture: 'unknown',
  drainage: 'unknown',
  site_water_regime: 'unknown',
  conditions: [],
  substrate_key: '',
  ph: null,
  ph_method: '',
  ec_ms_cm: null,
  humus_percent: null,
  notes: '',
};

/** Media that are filled from a catalogue substrate (GP-FR-121). */
export const SUBSTRATE_MEDIA: readonly GrowingMediumKind[] = [
  'raised_bed_mix',
  'potting_mix',
  'mineral_substrate',
];

export function soilToForm(profile: SoilProfile | null | undefined): SoilFormData {
  if (!profile) return EMPTY_SOIL_FORM;
  return {
    growing_medium_kind: profile.growing_medium_kind ?? '',
    soil_texture: profile.soil_texture,
    drainage: profile.drainage,
    site_water_regime: profile.site_water_regime,
    conditions: [...profile.conditions],
    substrate_key: profile.substrate_key ?? '',
    ph: profile.ph ?? null,
    ph_method: profile.ph_method ?? '',
    ec_ms_cm: profile.ec_ms_cm ?? null,
    humus_percent: profile.humus_percent ?? null,
    notes: profile.notes ?? '',
  };
}

function oneOf<T extends string>(allowed: readonly T[], value: string): T | null {
  return (allowed as readonly string[]).includes(value) ? (value as T) : null;
}

/** The API body of the form; values outside the closed lists never leave the client. */
export function formToSoil(form: SoilFormData): SoilProfile {
  const medium = oneOf(GROWING_MEDIUM_KINDS, form.growing_medium_kind);
  const hasSubstrate = medium !== null && SUBSTRATE_MEDIA.includes(medium) && form.substrate_key !== '';
  return {
    growing_medium_kind: medium,
    soil_texture: oneOf(SOIL_TEXTURES, form.soil_texture) ?? 'unknown',
    drainage: oneOf(SOIL_DRAINAGES, form.drainage) ?? 'unknown',
    site_water_regime: oneOf(SITE_WATER_REGIMES, form.site_water_regime) ?? 'unknown',
    conditions: form.conditions.flatMap((value) => {
      const condition: SoilCondition | null = oneOf(SOIL_CONDITIONS, value);
      return condition === null ? [] : [condition];
    }),
    substrate_key: hasSubstrate ? form.substrate_key : null,
    ph: form.ph,
    ph_method: form.ph === null ? null : (oneOf<PhMethod>(PH_METHODS, form.ph_method) ?? null),
    ec_ms_cm: form.ec_ms_cm,
    humus_percent: form.humus_percent,
    notes: form.notes.trim() === '' ? null : form.notes.trim(),
  };
}

/** GP-FR-121: a chosen substrate pre-fills pH and EC where the bed has no measurement yet. */
export function substrateDefaults(
  substrate: Substrate | undefined,
  current: Pick<SoilFormData, 'ph' | 'ec_ms_cm'>,
): Pick<SoilFormData, 'ph' | 'ec_ms_cm'> {
  if (!substrate) return current;
  return {
    ph: current.ph ?? substrate.ph_base,
    ec_ms_cm: current.ec_ms_cm ?? substrate.ec_base_ms,
  };
}
