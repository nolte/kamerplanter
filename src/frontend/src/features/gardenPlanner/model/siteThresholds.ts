/**
 * The garden-planning thresholds of a site (REQ-053 GP-FR-164/166, WP 8.24): the sun-class bounds with their
 * reference day and the reach thresholds. The backend answers the effective values on every site; the defaults
 * here are the fallback while the site loads, when it cannot be read, or for an older backend that does not
 * send them. They mirror `app/domain/models/site.py` (RHS classes, confirmed O-17; reach from
 * `app/domain/calculators/reach_calculator.py`). Pure: no I/O, no React.
 */
import type { ReachThresholds, Site, SunClassThresholds } from '@/api/types';
import { REACH_BOTH_SIDES_M, REACH_ONE_SIDE_M, type ReachThresholds as ReachOptions } from './reach';

/** RHS sun classes on midsummer, 21 June: > 6 h, 3-6 h, 2-3 h, < 2 h of direct sun. */
export const DEFAULT_SUN_CLASS_THRESHOLDS: Readonly<SunClassThresholds> = Object.freeze({
  full_sun_min_hours: 6,
  partial_shade_min_hours: 3,
  shade_min_hours: 2,
  reference_month: 6,
  reference_day: 21,
});

/** 1.2 m with access from two opposite sides, 0.6 m from one side. */
export const DEFAULT_REACH_THRESHOLDS: Readonly<ReachThresholds> = Object.freeze({
  both_sides_m: REACH_BOTH_SIDES_M,
  one_side_m: REACH_ONE_SIDE_M,
});

export interface SiteThresholds {
  sun: Readonly<SunClassThresholds>;
  reach: Readonly<ReachThresholds>;
}

/** The site's thresholds, each part falling back to its defaults when the site has none. */
export function siteThresholds(site: Pick<Site, 'sun_class_thresholds' | 'reach_thresholds'> | null | undefined): SiteThresholds {
  return {
    sun: site?.sun_class_thresholds ?? DEFAULT_SUN_CLASS_THRESHOLDS,
    reach: site?.reach_thresholds ?? DEFAULT_REACH_THRESHOLDS,
  };
}

/** The reach thresholds in the option shape of `assessReach`. */
export function reachOptions(reach: Readonly<ReachThresholds>): ReachOptions {
  return { bothSidesM: reach.both_sides_m, oneSideM: reach.one_side_m };
}
