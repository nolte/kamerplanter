import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  client: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

vi.mock('@/api/client', () => ({ __esModule: true, default: mocks.client, tenantClient: mocks.client }));

import * as oidc from '@/api/endpoints/adminOidcProviders';

const client = mocks.client;

beforeEach(() => vi.clearAllMocks());

describe('adminOidcProviders endpoints (#1906)', () => {
  it('lists on the global admin path', async () => {
    client.get.mockResolvedValue({ data: [] });
    await oidc.listOidcProviders();
    expect(client.get).toHaveBeenCalledWith('/admin/oidc-providers');
  });

  it('creates with the step-up in the body', async () => {
    client.post.mockResolvedValue({ data: { key: 'k' } });
    const payload = { slug: 'kc', current_password: 'x' } as never;
    await oidc.createOidcProvider(payload);
    expect(client.post).toHaveBeenCalledWith('/admin/oidc-providers', payload);
  });

  it('updates with PUT on the encoded key', async () => {
    client.put.mockResolvedValue({ data: { key: 'k 1' } });
    const payload = { display_name: 'X' } as never;
    await oidc.updateOidcProvider('k 1', payload);
    expect(client.put).toHaveBeenCalledWith('/admin/oidc-providers/k%201', payload);
  });

  it('deletes with the step-up as the request body, not as a query', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await oidc.deleteOidcProvider('k1', { step_up_code: '04829175' });
    expect(client.delete).toHaveBeenCalledWith('/admin/oidc-providers/k1', {
      data: { step_up_code: '04829175' },
    });
  });

  it('tests with POST and no body', async () => {
    client.post.mockResolvedValue({ data: { message: 'ok' } });
    await oidc.testOidcProvider('k/1');
    expect(client.post).toHaveBeenCalledWith('/admin/oidc-providers/k%2F1/test');
  });
});
