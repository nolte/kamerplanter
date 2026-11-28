import { useMemo, useSyncExternalStore } from 'react';
import {
  readConsentSnapshot,
  subscribeConsent,
  type ConsentSnapshot,
} from '@/observability/consent';

export interface UseConsentResult {
  /** Device decision, sign-in state, account consent; re-renders on a change in this tab or another one. */
  snapshot: ConsentSnapshot;
}

/**
 * UI-NFR-013 CI-004 — consent-aware rendering.
 *
 * A thin binding over the React-free store in `@/observability/consent`, so a
 * component and the error-tracking gate always read the same snapshot and decide
 * with the same functions (`browserReportsPermitted`, `consentPrompt`).
 */
export function useConsent(): UseConsentResult {
  const snapshot = useSyncExternalStore(subscribeConsent, readConsentSnapshot, readConsentSnapshot);
  return useMemo(() => ({ snapshot }), [snapshot]);
}
