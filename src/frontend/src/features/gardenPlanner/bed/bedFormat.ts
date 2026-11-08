import type { ChipProps } from '@mui/material/Chip';
import type { TFunction } from 'i18next';
import type { BedStatus } from '../model/types';
import type { SiteConditionsSlice, SunProfile } from './types';

/** Chip colour of a bed status: planned = neutral, active = positive, retired = muted. */
export const BED_STATUS_COLOR: Record<BedStatus, ChipProps['color']> = {
  planned: 'info',
  active: 'success',
  retired: 'default',
};

/** An ISO timestamp as a short local date; `null` when absent or unreadable. */
export function formatBedDate(value: string | null | undefined, language: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat(language, { dateStyle: 'medium' }).format(date);
}

export { isOverdue } from '../model/overdue';

/**
 * One line for the bed summary: "Sun from: Morning · about 6 h of direct sun · Leaf shade in summer"
 * (GP-FR-158/159). Only what was recorded appears; `null` when nothing was (no "unknown" noise).
 */
export function sunProfileLine(t: TFunction, profile: SunProfile | null | undefined): string | null {
  if (!profile) return null;
  const parts: string[] = [];
  if (profile.sun_window && profile.sun_window !== 'unknown') {
    parts.push(t('pages.gardenPlan.sun.window.summary', { window: t(`pages.gardenPlan.sun.window.options.${profile.sun_window}`) }));
  }
  if (profile.direct_sun_hours_summer !== null && profile.direct_sun_hours_summer !== undefined) {
    parts.push(t('pages.gardenPlan.sun.hours.summary', { hours: profile.direct_sun_hours_summer }));
  }
  if (profile.foliage_shade_in_summer) parts.push(t('pages.gardenPlan.sun.foliage.label'));
  return parts.length > 0 ? parts.join(' · ') : null;
}

/**
 * The names of the competition flags (GP-FR-165) in the order given, each once. A value this client does not know
 * (a newer server) reads as a neutral "Other report", never as a raw i18n key.
 */
function siteFlagLabels(t: TFunction, flags: readonly string[] | null | undefined): string[] {
  const other = t('pages.gardenPlan.siteConditions.flags.other');
  return [...new Set((flags ?? []).map((flag) => t(`enums.siteFlag.${flag}`, { defaultValue: other })))];
}

/**
 * "Allelopathy risk reported at this site" - naming exactly the flags that are set, combined when there are two
 * (GP-FR-165); `null` without a flag. A note, never a rating: nothing is derived from it.
 */
export function siteFlagsLine(t: TFunction, flags: readonly string[] | null | undefined): string | null {
  const labels = siteFlagLabels(t, flags);
  return labels.length > 0 ? t('pages.gardenPlan.siteConditions.flags.reported', { value: labels.join('/') }) : null;
}

/**
 * One line with the site conditions that were recorded (GP-FR-162/163/165/168): frost risk, cold-air pocket, stored
 * heat, wind, slope, aspect, access sides and competition flags. Only what was entered appears (`unknown` and absent are left out);
 * `null` when nothing was.
 */
export function siteConditionsLine(t: TFunction, conditions: SiteConditionsSlice | null | undefined): string | null {
  if (!conditions) return null;
  const parts: string[] = [];
  const risk = conditions.microclimate?.frost_risk;
  if (risk && risk !== 'unknown') {
    parts.push(t('pages.gardenPlan.siteConditions.summary.frost', { value: t(`enums.frostRisk.${risk}`) }));
  }
  if (conditions.microclimate?.cold_air_pocket) parts.push(t('pages.gardenPlan.siteConditions.coldAirPocket.label'));
  const heat = conditions.microclimate?.heat_retention;
  if (heat && heat !== 'unknown') {
    parts.push(t('pages.gardenPlan.siteConditions.summary.heat', { value: t(`enums.heatRetention.${heat}`) }));
  }
  const wind = conditions.wind_exposure;
  if (wind && wind !== 'unknown') {
    parts.push(t('pages.gardenPlan.siteConditions.summary.wind', { value: t(`enums.windExposure.${wind}`) }));
  }
  if (conditions.slope_deg !== null && conditions.slope_deg !== undefined) {
    parts.push(t('pages.gardenPlan.siteConditions.summary.slope', { value: conditions.slope_deg }));
  }
  if (conditions.aspect_deg !== null && conditions.aspect_deg !== undefined) {
    parts.push(t('pages.gardenPlan.siteConditions.summary.aspect', { value: conditions.aspect_deg }));
  }
  if (conditions.access_sides && conditions.access_sides.length > 0) {
    parts.push(
      t('pages.gardenPlan.siteConditions.summary.access', {
        value: conditions.access_sides.map((side) => t(`enums.accessSide.${side}`)).join(', '),
      }),
    );
  }
  const flags = siteFlagLabels(t, conditions.flags);
  if (flags.length > 0) parts.push(t('pages.gardenPlan.siteConditions.summary.flags', { value: flags.join(', ') }));
  return parts.length > 0 ? parts.join(' · ') : null;
}

/** The two places the water distance is written; each has its own sentence around the number. */
const WATER_SOURCE_KEY = {
  header: 'pages.bed.header.waterSourceDistance',
  list: 'pages.bed.list.waterSourceDistance',
} as const;

/**
 * The distance to the nearest water source as the bed head and the bed list show it (GP-FR-167): two decimals at
 * most, and "Right at the bed" for every distance that would read as 0 at that precision - a tap 3 mm off the edge is
 * at the bed, not "0 m" away. `null` without a value (no source, or no geometry): nothing to show, never "0 m".
 */
export function waterSourceText(
  t: TFunction,
  language: string,
  metres: number | null | undefined,
  place: keyof typeof WATER_SOURCE_KEY,
): string | null {
  if (metres === null || metres === undefined || !Number.isFinite(metres)) return null;
  const shown = Number(metres.toFixed(2));
  if (shown === 0) return t('pages.bed.header.waterSourceAtBed');
  const distance = new Intl.NumberFormat(language, { maximumFractionDigits: 2 }).format(shown);
  return t(WATER_SOURCE_KEY[place], { distance });
}

/**
 * A comparator for a nullable number column of a `DataTable`, which multiplies the comparator by the direction: a
 * missing value stays **last in both directions** (the sign of the null comparison is flipped for `desc`, so the
 * table's flip restores it), the values themselves sort by the direction.
 */
export function compareNullableLast(
  a: number | null | undefined,
  b: number | null | undefined,
  direction: 'asc' | 'desc',
): number {
  const aMissing = a === null || a === undefined;
  const bMissing = b === null || b === undefined;
  if (aMissing || bMissing) {
    const nulls = (aMissing ? 1 : 0) - (bMissing ? 1 : 0);
    return direction === 'asc' ? nulls : -nulls;
  }
  return a - b;
}
