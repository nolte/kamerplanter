import { configureStore } from '@reduxjs/toolkit';
import { setActiveTenantRejectedHandler } from '../api/client';
import { clearActiveTenant, loadMyTenants } from './slices/tenantSlice';
import { rootReducer } from './rootReducer';
import { sessionListener } from './sessionListener';

export const store = configureStore({
  // The slice map lives in `rootReducer.ts`, wrapped in the session-end reset (#2117).
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) => getDefaultMiddleware().prepend(sessionListener.middleware),
});

/**
 * Stale-slug recovery, wired where the store exists (#1091 A-4).
 *
 * The API client detects that the backend refuses the persisted active tenant
 * (a membership was revoked, the organisation was deleted) but cannot repair it
 * on its own: it owns no state beyond the in-memory slug, and it must not import
 * the store — every slice imports the client, so the reverse edge would be a
 * cycle. This is the composition root, the one place that legitimately knows
 * both, so the behaviour is registered here.
 *
 * Clearing first and reloading second matters: `loadMyTenants.fulfilled` re-picks
 * an existing tenant and re-persists `kp_active_tenant_slug`, so the user lands
 * on a working scope instead of a permanently 403-ing catalogue. The returned
 * dispatch promise is what the client uses to collapse a page-load's worth of
 * simultaneous 403s into a single reload.
 *
 * Not a cache invalidation: switching tenants deliberately goes through
 * `TenantSwitcher`, which does a full `window.location.reload()`.
 */
setActiveTenantRejectedHandler(() => {
  store.dispatch(clearActiveTenant());
  return store.dispatch(loadMyTenants());
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
