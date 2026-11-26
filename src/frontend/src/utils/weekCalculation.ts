import { utcCalendarDaysBetween } from '@/utils/calendarDay';
import { formatMonthName } from '@/utils/formatting';

export const MS_PER_WEEK = 7 * 24 * 60 * 60 * 1000;

/**
 * Calculate the current plan week (1-based) relative to the epoch date, counted in UTC calendar days —
 * the clock the server uses for the same value (`calendar_aggregation_engine._resolve_dosage_metadata`,
 * BACKEND.md §12a). `undefined` for an unreadable or future epoch.
 */
export function computeCurrentWeek(epoch: string, now: Date = new Date()): number | undefined {
  const days = utcCalendarDaysBetween(epoch, now);
  if (days === undefined || days < 0) return undefined;
  return Math.floor(days / 7) + 1;
}

/** Calculate the current day (1-based) relative to the epoch date, counted in UTC calendar days. */
export function computeCurrentDay(epoch: string, now: Date = new Date()): number | undefined {
  const days = utcCalendarDaysBetween(epoch, now);
  if (days === undefined || days < 0) return undefined;
  return days + 1;
}

/**
 * The nutrient-plan week of a planting run, by the server's rule (#3016).
 *
 * Mirrors `GET /planting-runs/{key}/active-channels` without `current_week`
 * (`api/v1/planting_runs/tenant_router.py`, `get_active_channels`): whole UTC calendar days since the
 * UTC day of `started_at`, `max(1, days // 7 + 1)`; a run that has not started is in week 1. The server
 * picks the run's dosages for exactly this week, so the week the page shows must be this one.
 */
export function computeRunElapsedWeek(
  startedAt: string | null | undefined,
  now: Date = new Date(),
): number | undefined {
  if (!startedAt) return 1;
  const days = utcCalendarDaysBetween(startedAt, now);
  if (days === undefined) return undefined;
  return Math.max(1, Math.floor(days / 7) + 1);
}

/** Approximate mapping of ISO calendar weeks to months (sums to 52). */
export interface MonthWeekSpan {
  /** 0-based month index (0=Jan, 11=Dec) */
  month: number;
  weekStart: number;
  weekEnd: number;
  /** Number of week-columns this month spans */
  span: number;
}

export const MONTH_WEEK_SPANS: MonthWeekSpan[] = [
  { month: 0,  weekStart: 1,  weekEnd: 4,  span: 4 },  // Jan
  { month: 1,  weekStart: 5,  weekEnd: 8,  span: 4 },  // Feb
  { month: 2,  weekStart: 9,  weekEnd: 13, span: 5 },  // Mar
  { month: 3,  weekStart: 14, weekEnd: 17, span: 4 },  // Apr
  { month: 4,  weekStart: 18, weekEnd: 22, span: 5 },  // May
  { month: 5,  weekStart: 23, weekEnd: 26, span: 4 },  // Jun
  { month: 6,  weekStart: 27, weekEnd: 30, span: 4 },  // Jul
  { month: 7,  weekStart: 31, weekEnd: 35, span: 5 },  // Aug
  { month: 8,  weekStart: 36, weekEnd: 39, span: 4 },  // Sep
  { month: 9,  weekStart: 40, weekEnd: 43, span: 4 },  // Oct
  { month: 10, weekStart: 44, weekEnd: 48, span: 5 },  // Nov
  { month: 11, weekStart: 49, weekEnd: 52, span: 4 },  // Dec
];

/** Get the short month name for a 0-based month index in the active UI language. */
export function getShortMonthName(monthIndex: number): string {
  return formatMonthName(monthIndex + 1, 'short');
}
