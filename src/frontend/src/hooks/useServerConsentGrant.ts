import { useCallback, useMemo, useRef } from 'react';
import { grantConsent, listConsents } from '@/api/endpoints/privacy';

export interface UseServerConsentGrantResult {
  /**
   * Make sure the purpose is granted on the server: read the consent list once
   * (cached until {@link reset}) and grant only when it is not granted yet.
   * Rejects when the grant fails — the caller must not go on as if it had worked.
   */
  ensureGranted: () => Promise<void>;
  /** Forget the cached state, e.g. when a dialog reopens. */
  reset: () => void;
}

/**
 * REQ-025 — grant a server-side consent purpose on demand, where a switch in the
 * UI *is* the consent (e.g. `reference_contribution`, #2174).
 *
 * Full mode only: the Light mode has no `/privacy/consents` (it answers 404), so
 * a caller must not reach this there.
 *
 * A failed read of the list counts as "not granted": the grant that follows is
 * the authoritative answer, and granting an already granted purpose is harmless.
 */
export function useServerConsentGrant(purpose: string): UseServerConsentGrantResult {
  const known = useRef<Promise<boolean> | null>(null);

  const reset = useCallback(() => {
    known.current = null;
  }, []);

  const ensureGranted = useCallback(async () => {
    if (!known.current) {
      known.current = listConsents()
        .then((records) => records.some((r) => r.purpose === purpose && r.granted))
        .catch(() => false);
    }
    if (await known.current) return;
    await grantConsent(purpose);
    known.current = Promise.resolve(true);
  }, [purpose]);

  return useMemo(() => ({ ensureGranted, reset }), [ensureGranted, reset]);
}
