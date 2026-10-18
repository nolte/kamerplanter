import type { ChipProps } from '@mui/material/Chip';
import type { BedStatus } from '../model/types';

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

/** Whether `value` lies before today (a due date that has passed). */
export function isOverdue(value: string | null | undefined, now: Date = new Date()): boolean {
  if (!value) return false;
  const date = new Date(value);
  return !Number.isNaN(date.getTime()) && date.getTime() < now.getTime();
}
