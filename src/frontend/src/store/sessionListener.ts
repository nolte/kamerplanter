import { createListenerMiddleware } from '@reduxjs/toolkit';
import { setActiveTenantSlug } from '@/api/client';
import { releasePushSubscription } from '@/lib/pushSubscription';
import { clearOfflineData, postNamespace } from '@/pwa/offlineData';
import { isSessionEnd, type rootReducer } from './rootReducer';
import { DEAD_SESSION_REFRESH_CODE, RATE_LIMITED_REJECTION, refreshAccessToken } from './slices/authSlice';

/** Where `tenantSlice` persists the active tenant across reloads. */
const ACTIVE_TENANT_KEY = 'kp_active_tenant_slug';

type SessionState = ReturnType<typeof rootReducer>;

/**
 * The session-end side effects outside the store (#2117, MT-020).
 *
 * The reducer half (`rootReducer`) empties every slice; what lives elsewhere is
 * dropped here, on the same actions:
 *
 * - the persisted active tenant slug and the API client's in-memory copy — left
 *   in place, the next account's `loadMyTenants` would resume the previous
 *   account's tenant when it is a member there too, and every request in between
 *   carried the previous account's `X-Active-Tenant`;
 * - the browser's push subscription. The logout thunk has already removed the
 *   server copy (it still had a token); on a forced sign-out there is no token,
 *   so only the browser side ends here and the backend prunes its copy when the
 *   push service reports the endpoint gone. Idempotent: after a logout there is
 *   no subscription left to find;
 * - the service worker's API cache and every IndexedDB database (UI-NFR-012
 *   SR-019, REQ-053 WP 9.1, G-W9 b): the next person on a shared device must not
 *   read the previous account's plans offline. Pinned by
 *   `test/guards/offlineDataClearedOnSessionChange.test.ts`.
 */
export const sessionListener = createListenerMiddleware();

sessionListener.startListening({
  predicate: (action) => isSessionEnd(action),
  effect: async () => {
    setActiveTenantSlug(null);
    try {
      localStorage.removeItem(ACTIVE_TENANT_KEY);
    } catch {
      // Storage unavailable (private mode) — nothing persisted to remove.
    }
    await clearOfflineData();
    await releasePushSubscription({ notifyServer: false });
  },
});

/**
 * A refresh the server refused means the session is gone (#2789 review S3): the bootstrap in
 * `AuthProvider` swallows that rejection without `clearAuth`, e.g. after an account erasure or a
 * revocation elsewhere, so the previous session's offline data is cleared here. A rate limit is not a
 * dead session (#1131), a 5xx is an outage, and a refresh that got no answer at all (offline start)
 * must keep the cache — it is exactly what the offline start reads. The thunk's error serialiser marks
 * a 401/403 with {@link DEAD_SESSION_REFRESH_CODE}.
 */
export function isDeadSessionRefresh(action: unknown): boolean {
  if (!refreshAccessToken.rejected.match(action)) return false;
  if (action.payload === RATE_LIMITED_REJECTION) return false;
  // Only 401/403 (#2789 verification M1): a 5xx answers with the same ApiError envelope while the
  // refresh cookie stays valid — the outage is exactly when the offline data is needed.
  return action.error.code === DEAD_SESSION_REFRESH_CODE;
}

sessionListener.startListening({
  predicate: (action) => isDeadSessionRefresh(action),
  effect: async () => {
    await clearOfflineData();
  },
});

function namespaceOf(state: SessionState): string {
  return `${state.auth.user?.key ?? ''}\u0000${state.tenants.activeTenant?.key ?? ''}`;
}

/**
 * The service worker's cache namespace `kp:{user_key}:{tenant_key}` follows the signed-in user and
 * the active tenant (REQ-053 WP 9.1). The keys come from the store, never from a token; while
 * either is missing the worker caches no API answer. A changed namespace also makes the worker drop
 * every other namespace's cache.
 */
sessionListener.startListening({
  predicate: (_action, current, previous) =>
    namespaceOf(current as SessionState) !== namespaceOf(previous as SessionState),
  effect: async (_action, api) => {
    const state = api.getState() as SessionState;
    await postNamespace(state.auth.user?.key ?? null, state.tenants.activeTenant?.key ?? null);
  },
});
