import type { SiteConditionsPatch, SiteConditionsSlice } from './types';

/** Lays `next` over `previous`; the microclimate keys merge, every other key is replaced. */
export function mergeSitePatch(previous: SiteConditionsPatch, next: SiteConditionsPatch): SiteConditionsPatch {
  const merged: SiteConditionsPatch = { ...previous, ...next };
  if (previous.microclimate || next.microclimate) {
    merged.microclimate = { ...previous.microclimate, ...next.microclimate };
  }
  return merged;
}

const sameSides = (a: readonly string[], b: readonly string[]) =>
  a.length === b.length && [...a].sort().join() === [...b].sort().join();

/**
 * Only the keys that differ from what is stored go out (a key set back to its stored value drops out); the
 * defaults a missing stored value stands for are `unknown`, `false`, `null` and no sides.
 */
export function changedSitePatch(stored: SiteConditionsSlice | null | undefined, patch: SiteConditionsPatch): SiteConditionsPatch {
  const out: SiteConditionsPatch = {};
  const micro = patch.microclimate;
  if (micro) {
    const changed: NonNullable<SiteConditionsPatch['microclimate']> = {};
    if (micro.frost_risk !== undefined && micro.frost_risk !== (stored?.microclimate?.frost_risk ?? 'unknown')) {
      changed.frost_risk = micro.frost_risk;
    }
    if (
      micro.cold_air_pocket !== undefined &&
      micro.cold_air_pocket !== (stored?.microclimate?.cold_air_pocket ?? false)
    ) {
      changed.cold_air_pocket = micro.cold_air_pocket;
    }
    if (
      micro.heat_retention !== undefined &&
      micro.heat_retention !== (stored?.microclimate?.heat_retention ?? 'unknown')
    ) {
      changed.heat_retention = micro.heat_retention;
    }
    if (Object.keys(changed).length > 0) out.microclimate = changed;
  }
  if (patch.wind_exposure !== undefined && patch.wind_exposure !== (stored?.wind_exposure ?? 'unknown')) {
    out.wind_exposure = patch.wind_exposure;
  }
  if (patch.slope_deg !== undefined && patch.slope_deg !== (stored?.slope_deg ?? null)) out.slope_deg = patch.slope_deg;
  if (patch.aspect_deg !== undefined && patch.aspect_deg !== (stored?.aspect_deg ?? null)) {
    out.aspect_deg = patch.aspect_deg;
  }
  if (patch.access_sides !== undefined && !sameSides(patch.access_sides, stored?.access_sides ?? [])) {
    out.access_sides = patch.access_sides;
  }
  return out;
}

/** The slice as the patch would leave it: what the editors show while the change is not yet stored. */
export function appliedSitePatch(stored: SiteConditionsSlice | null | undefined, patch: SiteConditionsPatch): SiteConditionsSlice {
  return {
    ...stored,
    ...patch,
    microclimate: { ...stored?.microclimate, ...patch.microclimate },
  };
}
