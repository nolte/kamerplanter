import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import type { TFunction } from 'i18next';
import type { ReachThresholds, Site, SiteType, SunClassThresholds } from '@/api/types';
import {
  DEFAULT_REACH_THRESHOLDS,
  DEFAULT_SUN_CLASS_THRESHOLDS,
} from '@/features/gardenPlanner/model/siteThresholds';

/**
 * Shared form contract for the site create dialog and the site detail edit form
 * (REQ-046 follow-up). Both surfaces must expose the site `type` and the
 * `gps_coordinates`, otherwise the per-site weather-source section can never be
 * reached (it only renders for outdoor/greenhouse sites that carry GPS).
 */

/** All selectable site types, mirrored from the backend `SiteType` enum. */
export const SITE_TYPE_VALUES: readonly SiteType[] = [
  'outdoor',
  'greenhouse',
  'indoor',
  'windowsill',
  'balcony',
  'grow_tent',
] as const;

/**
 * Single source of truth for the "outdoor / weather-relevant" site types — the
 * types for which GPS coordinates, weather sources and frost warnings apply
 * (REQ-002/REQ-046). It mirrors the backend `WEATHER_RELEVANT_SITE_TYPES` (and,
 * by the same reasoning, `OVERWINTERING_SITE_TYPES`): a frost-exposed outdoor
 * location is exactly one whose local weather drives plant care.
 *
 * `balcony` is included — a balcony is a frost-exposed outdoor spot, so its
 * plants benefit from weather/frost data just like ground/greenhouse ones.
 * `indoor` / `windowsill` / `grow_tent` stay excluded (climate-controlled).
 *
 * Replaces the scattered `type === 'outdoor' || type === 'greenhouse'` checks
 * that previously omitted `balcony`, contradicting the frost classification.
 */
export const WEATHER_RELEVANT_SITE_TYPES: readonly SiteType[] = [
  'outdoor',
  'greenhouse',
  'balcony',
] as const;

/** Whether GPS/weather/frost features apply to a given site type. */
export function isWeatherRelevantSiteType(type: SiteType | undefined | null): boolean {
  return type != null && WEATHER_RELEVANT_SITE_TYPES.includes(type);
}

/**
 * A GPS coordinate input: either a number or the empty string (field cleared).
 * Both coordinates empty ⇒ no GPS at all; both filled ⇒ a `[lat, lon]` tuple.
 */
const coordinate = z.union([z.literal(''), z.number()]);

/** Upper bounds of the garden-planning thresholds, as the backend models them (WP 8.24). */
const MAX_SUN_HOURS = 24;
const MAX_REACH_M = 1000;

/** Hours of direct sun: more than 0, at most a day (GP-FR-164). */
const sunHours = z.number().gt(0).max(MAX_SUN_HOURS);
/** A reach threshold in metres: more than 0 (GP-FR-166). */
const reachMetres = z.number().gt(0).max(MAX_REACH_M);

export const siteFormSchema = z.object({
  name: z.string().min(1),
  type: z.enum(SITE_TYPE_VALUES),
  gps_lat: coordinate,
  gps_lon: coordinate,
  climate_zone: z.string(),
  total_area_m2: z.number().min(0),
  timezone: z.string(),
  // REQ-053 GP-FR-164/166 (WP 8.24): the garden-planning thresholds of the site.
  sun_class_thresholds: z.object({
    full_sun_min_hours: sunHours,
    partial_shade_min_hours: sunHours,
    shade_min_hours: sunHours,
    reference_month: z.number().int().min(1).max(12),
    reference_day: z.number().int().min(1).max(31),
  }),
  reach_thresholds: z.object({
    both_sides_m: reachMetres,
    one_side_m: reachMetres,
  }),
});

export type SiteFormData = z.infer<typeof siteFormSchema>;

const GPS_LAT_MIN = -90;
const GPS_LAT_MAX = 90;
const GPS_LON_MIN = -180;
const GPS_LON_MAX = 180;

/**
 * Builds the resolver with the cross-field GPS validation (matches the backend
 * `Site.validate_gps`): coordinates come as a pair and stay within range. The
 * messages are translated, so the resolver is built per-render with `t`.
 */
