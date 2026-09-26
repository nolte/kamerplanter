import { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import type { StepUpAction } from '@/api/types';
import {
  clearStepUpResume,
  consumePendingStepUpToken,
  peekPendingStepUpToken,
  peekStepUpReauthError,
  readStepUpResume,
  returnPathname,
  takeStepUpReauthError,
} from '@/utils/stepUpReauth';

export interface PendingStepUpReauth {
  /** A token of a fresh sign-in for the act is waiting to be sent. */
  hasToken: boolean;
  /** The callback's error code (`step_up_failed` / `step_up_stale` / `step_up_cancelled`), if any. */
  callbackError: string | null;
  /** The token to send, left in storage; `null` when none or expired. */
  peekToken: () => string | null;
  /**
   * Take the token out of storage — single use. Call after the act succeeded or
   * the step-up itself was refused (401/429), not on any other refusal.
   */
  consumeToken: () => string | null;
  /** Forget the callback error once it was acted on. */
  dismissError: () => void;
}

/**
 * What the fresh sign-in (#1815) left behind for one act: a pending token or a
 * callback error. Read from sessionStorage on render while `active` (e.g. while
 * the dialog is open); the mutators re-render.
 */
export function usePendingStepUpReauth(action: StepUpAction, active = true): PendingStepUpReauth {
  // Bumped after every storage mutation so the next render reads the new state.
  const [version, setVersion] = useState(0);
  const bump = useCallback(() => setVersion((v) => v + 1), []);

  return useMemo(() => {
    const token = active && version >= 0 ? peekPendingStepUpToken(action) : null;
    const callbackError = active ? peekStepUpReauthError(action) : null;
    return {
      hasToken: token !== null,
      callbackError,
      peekToken: () => peekPendingStepUpToken(action),
      consumeToken: () => {
        const consumed = consumePendingStepUpToken(action);
        bump();
        return consumed;
      },
      dismissError: () => {
        takeStepUpReauthError(action);
        bump();
      },
    };
  }, [action, active, version, bump]);
}

/**
 * Whether this page should reopen the step-up `surface` after the browser came
 * back from the identity provider (#1815).
 *
 * `true` on the first render when the saved resume context names this surface,
 * its return path is the current page, and the callback left a pending token or
 * an error for its act. The context is removed once read, so the dialog reopens
 * once. A page initialises its "dialog open" state from this value.
 */
export function useStepUpResume(surface: string): boolean {
  const location = useLocation();
  const [resume] = useState(() => {
    const record = readStepUpResume();
    if (!record || record.surface !== surface) return false;
    if (returnPathname(record.returnPath) !== location.pathname) return false;
    return peekPendingStepUpToken(record.action) !== null || peekStepUpReauthError(record.action) !== null;
  });

  useEffect(() => {
    if (resume) clearStepUpResume();
  }, [resume]);

  return resume;
}
