/**
 * The one definition of "overdue" (REQ-053 GP-FR-192, operator decision #2435 item 6 / #2455 item 4, #2461).
 *
 * A task is overdue when its due day lies before today, both read as UTC calendar days; a task due today is
 * not overdue, whatever the time of day. Pure: `now` is an argument. The Python twin is
 * `domain/calculators/overdue_calculator.py`; both run against the operation `overdue` of
 * `garden-plan-vectors.json`. The bed list column, the care tab, the badge text and field mode all call this.
 */

/** The UTC calendar day (`YYYY-MM-DD`) of an ISO value; a value without a zone is read as UTC. `null` when absent or unreadable. */
export function utcDayOfValue(value: string | null | undefined): string | null {
  if (!value) return null;
  const zoned = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value) || !/T/.test(value) ? value : `${value}Z`;
  const time = Date.parse(zoned);
  if (Number.isNaN(time)) return null;
  return new Date(time).toISOString().slice(0, 10);
}

/** Whether a task due at `due` is overdue at `now` (due UTC day < today's UTC day). */
export function isOverdue(due: string | null | undefined, now: Date | string = new Date()): boolean {
  const day = utcDayOfValue(due);
  if (day === null) return false;
  const instant = typeof now === 'string' ? new Date(now) : now;
  return day < instant.toISOString().slice(0, 10);
}
