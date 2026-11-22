import { useEffect, useRef, useState } from 'react';
import { utcDay } from '../model/plantState';

/** The calendar day rolls over at midnight UTC; a minute is fine-grained enough and cheap. */
const TICK_MS = 60_000;

/** The state only changes with the day (GP-FR-192 works on UTC calendar days), so only a new day recomputes it. */
export const today = (): string => utcDay(new Date().toISOString());

/** The instant a plant state is computed for on `day`: noon UTC keeps it inside that calendar day everywhere. */
export const stateInstant = (day: string): string => `${day}T12:00:00Z`;

/**
 * The clock of the plant states (GP-FR-191/192), shared by the bed view and the plan layer: the current UTC day,
 * checked every minute while `enabled`, and `onForeground` whenever the page comes back to the foreground, so the
 * caller reloads its answers. The callback is read through a ref - a new function per render does not re-subscribe.
 */
export function usePlantStateClock(enabled: boolean, onForeground: () => void): string {
  const [day, setDay] = useState(today);
  const foreground = useRef(onForeground);
  useEffect(() => {
    foreground.current = onForeground;
  }, [onForeground]);
  useEffect(() => {
    if (!enabled) return undefined;
    const timer = window.setInterval(() => setDay(today()), TICK_MS);
    const onVisible = () => {
      if (document.visibilityState === 'visible') foreground.current();
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [enabled]);
  return day;
}
