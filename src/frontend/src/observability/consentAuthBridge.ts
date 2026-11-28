/**
 * Reports the sign-in state to the consent store (UI-NFR-013 v1.3 CP-008).
 *
 * In the initial chunk on purpose: until this has reported, the consent store
 * treats the sign-in state as `unknown` and nothing is sent. If the report lived
 * in a lazy chunk, a failed chunk load would leave a signed-in person looking
 * signed out — and a device grant would count for them.
 *
 * The account reconciliation (`consentSync.ts`) is its own chunk, loaded on the
 * first sign-in of the page view when this deployment asks for the consent at
 * all. If it fails to load, the account consent stays `unknown`: no report, no
 * banner; the privacy settings load the module themselves and show the state.
 */

import { setAuthStatus, type AuthStatus } from '@/observability/consent';
import { isBrowserConsentManaged } from '@/observability/errorTracking';

/** The part of the Redux auth slice this bridge reads. */
export interface AuthSliceView {
  initialized: boolean;
  isAuthenticated: boolean;
  user: { key: string } | null;
}

interface StoreLike {
  getState: () => { auth: AuthSliceView };
  subscribe: (listener: () => void) => () => void;
}

/** The sign-in state of an auth slice: `unknown` until the bootstrap finished or while the profile loads. */
export function authStatusFrom(auth: AuthSliceView): AuthStatus {
  if (!auth.initialized) return { kind: 'unknown' };
  if (!auth.isAuthenticated) return { kind: 'signed_out' };
  return auth.user?.key ? { kind: 'signed_in', account: auth.user.key } : { kind: 'unknown' };
}

let syncLoad: Promise<void> | null = null;

function ensureAccountSync(): void {
  if (syncLoad || !isBrowserConsentManaged()) return;
  syncLoad = import('@/observability/consentSync')
    .then((sync) => sync.startAccountSync())
    .catch((error: unknown) => {
      // Safe direction: without the module the account consent stays unknown.
      // The next sign-in change tries again.
      syncLoad = null;
      console.warn('[consent] account reconciliation failed to load', error);
    });
}

/**
 * Report the store's sign-in state now and on every change.
 *
 * @returns the unsubscribe function.
 */
export function bindConsentToAuth(store: StoreLike): () => void {
  const apply = () => {
    const status = authStatusFrom(store.getState().auth);
    setAuthStatus(status);
    if (status.kind === 'signed_in') ensureAccountSync();
  };
  apply();
  return store.subscribe(apply);
}

/** Test seam: forget that the reconciliation module was loaded. */
export function resetConsentAuthBridgeForTests(): void {
  syncLoad = null;
}
