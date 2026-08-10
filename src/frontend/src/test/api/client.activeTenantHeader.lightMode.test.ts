import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

// Must be mocked before `@/api/client` and the slice are evaluated — both read
// `isLightMode` at module scope.
vi.mock('@/config/mode', () => ({
  KAMERPLANTER_MODE: 'light',
  isLightMode: true,
  isFullMode: false,
}));

// The setup file already pulled `@/api/client` in under the real mode module, so
// the cached graph is dropped before re-importing it against the mock.
vi.resetModules();

const { default: client, ACTIVE_TENANT_HEADER, setActiveTenantSlug, getActiveTenantSlug } =
  await import('@/api/client');
const { default: tenantReducer, loadMyTenants } = await import('@/store/slices/tenantSlice');

/**
 * #1091 A-4 AC 3 — what light mode (REQ-027) actually does.
 *
 * The operator decided the light-mode client should send `mein-garten` rather
 * than nothing, and the backend proves it accepts that slug (A-2 AC 9). The
 * question this file answers is whether that happens *without* a light-mode
 * branch in the interceptor: it does, because the light-mode seed gives the sole
 * operator a `lead` membership in the `mein-garten` tenant, so `loadMyTenants`
 * resolves the active slug there exactly as it would for any organisation. The
 * interceptor therefore stays uniform — a second, hard-coded light-mode slug
 * would be a source of truth competing with the store.
 */
describe('global client in light mode', () => {
  const lightTenant = {
    key: 'system-tenant',
    slug: 'mein-garten',
    name: 'Mein Garten',
    tenant_type: 'personal',
    role: 'lead',
  };

  let seen: string | null = null;

  beforeEach(() => {
    seen = null;
    setActiveTenantSlug(null);
    server.use(
      http.get('/api/v1/header-probe', ({ request }) => {
        seen = request.headers.get(ACTIVE_TENANT_HEADER);
        return HttpResponse.json({ ok: true });
      }),
    );
  });

  it('sends mein-garten once the tenant list has loaded', async () => {
    tenantReducer(undefined, { type: loadMyTenants.fulfilled.type, payload: [lightTenant] });
    expect(getActiveTenantSlug()).toBe('mein-garten');

    await client.get('/header-probe');
    expect(seen).toBe('mein-garten');
  });

  it('sends nothing before the tenant list has loaded — headerless is valid too', async () => {
    // The bootstrap window (AC 2) exists in light mode as well; the backend reads
    // a header-less request as "no org context", which resolves to the same
    // global catalogue the light-mode operator would see anyway.
    expect(getActiveTenantSlug()).toBeNull();
    await client.get('/header-probe');
    expect(seen).toBeNull();
  });
});
