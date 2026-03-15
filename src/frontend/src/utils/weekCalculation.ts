export const MS_PER_WEEK = 7 * 24 * 60 * 60 * 1000;
const MS_PER_DAY = 24 * 60 * 60 * 1000;

/** Calculate the current plan week relative to the epoch date. */
export function computeCurrentWeek(epoch: string): number | undefined {
  const start = new Date(epoch);
  if (isNaN(start.getTime())) return undefined;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  start.setHours(0, 0, 0, 0);
  const diffMs = now.getTime() - start.getTime();
  if (diffMs < 0) return undefined;
  return Math.floor(diffMs / MS_PER_WEEK) + 1;
}

/** Calculate the current day (1-based) relative to the epoch date. */
export function computeCurrentDay(epoch: string): number | undefined {
  const start = new Date(epoch);
  if (isNaN(start.getTime())) return undefined;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  start.setHours(0, 0, 0, 0);
  const diffMs = now.getTime() - start.getTime();
  if (diffMs < 0) return undefined;
  return Math.floor(diffMs / MS_PER_DAY) + 1;
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

/** Get short month name for a 0-based month index in the given locale. */
export function getShortMonthName(monthIndex: number, locale: string): string {
  return new Date(2026, monthIndex).toLocaleDateString(locale, { month: 'short' });
}
