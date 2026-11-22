/**
 * The guard behind "Complete" (REQ-053 GP-FR-149, field mode): a second tap within 300 ms of the
 * first, or while the first is still waiting for its answer, is the same tap. The button also shows
 * its loading state, but a state update lands after the second event of a fast double tap - this check
 * runs on the refs that are already current.
 */

export const SUBMIT_DEBOUNCE_MS = 300;

export function isDuplicateTap(lastTapAt: number, now: number, busy: boolean): boolean {
  return busy || now - lastTapAt < SUBMIT_DEBOUNCE_MS;
}
