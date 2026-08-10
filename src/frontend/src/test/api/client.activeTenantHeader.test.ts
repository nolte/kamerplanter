import { describe, it, expect, afterEach, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import client, {
  ACTIVE_TENANT_HEADER,
  setActiveTenantSlug,
  tenantClient,
} from '@/api/client';
import { server } from '../mocks/server';

/**
 * #1091 A-4 — the global client tells the backend which tenant the caller is
 * acting in (ADR-009, REQ-049 §2.11).
 *
 * The global catalogues (`/species`, `/botanical-families`, cultivars,
 * companion planting) carry no `/t/{slug}/` segment, so `X-Active-Tenant` is the
 * only signal the backend has; without it a member of an organisation silently
 * reads and writes in their personal garden.
 */
describe('global client: X-Active-Tenant', () => {
  /** Captured header value of the last `/api/v1/header-probe` request. */
  let seen: string | null = null;

  beforeEach(() => {
    seen = null;
    server.use(
      http.get('/api/v1/header-probe', ({ request }) => {
        seen = request.headers.get(ACTIVE_TENANT_HEADER);
        return HttpResponse.json({ ok: true });
      }),
      http.post('/api/v1/header-probe', ({ request }) => {
        seen = request.headers.get(ACTIVE_TENANT_HEADER);
        return HttpResponse.json({ ok: true });
      }),
      http.get('/api/v1/t/test-tenant/header-probe', ({ request }) => {
        seen = request.headers.get(ACTIVE_TENANT_HEADER);
        return HttpResponse.json({ ok: true });
      }),
    );
  });

  afterEach(() => {
    // setup.ts re-arms the slug before every test, but a test that clears it
    // must not leak that into the next file-local test.
    setActiveTenantSlug('test-tenant');
  });

  it('mirrors the backend header name exactly', () => {
    // The backend declares `ACTIVE_TENANT_HEADER = "X-Active-Tenant"` in
    // app/common/auth.py; a typo here is a silently header-less client.
    expect(ACTIVE_TENANT_HEADER).toBe('X-Active-Tenant');
  });

  it('sends the active slug on a GET', async () => {
    setActiveTenantSlug('garten-b');
    await client.get('/header-probe');
    expect(seen).toBe('garten-b');
  });

  it('sends the active slug on a write, so the row is stamped with the acting tenant', async () => {
    setActiveTenantSlug('garten-b');
    await client.post('/header-probe', { name: 'x' });
    expect(seen).toBe('garten-b');
  });

  it('sends no header at all when no tenant is active', async () => {
    setActiveTenantSlug(null);
    await client.get('/header-probe');
    // Not an empty string: the backend reads absent and blank alike as "no org
    // context", but an empty header is noise that says nothing.
    expect(seen).toBeNull();
  });

  it(
    'does not wait for the bootstrap before firing a header-less request',
    async () => {
      // AC 2 — the global client must NOT use `waitForTenantSlug()`. A blocking
      // implementation would poll for up to 10s here (and on `/auth/login`,
      // `/auth/refresh`, … which have nothing to do with tenants), so this test
      // fails by timeout rather than by assertion if the wait is ever added.
      setActiveTenantSlug(null);
      const started = Date.now();
      const response = await client.get('/header-probe');
      expect(response.data).toEqual({ ok: true });
      expect(Date.now() - started).toBeLessThan(2000);
      expect(seen).toBeNull();
    },
    3000,
  );

  it('leaves tenantClient alone — its routes bind the tenant from the path', async () => {
    setActiveTenantSlug('test-tenant');
    await tenantClient.get('/header-probe');
    expect(seen).toBeNull();
  });
});
