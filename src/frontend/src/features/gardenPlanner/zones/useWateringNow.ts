import { useMemo } from 'react';
import { stateInstant, usePlantStateClock } from '../planting/plantStateClock';

const NO_FOREGROUND = (): void => undefined;

/**
 * The instant "days since the last watering" counts from. The count works on whole UTC calendar days (as the
 * backend does), so the instant only has to move with the day: the plant-state clock checks every minute and
 * rolls over at midnight UTC, and the day classes follow without a reload of the page.
 */
export function useWateringNow(): number {
  const day = usePlantStateClock(true, NO_FOREGROUND);
  return useMemo(() => Date.parse(stateInstant(day)), [day]);
}
