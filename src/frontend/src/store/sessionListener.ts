import { createListenerMiddleware } from '@reduxjs/toolkit';
import { setActiveTenantSlug } from '@/api/client';
import { releasePushSubscription } from '@/lib/pushSubscription';
import { isSessionEnd } from './rootReducer';

/** Where `tenantSlice` persists the active tenant across reloads. */
const ACTIVE_TENANT_KEY = 'kp_active_tenant_slug';

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
 *   no subscription left to find.
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
    await releasePushSubscription({ notifyServer: false });
  },
});
