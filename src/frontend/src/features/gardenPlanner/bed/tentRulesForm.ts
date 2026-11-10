/**
 * The form of a location's tent rules (REQ-053 WP 10.11, W-016): its own neighbourhood factor (W-016.8) and the lamp
 * height and canopy distance of its lighting (W-016.2/3). Pure: the schema, and the mapping between the stored
 * values, the form and the `PATCH /locations/{key}` body. The bounds are the server's (`site.py`
 * `MAX_ADJACENCY_FACTOR`, `MAX_LAMP_HEIGHT_CM`); the server refuses the same values with a 422.
 */
import type { TFunction } from 'i18next';
import { z } from 'zod';
import type { LocationLighting } from '@/api/types';
import type { TentRulesPatch } from './types';

export const MAX_ADJACENCY_FACTOR = 10;
export const MAX_LAMP_HEIGHT_CM = 1000;

export interface TentRulesFormData {
  adjacency_factor: number | null;
  lamp_height_cm: number | null;
  canopy_distance_cm: number | null;
}

export function buildTentRulesSchema(t: TFunction) {
  return z
    .object({
      adjacency_factor: z
        .number()
        .gt(0, t('pages.bed.tentRules.errors.factorRange'))
        .max(MAX_ADJACENCY_FACTOR, t('pages.bed.tentRules.errors.factorRange'))
        .nullable(),
      lamp_height_cm: z
        .number()
        .gt(0, t('pages.bed.tentRules.errors.lampRange'))
        .max(MAX_LAMP_HEIGHT_CM, t('pages.bed.tentRules.errors.lampRange'))
        .nullable(),
      canopy_distance_cm: z
        .number()
        .min(0, t('pages.bed.tentRules.errors.canopyRange'))
        .max(MAX_LAMP_HEIGHT_CM, t('pages.bed.tentRules.errors.canopyRange'))
        .nullable(),
    })
    .refine(
      (data) =>
        data.lamp_height_cm === null || data.canopy_distance_cm === null || data.canopy_distance_cm <= data.lamp_height_cm,
      { path: ['canopy_distance_cm'], message: t('pages.bed.tentRules.errors.canopyAboveLamp') },
    );
}

export function tentRulesToForm(
  adjacencyFactor: number | null | undefined,
  lighting: LocationLighting | null | undefined,
): TentRulesFormData {
  return {
    adjacency_factor: adjacencyFactor ?? null,
    lamp_height_cm: lighting?.lamp_height_cm ?? null,
    canopy_distance_cm: lighting?.canopy_distance_cm ?? null,
  };
}

/**
 * The PATCH body. The lighting is replaced whole on the server, so the stored fixture footprint (set through the API,
 * not edited here) travels along; without any value left the lighting is cleared (`null`).
 */
export function formToTentRulesPatch(data: TentRulesFormData, stored: LocationLighting | null | undefined): TentRulesPatch {
  const fixture = stored?.fixture_geometry ?? null;
  const empty = data.lamp_height_cm === null && data.canopy_distance_cm === null && fixture === null;
  return {
    adjacency_factor: data.adjacency_factor,
    lighting: empty
      ? null
      : {
          ...(data.lamp_height_cm !== null ? { lamp_height_cm: data.lamp_height_cm } : {}),
          ...(data.canopy_distance_cm !== null ? { canopy_distance_cm: data.canopy_distance_cm } : {}),
          ...(fixture !== null ? { fixture_geometry: fixture } : {}),
        },
  };
}
