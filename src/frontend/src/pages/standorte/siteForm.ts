import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import type { TFunction } from 'i18next';
import type { SiteType } from '@/api/types';

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

export const siteFormSchema = z.object({
  name: z.string().min(1),
  type: z.enum(SITE_TYPE_VALUES),
  gps_lat: coordinate,
  gps_lon: coordinate,
  climate_zone: z.string(),
  total_area_m2: z.number().min(0),
  timezone: z.string(),
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
    }),
  );
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