export function buildSiteResolver(t: TFunction) {
  return zodResolver(
    siteFormSchema.superRefine((data, ctx) => {
      const latSet = data.gps_lat !== '';
      const lonSet = data.gps_lon !== '';
      if (latSet !== lonSet) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: [latSet ? 'gps_lon' : 'gps_lat'],
          message: t('pages.sites.gpsBothRequired'),
        });
      }
      if (latSet && (Number(data.gps_lat) < GPS_LAT_MIN || Number(data.gps_lat) > GPS_LAT_MAX)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['gps_lat'],
          message: t('pages.sites.gpsLatRange'),
        });
      }
      if (lonSet && (Number(data.gps_lon) < GPS_LON_MIN || Number(data.gps_lon) > GPS_LON_MAX)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['gps_lon'],
          message: t('pages.sites.gpsLonRange'),
        });
      }
      refineThresholds(data, ctx, t);
    }),
  );
}

/**
 * The cross-field rules of the thresholds, as the backend models them (`SunClassThresholds`,
 * `ReachThresholds`): the sun-class bounds strictly descending, the reference day a real day of the
 * year, one-side reach not above two-side reach. The server answers 422 to the same values.
 */
function refineThresholds(data: SiteFormData, ctx: z.RefinementCtx, t: TFunction): void {
  const sun = data.sun_class_thresholds;
  if (!(sun.full_sun_min_hours > sun.partial_shade_min_hours)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['sun_class_thresholds', 'partial_shade_min_hours'],
      message: t('pages.sites.thresholds.partialBelowFull'),
    });
  }
  if (!(sun.partial_shade_min_hours > sun.shade_min_hours)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['sun_class_thresholds', 'shade_min_hours'],
      message: t('pages.sites.thresholds.shadeBelowPartial'),
    });
  }
  if (!isDayOfYear(sun.reference_month, sun.reference_day)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['sun_class_thresholds', 'reference_day'],
      message: t('pages.sites.thresholds.noSuchDay'),
    });
  }
  const reach = data.reach_thresholds;
  if (reach.one_side_m > reach.both_sides_m) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ['reach_thresholds', 'one_side_m'],
      message: t('pages.sites.thresholds.oneAboveBoth'),
    });
  }
}

/** Whether month and day name a day of a leap year (29 February counts). */
export function isDayOfYear(month: number, day: number): boolean {
  if (!Number.isInteger(month) || !Number.isInteger(day)) return false;
  const date = new Date(Date.UTC(2000, month - 1, day));
  return date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}

/** The form values of the thresholds from what the site answered; the defaults where it sent none. */
export function thresholdsToFields(
  site: Pick<Site, 'sun_class_thresholds' | 'reach_thresholds'> | null | undefined,
): Pick<SiteFormData, 'sun_class_thresholds' | 'reach_thresholds'> {
  return {
    sun_class_thresholds: { ...(site?.sun_class_thresholds ?? DEFAULT_SUN_CLASS_THRESHOLDS) },
    reach_thresholds: { ...(site?.reach_thresholds ?? DEFAULT_REACH_THRESHOLDS) },
  };
}

function sameValues<T extends object>(a: T, b: T): boolean {
  return (Object.keys(a) as (keyof T)[]).every((key) => a[key] === b[key]);
}

/**
 * The thresholds the edit sends: a part the user did not change goes out as `null`, which keeps what is stored
 * (the server stores nothing for a site that never had them, so a later change of the defaults reaches it).
 */
export function thresholdsToPayload(
  data: Pick<SiteFormData, 'sun_class_thresholds' | 'reach_thresholds'>,
  site: Pick<Site, 'sun_class_thresholds' | 'reach_thresholds'> | null | undefined,
): { sun_class_thresholds: SunClassThresholds | null; reach_thresholds: ReachThresholds | null } {
  const before = thresholdsToFields(site);
  return {
    sun_class_thresholds: sameValues(data.sun_class_thresholds, before.sun_class_thresholds)
      ? null
      : data.sun_class_thresholds,
    reach_thresholds: sameValues(data.reach_thresholds, before.reach_thresholds) ? null : data.reach_thresholds,
  };
}

/** Maps the two coordinate fields to the API `gps_coordinates` tuple (or null). */
export function gpsToPayload(data: SiteFormData): [number, number] | null {
  if (data.gps_lat === '' || data.gps_lon === '') return null;
  return [Number(data.gps_lat), Number(data.gps_lon)];
}

/** Maps an API `gps_coordinates` tuple back to the two form coordinate fields. */
export function gpsToFields(
  gps: [number, number] | null | undefined,
): { gps_lat: number | ''; gps_lon: number | '' } {
  if (!gps) return { gps_lat: '', gps_lon: '' };
  return { gps_lat: gps[0], gps_lon: gps[1] };
}

/** Builds the translated `<Select>` options for the site type field. */
export function siteTypeOptions(t: TFunction): { value: SiteType; label: string }[] {
  return SITE_TYPE_VALUES.map((value) => ({
    value,
    label: t(`enums.siteType.${value}`),
  }));
}
