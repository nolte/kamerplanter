import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  client: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

vi.mock('@/api/client', () => ({ __esModule: true, default: mocks.client, tenantClient: mocks.client }));

import * as plans from '@/api/endpoints/adminPlans';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('adminPlans endpoints (REQ-056 §7.6, #2142)', () => {
  it('lists the catalogue on the global platform-admin path', async () => {
    client.get.mockResolvedValue({ data: [] });
    await plans.listPlans();
    expect(client.get).toHaveBeenCalledWith('/admin/platform/plans');
  });

  it('creates a plan with the payload as given', async () => {
    const payload = { key: 'community', name: 'Community', limits: { members: 30, storage_mb: 0 } };
    client.post.mockResolvedValue({ data: payload });
    await plans.createPlan(payload);
    expect(client.post).toHaveBeenCalledWith('/admin/platform/plans', payload);
  });

  it('patches and deletes by the encoded key', async () => {
    client.patch.mockResolvedValue({ data: {} });
    client.delete.mockResolvedValue({ data: undefined });
    await plans.updatePlan('a b', { is_default: true });
    expect(client.patch).toHaveBeenCalledWith('/admin/platform/plans/a%20b', { is_default: true });
    await plans.deletePlan('a b');
    expect(client.delete).toHaveBeenCalledWith('/admin/platform/plans/a%20b');
  });
});
