/**
 * "Due" and "overdue" in field mode (REQ-053 GP-UX-030, §18.1 step 4). Pure: `today` is an argument.
 *
 * Operator decision (WP 5.1): a task is overdue when its due day - the UTC calendar day of `due_date` -
 * lies before today's UTC calendar day; a task due today is not overdue, whatever the time of day. This
 * is the rule of the plant state (`model/plantState.ts`, `due < today` on UTC days), so the sheet, the
 * list and the plant markers never disagree.
 */
import type { BedListItem } from '../bed/types';
import type { CareTask } from '../care/careTypes';

/** The UTC calendar day (`YYYY-MM-DD`) of an ISO value, or `null` when it is absent or unreadable. */
export function utcDayOf(value: string | null | undefined): string | null {
  if (!value) return null;
  const time = Date.parse(value);
  if (Number.isNaN(time)) return null;
  return new Date(time).toISOString().slice(0, 10);
}

/** Today as a UTC calendar day. */
export function todayUtc(now: Date = new Date()): string {
  return now.toISOString().slice(0, 10);
}

/** Overdue: the due day lies before `today` (both UTC calendar days). */
export function isOverdueOn(due: string | null | undefined, today: string): boolean {
  const day = utcDayOf(due);
  return day !== null && day < today;
}

/** Due today or earlier: what "heute fällig" counts. */
export function isDueBy(due: string | null | undefined, today: string): boolean {
  const day = utcDayOf(due);
  return day !== null && day <= today;
}

export interface FieldTaskSections {
  overdue: CareTask[];
  today: CareTask[];
  later: CareTask[];
}

function byDue(a: CareTask, b: CareTask): number {
  const left = utcDayOf(a.due_date) ?? '9999-12-31';
  const right = utcDayOf(b.due_date) ?? '9999-12-31';
  if (left !== right) return left < right ? -1 : 1;
  return a.key < b.key ? -1 : a.key > b.key ? 1 : 0;
}

/**
 * The tasks of the sheet: overdue first, then due today, then the rest by due day. System suggestions stay
 * in the care tab of the bed view - the field shows what was planned.
 */
export function fieldTaskSections(tasks: readonly CareTask[], today: string): FieldTaskSections {
  const sections: FieldTaskSections = { overdue: [], today: [], later: [] };
  for (const task of [...tasks].sort(byDue)) {
    if (task.suggested) continue;
    if (isOverdueOn(task.due_date, today)) sections.overdue.push(task);
    else if (isDueBy(task.due_date, today)) sections.today.push(task);
    else sections.later.push(task);
  }
  return sections;
}

/** Whether a bed of the list has something to do today: an overdue task or one due today. */
export function bedIsDue(bed: BedListItem, today: string): boolean {
  return (bed.overdue_task_count ?? 0) > 0 || isDueBy(bed.next_due_at, today);
}

/**
 * The order of "My beds · due today" (GP-UX-030: by assignment and due date): the signed-in user's beds
 * first, then beds with overdue tasks (most first), then by the next due day, then by name. Retired beds
 * are not field work and are dropped.
 */
export function sortFieldBeds(
  beds: readonly BedListItem[],
  mine: ReadonlySet<string>,
  today: string,
  language: string,
): BedListItem[] {
  const collator = new Intl.Collator(language, { sensitivity: 'base', numeric: true });
  return beds
    .filter((bed) => bed.bed_status !== 'retired')
    .sort((a, b) => {
      const ownA = mine.has(a.key) ? 0 : 1;
      const ownB = mine.has(b.key) ? 0 : 1;
      if (ownA !== ownB) return ownA - ownB;
      const dueA = bedIsDue(a, today) ? 0 : 1;
      const dueB = bedIsDue(b, today) ? 0 : 1;
      if (dueA !== dueB) return dueA - dueB;
      const overdue = (b.overdue_task_count ?? 0) - (a.overdue_task_count ?? 0);
      if (overdue !== 0) return overdue;
      const nextA = utcDayOf(a.next_due_at) ?? '9999-12-31';
      const nextB = utcDayOf(b.next_due_at) ?? '9999-12-31';
      if (nextA !== nextB) return nextA < nextB ? -1 : 1;
      return collator.compare(a.name, b.name);
    });
}
