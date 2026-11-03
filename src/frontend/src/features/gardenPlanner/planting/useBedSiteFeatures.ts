import { useMemo } from 'react';
import type { BedListItem } from '../bed/types';
import type { BedSiteFeatures } from './siteFitOf';

/** The frost risk, wind and drainage of a bed from the bed document (GP-FR-161); a stable object per value set. */
export function useBedSiteFeatures(bed: Pick<BedListItem, 'site_conditions' | 'soil_profile'>): BedSiteFeatures {
  const frostRisk = bed.site_conditions?.microclimate?.frost_risk;
  const windExposure = bed.site_conditions?.wind_exposure;
  const drainage = bed.soil_profile?.drainage;
  return useMemo(() => ({ frostRisk, windExposure, drainage }), [frostRisk, windExposure, drainage]);
}
