import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import client, { ACTIVE_TENANT_DENIED_MESSAGE, setActiveTenantSlug } from '@/api/client';
import { store } from '@/store/store';
import { loadMyTenants } from '@/store/slices/tenantSlice';
import { server } from '../mocks/server';

/**
 * #1091 A-4 AC 4 — the *wiring*, not just the detection.
 *
 * `client.staleTenantRecovery.test.ts` pins when recovery fires with an injected
 * handler; this file pins that the real application registers a handler at all
 * and that it repairs the state a user can see. Without it the whole mechanism
 * could sit in the client, fully tested, and be inert because nobody ever called
 * `setActiveTenantRejectedHandler` — the "implemented but never wired" class the
 * permission gate already cost this project once.
 */
describe('active-tenant recovery wiring (store composition root)', () => {
  const staleTenant = {
    key: 'org-1',
    slug: 'garten-b',
    name: 'Garten B',
    tenant_type: 'organization',
    role: 'grower',
  };
  const remainingTenant = {
    key: 'personal-1',
    slug: 'mein-garten',
    name: 'Mein Garten',
    tenant_type: 'personal',
    role: 'lead',
  };

  let tenantListRequests = 0;

  beforeEach(() => {
    tenantListRequests = 0;
    server.use(
      // The membership in `garten-b` has been revoked, so the reload no longer
      // offers it — the user must land somewhere that still resolves.
      http.get('/api/v1/tenants', () => {
        tenantListRequests += 1;
        return HttpResponse.json([remainingTenant]);
      }),
      http.get('/api/v1/species', () =>
        HttpResponse.json(
          {
            error_id: 'err_tenant_denied',
            error_code: 'FORBIDDEN',
            message: ACTIVE_TENANT_DENIED_MESSAGE,
            details: [],
            timestamp: '2026-08-10T00:00:00Z',
            path: '/api/v1/species',
            method: 'GET',
          },
          { status: 403 },
        ),
      ),
    );
  });

  afterEach(() => {
    setActiveTenantSlug('test-tenant');
  });

  it('drops the revoked tenant and reloads the list onto one that still exists', async () => {
    store.dispatch({ type: loadMyTenants.fulfilled.type, payload: [staleTenant, remainingTenant] });
    expect(store.getState().tenants.activeTenant?.slug).toBe('garten-b');

    await expect(client.get('/species')).rejects.toBeTruthy();

    // The reload is asynchronous; wait for it to settle.
    await expect
      .poll(() => store.getState().tenants.activeTenant?.slug, { timeout: 3000 })
      .toBe('mein-garten');
    expect(tenantListRequests).toBe(1);
    expect(store.getState().tenants.myTenants).toEqual([remainingTenant]);
    // The persisted-slug side of the same repair is asserted in
    // `tenantSlice.test.ts`, where `localStorage` is stubbed deterministically
    // (the runner's own global is not usable here).
  });
});
