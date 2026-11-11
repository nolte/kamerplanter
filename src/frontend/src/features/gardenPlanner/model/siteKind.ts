/**
 * Garden plan or indoor plan (REQ-053 §9.8, GP-FR-182/183, WP 10.8). The plan response names its site type; a flat,
 * a windowsill and a grow tent make it an indoor plan: weather, frost and wind are hidden, the bed list reads
 * "Pflanzplätze", and the empty plan invites to draw the flat or to load a photo of it.
 *
 * The set mirrors the backend `INDOOR_PLAN_SITE_TYPES` - every site type that is not weather-relevant
 * (`WEATHER_RELEVANT_SITE_TYPES`, `pages/standorte/siteForm.ts`); `siteKind.test.ts` pins that the two sets split
 * the site types between them. Pure: no I/O, no React.
 */
import type { SiteType } from '@/api/types';

export const INDOOR_PLAN_SITE_TYPES: readonly SiteType[] = ['indoor', 'windowsill', 'grow_tent'] as const;

/**
 * Whether a plan of this site type is an indoor plan. An unknown type (`null`/absent: a plan cached before the
 * response carried it, a hand-built model) is a garden plan - the behaviour every plan had before.
 */
export function isIndoorPlanSite(type: SiteType | null | undefined): boolean {
  return type != null && INDOOR_PLAN_SITE_TYPES.includes(type);
}
