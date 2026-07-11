import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

/** UI-NFR-019 §2.6 — kiosk auto-timeout defaults (R-033, R-035). */
export const KIOSK_IDLE_MS = 120_000;
export const KIOSK_WARNING_MS = 30_000;

interface UseKioskTimeoutOptions {
  /** Only arm the timer while the kiosk shell is mounted/active. */
  enabled: boolean;
  /** Inactivity before the warning overlay appears (R-033, default 120s). */
  idleMs?: number;
  /** Grace period the overlay counts down before auto-reset (R-035, default 30s). */
  warningMs?: number;
  /** Invoked on auto-reset — returns the kiosk to its start page (R-035). */
  onReset: () => void;
}

export interface KioskTimeoutState {
  /** Whether the timeout warning overlay is visible. */
  showWarning: boolean;
  /** Whole seconds left before auto-reset while the warning shows. */
  remainingSeconds: number;
  /** "Weiter arbeiten" — dismiss the warning and restart the idle timer (R-034). */
  dismissWarning: () => void;
}

/** Activity events that reset the inactivity timer (R-036). */
const ACTIVITY_EVENTS: Array<keyof WindowEventMap> = [
  'pointerdown',
  'touchstart',
  'mousedown',
  'keydown',
];

/**
 * UI-NFR-019 §2.6 — inactivity timer for the kiosk shell. After ``idleMs`` of no
 * interaction a warning overlay appears with a ``warningMs`` countdown; if the
 * user does not respond, ``onReset`` returns them to the start page. Any touch
 * interaction (or "Weiter arbeiten") resets the timer (R-034, R-036).
 */
export function useKioskTimeout({
  enabled,
  idleMs = KIOSK_IDLE_MS,
  warningMs = KIOSK_WARNING_MS,
  onReset,
}: UseKioskTimeoutOptions): KioskTimeoutState {
  const [showWarning, setShowWarning] = useState(false);
  const [remainingSeconds, setRemainingSeconds] = useState(Math.ceil(warningMs / 1000));

  const idleTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const countdownTimer = useRef<ReturnType<typeof setInterval>>(undefined);
  // Latest onReset without re-arming listeners on every parent render.
  const onResetRef = useRef(onReset);
  useEffect(() => {
    onResetRef.current = onReset;
  }, [onReset]);

  const clearTimers = useCallback(() => {
    if (idleTimer.current) clearTimeout(idleTimer.current);
    if (countdownTimer.current) clearInterval(countdownTimer.current);
  }, []);

  const startIdleTimer = useCallback(() => {
    if (idleTimer.current) clearTimeout(idleTimer.current);
    idleTimer.current = setTimeout(() => {
      // Seed the countdown here so the countdown effect never has to call
      // setState synchronously in its body.
      setRemainingSeconds(Math.ceil(warningMs / 1000));
      setShowWarning(true);
    }, idleMs);
  }, [idleMs, warningMs]);

  const dismissWarning = useCallback(() => {
    setShowWarning(false);
    startIdleTimer();
  }, [startIdleTimer]);

  // Drive the countdown while the warning is visible; auto-reset at zero.
  useEffect(() => {
    if (!enabled || !showWarning) return;
    countdownTimer.current = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          if (countdownTimer.current) clearInterval(countdownTimer.current);
          setShowWarning(false);
          onResetRef.current();
          return Math.ceil(warningMs / 1000);
        }
        return prev - 1;
      });
    }, 1000);
    return () => {
      if (countdownTimer.current) clearInterval(countdownTimer.current);
    };
  }, [enabled, showWarning, warningMs]);

  // Arm the idle timer and activity listeners while enabled.
  useEffect(() => {
    if (!enabled) {
      clearTimers();
      setShowWarning(false);
      return;
    }
    const handleActivity = () => {
      // Interaction only resets the idle countdown, never the warning overlay —
      // the overlay is dismissed explicitly via its button (R-034).
      if (!showWarning) startIdleTimer();
    };
    ACTIVITY_EVENTS.forEach((evt) =>
      window.addEventListener(evt, handleActivity, { passive: true }),
    );
    // While the warning overlay is up the idle timer must stay stopped, otherwise
    // it would re-trigger and reseed the countdown, preventing the auto-reset.
    if (showWarning) {
      if (idleTimer.current) clearTimeout(idleTimer.current);
    } else {
      startIdleTimer();
    }
    return () => {
      ACTIVITY_EVENTS.forEach((evt) => window.removeEventListener(evt, handleActivity));
      if (idleTimer.current) clearTimeout(idleTimer.current);
    };
  }, [enabled, showWarning, startIdleTimer, clearTimers]);

  return useMemo(
    () => ({ showWarning, remainingSeconds, dismissWarning }),
    [showWarning, remainingSeconds, dismissWarning],
  );
}
