/**
 * What stood in a bed the year before the season shown (REQ-053 GP-FR-077, #2764): read from the bed's rotation
 * timeline (`GET /locations/{key}/rotation`), the one source the history timeline and the site rotation matrix read
 * too - plants of every slot and the years filled in afterwards. Nothing is derived here a second time: the head
 * picks the year out of the server's answer.
 *
 * The bed view offers the seasons from six years back on, so the timeline is asked for its longest look-back; the
 * previous year of every offered season lies inside it.
 */
import { useMemo } from 'react';
import type { RotationYear } from './historyTypes';
import { useRotationTimeline } from './useRotationTimeline';

/** The longest look-back the server offers (`MAX_ROTATION_TIMELINE_YEARS` in `app/config/constants.py`). */
export const PREVIOUS_YEAR_LOOKBACK = 10;

export type PreviousYearState =
  | { status: 'loading' }
  | { status: 'error' }
  /** `entry` is `null` while the year lies outside the timeline the server returned. */
  | { status: 'ready'; entry: RotationYear | null };

/**
 * @param bedKey  the bed
 * @param year    the year before the season shown
 * @param version changes whenever the bed's history may have changed (a planting, a filled-in year)
 */
export function usePreviousYear(bedKey: string, year: number, version: number): PreviousYearState {
  const { state } = useRotationTimeline(bedKey, PREVIOUS_YEAR_LOOKBACK, version);
  return useMemo<PreviousYearState>(() => {
    if (state.status === 'loading') return { status: 'loading' };
    if (state.status === 'error') return { status: 'error' };
    return { status: 'ready', entry: state.timeline.timeline.find((entry) => entry.year === year) ?? null };
  }, [state, year]);
}
