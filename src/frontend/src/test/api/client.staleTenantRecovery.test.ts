import { describe, it, expect, afterEach, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import client, {
  ACTIVE_TENANT_DENIED_MESSAGE,
  getActiveTenantSlug,
  setActiveTenantRejectedHandler,
  setActiveTenantSlug,
} from '@/api/client';
import { ApiError } from '@/api/errors';
import { server } from '../mocks/server';

/**
 * #1091 A-4 AC 4 — stale-slug recovery, and the refusal it must keep its hands off.
 *
 * A revoked membership leaves `kp_active_tenant_slug` naming a tenant the
 * backend will not honour; from then on *every* global catalogue operation (~19
 * of them) answers 403 and the user cannot get out of it by navigating. An
 * under-privileged role produces the very same 403 `FORBIDDEN` — but there the
 * active tenant is correct and clearing it would drop the user out of their
 * organisation for pressing a button they may not press. Both cases are pinned
 * here, because a recovery that cannot tell them apart is worse than none.
 */
describe('stale active-tenant recovery', () => {
  /** The invalid-tenant refusal, verbatim from `_ACTIVE_TENANT_DENIED`. */
  const deniedTenantEnvelope = {
    error_id: 'err_tenant_denied',
    error_code: 'FORBIDDEN',
    message: ACTIVE_TENANT_DENIED_MESSAGE,
    details: [],
    timestamp: '2026-08-10T00:00:00Z',
    path: '/api/v1/species',
    method: 'GET',
  };

  /** The role refusal of the SEC-005 (#1113) create gate — same status, same code. */
  const deniedRoleEnvelope = {
    ...deniedTenantEnvelope,
    error_id: 'err_role_denied',
    message: 'Your role may not create species in this tenant.',
    method: 'POST',
  };

  const onRejected = vi.fn();

  beforeEach(() => {
    onRejected.mockReset();
    setActiveTenantRejectedHandler(onRejected);
    setActiveTenantSlug('garten-b');
  });

  afterEach(() => {
    setActiveTenantRejectedHandler(null);
    setActiveTenantSlug('test-tenant');
  });

  it('clears the active tenant and asks for a tenant reload on an invalid-tenant 403', async () => {
    server.use(
      http.get('/api/v1/species', () => HttpResponse.json(deniedTenantEnvelope, { status: 403 })),
    );

    await expect(client.get('/species')).rejects.toBeInstanceOf(ApiError);

    expect(getActiveTenantSlug()).toBeNull();
    expect(onRejected).toHaveBeenCalledTimes(1);
  });

  it('leaves the active tenant untouched on a role 403 — same status, same error_code', async () => {
    server.use(
      http.post('/api/v1/species', () => HttpResponse.json(deniedRoleEnvelope, { status: 403 })),
    );

    await expect(client.post('/species', { scientific_name: 'x' })).rejects.toBeInstanceOf(
      ApiError,
    );

    // A viewer being refused a create must not be thrown out of their org.
    expect(getActiveTenantSlug()).toBe('garten-b');
    expect(onRejected).not.toHaveBeenCalled();
  });

  it('ignores an invalid-tenant 403 on a request that carried no header', async () => {
    // Nothing claimed a tenant, so nothing about a tenant can be stale — this is
    // the arm that keeps recovery from firing on unrelated refusals.
    setActiveTenantSlug(null);
    server.use(
      http.get('/api/v1/species', () => HttpResponse.json(deniedTenantEnvelope, { status: 403 })),
    );

    await expect(client.get('/species')).rejects.toBeInstanceOf(ApiError);

    expect(onRejected).not.toHaveBeenCalled();
  });

  it('ignores other refusals that carried the header (platform-admin 403)', async () => {
    server.use(
      http.get('/api/v1/admin/probe', () =>
        HttpResponse.json(
          { ...deniedTenantEnvelope, message: 'Platform admin role required.' },
          { status: 403 },
        ),
      ),
    );

    await expect(client.get('/admin/probe')).rejects.toBeInstanceOf(ApiError);

    expect(getActiveTenantSlug()).toBe('garten-b');
    expect(onRejected).not.toHaveBeenCalled();
  });

  it('ignores a 404 carrying the same message', async () => {
    server.use(
      http.get('/api/v1/species', () =>
        HttpResponse.json({ ...deniedTenantEnvelope, error_code: 'NOT_FOUND' }, { status: 404 }),
      ),
    );

    await expect(client.get('/species')).rejects.toBeInstanceOf(ApiError);
    expect(onRejected).not.toHaveBeenCalled();
  });

  it('reloads once when a whole page worth of catalogue requests fails at the same time', async () => {
    // A stale slug refuses every catalogue operation simultaneously; without the
    // in-flight guard each one would trigger its own tenant-list reload.
    server.use(
      http.get('/api/v1/species', () => HttpResponse.json(deniedTenantEnvelope, { status: 403 })),
      http.get('/api/v1/botanical-families', () =>
        HttpResponse.json(deniedTenantEnvelope, { status: 403 }),
      ),
      http.get('/api/v1/cultivars', () =>
        HttpResponse.json(deniedTenantEnvelope, { status: 403 }),
      ),
    );
    let release: () => void = () => undefined;
    onRejected.mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          release = resolve;
        }),
    );

    const results = await Promise.allSettled([
      client.get('/species'),
      client.get('/botanical-families'),
      client.get('/cultivars'),
    ]);

    expect(results.every((r) => r.status === 'rejected')).toBe(true);
    expect(onRejected).toHaveBeenCalledTimes(1);
    // Let the guard clear again so it cannot leak into the next test.
    release();
    await new Promise((resolve) => setTimeout(resolve, 0));
  });

  it('survives a recovery handler that throws', async () => {
    onRejected.mockImplementation(() => {
      throw new Error('reload failed');
    });
    server.use(
      http.get('/api/v1/species', () => HttpResponse.json(deniedTenantEnvelope, { status: 403 })),
    );

    // The caller still sees the original ApiError, not the handler's failure.
    await expect(client.get('/species')).rejects.toMatchObject({
      errorCode: 'FORBIDDEN',
      statusCode: 403,
    });
  });

  it('does not fall over when no handler is registered', async () => {
    setActiveTenantRejectedHandler(null);
    server.use(
      http.get('/api/v1/species', () => HttpResponse.json(deniedTenantEnvelope, { status: 403 })),
    );

    await expect(client.get('/species')).rejects.toBeInstanceOf(ApiError);
    // The in-memory slug is dropped regardless, so the next request is answered
    // in personal scope instead of failing again.
    expect(getActiveTenantSlug()).toBeNull();
  });
});
