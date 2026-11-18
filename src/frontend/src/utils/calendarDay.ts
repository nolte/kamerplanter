/**
 * Calendar days (`YYYY-MM-DD`) — the one place that turns an instant into a day (#3016).
 *
 * There are exactly two calendars in this application, and every caller has to say which one it means:
 *
 * - **Local** ({@link toLocalIsoDate}): the day on the user's wall clock. Every date a user *enters* —
 *   `planted_on`, `purchase_date`, `mixed_on`, a run's planned start — defaults to this. Between 00:00 and
 *   02:00 CEST the UTC day is still yesterday, so cutting the date off `new Date().toISOString()` used to
 *   pre-fill the wrong date.
 * - **UTC** ({@link toUtcIsoDate}, {@link utcDayOf}, {@link utcCalendarDaysBetween}): the server's clock.
 *   The backend derives every "today" from `today_utc()` (BACKEND.md §12a); a client value that has to agree
 *   with a server decision — the active nutrient week, "not in the future", "overdue" — mirrors that clock.
 *
 * Cutting the date part off `toISOString()` does not say which one it means, which is how the wrong one
 * kept getting picked; `src/test/guards/calendarDayHasOneHelper.test.ts` refuses it in production code.
 */

const MS_PER_DAY = 24 * 60 * 60 * 1000;

function pad(value: number, width = 2): string {
  return String(value).padStart(width, '0');
}

/** The user's local calendar day of `date` (default: now) as `YYYY-MM-DD`. */
export function toLocalIsoDate(date: Date = new Date()): string {
  return `${pad(date.getFullYear(), 4)}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** The UTC calendar day of `date` (default: now) as `YYYY-MM-DD` — the day the server calls "today". */
export function toUtcIsoDate(date: Date = new Date()): string {
  return `${pad(date.getUTCFullYear(), 4)}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}`;
}

/**
 * The UTC calendar day of an ISO value, read the way the backend reads it: a value without a zone
 * (`2026-03-10T23:30:00`) is UTC, a bare date (`2026-03-10`) is that day. `null` when absent or unreadable.
 */
export function utcDayOf(value: string | Date | null | undefined): string | null {
  if (value == null || value === '') return null;
  let time: number;
  if (value instanceof Date) {
    time = value.getTime();
  } else {
    const zoned = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value) || !value.includes('T') ? value : `${value}Z`;
    time = Date.parse(zoned);
  }
  if (Number.isNaN(time)) return null;
  return toUtcIsoDate(new Date(time));
}

/**
 * Whole UTC calendar days from `start` to `end` (default: now; negative when `start` lies ahead), or
 * `undefined` when either is absent or unreadable. Mirrors `(today_utc() - started.date()).days` on the server.
 */
export function utcCalendarDaysBetween(
  start: string | Date | null | undefined,
  end: string | Date = new Date(),
): number | undefined {
  const startDay = utcDayOf(start);
  const endDay = utcDayOf(end);
  if (startDay === null || endDay === null) return undefined;
  const from = Date.parse(`${startDay}T00:00:00Z`);
  const to = Date.parse(`${endDay}T00:00:00Z`);
  return Math.round((to - from) / MS_PER_DAY);
}
