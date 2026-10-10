import { useMemo, useSyncExternalStore } from 'react';
import {
  readConsent,
  subscribeConsent,
  writeConsent,
  type ConsentState,
} from '@/observability/consent';

export interface UseConsentResult {
  /** The current decision; re-renders on a change in this tab or another one. */
  consent: ConsentState;
  /** Persist a new decision; every subscriber (incl. error tracking) reacts. */
  setConsent: (state: ConsentState) => void;
}

/**
 * UI-NFR-013 CI-004 — consent-aware rendering.
 *
 * A thin binding over the React-free store in `@/observability/consent`, so a
 * component and the error-tracking gate always read the same decision.
 */
export function useConsent(): UseConsentResult {
  const consent = useSyncExternalStore(subscribeConsent, readConsent, readConsent);
  return useMemo(() => ({ consent, setConsent: writeConsent }), [consent]);
}
