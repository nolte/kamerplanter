import type { Species } from '@/api/types';
import { assessSiteAxes, assessSiteFit, type LightRequirement, type SiteAxisHint, type SiteFitResult } from '../model/siteFit';
import type { FrostRisk, SoilDrainage, SunExposure, WindExposure } from '../model/types';

/** The bed features beyond the sun class that the axis hints read (GP-FR-161); absent = unknown. */
export interface BedSiteFeatures {
  frostRisk?: FrostRisk;
  windExposure?: WindExposure;
  drainage?: SoilDrainage;
}

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

/**
 * The axis hints (frost, wind, waterlogging) of a species on a bed (GP-FR-161), in the fixed order of the
 * calculator; empty = nothing to say. Independent of the light requirement: a species without one still
 * gets its frost or drainage hint.
 */
export function siteAxesOf(species: Species | undefined, bed: BedSiteFeatures | undefined): SiteAxisHint[] {
  if (!species || !bed) return [];
  return assessSiteAxes(
    bed.frostRisk,
    species.frost_sensitivity,
    bed.windExposure,
    species.support_required,
    bed.drainage,
    species.waterlogging_tolerance,
  );
}
