export const MS_PER_WEEK = 7 * 24 * 60 * 60 * 1000;

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
