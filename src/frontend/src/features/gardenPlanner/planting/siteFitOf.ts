import type { Species } from '@/api/types';
import { assessSiteFit, type LightRequirement, type SiteFitResult } from '../model/siteFit';
import type { SunExposure } from '../model/types';

/** What the planting dialog shows for one species on this bed (GP-FR-160); `null` = no hint to show. */
export interface SpeciesSiteFit {
  lightRequirement: LightRequirement;
  shadeTolerance: string | null;
  result: SiteFitResult;
}

/**
 * The `site_fit` of a species on a bed, or `null` when there is nothing to say: no species, an unknown
 * sun class on the bed or no recorded `light_requirement` give no hint at all (GP-FR-160 - an unknown is
 * not a green light). `shade_tolerance` never stands in for the requirement (E-05).
 */
export function siteFitOf(species: Species | undefined, sunExposure: SunExposure): SpeciesSiteFit | null {
  const requirement = species?.light_requirement ?? null;
  if (!species || requirement === null) return null;
  const result = assessSiteFit(sunExposure, requirement, species.shade_tolerance ?? null);
  if (result.fit === 'unknown') return null;
  return { lightRequirement: requirement, shadeTolerance: species.shade_tolerance ?? null, result };
}
