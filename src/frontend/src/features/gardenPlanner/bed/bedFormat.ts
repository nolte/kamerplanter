import type { ChipProps } from '@mui/material/Chip';
import type { TFunction } from 'i18next';
import type { BedStatus } from '../model/types';
import type { SunProfile } from './types';

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
