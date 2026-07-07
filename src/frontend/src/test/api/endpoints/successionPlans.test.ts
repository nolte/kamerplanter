import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const client = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  };
  return { client };
});

vi.mock('@/api/client', () => ({
  __esModule: true,
  default: mocks.client,
  tenantClient: mocks.client,
}));

import * as api from '@/api/endpoints/successionPlans';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('successionPlans endpoints', () => {
  it('listSuccessionPlans defaults to offset 0 / limit 50', async () => {
    client.get.mockResolvedValue({ data: [] });
    await api.listSuccessionPlans();
    expect(client.get).toHaveBeenCalledWith('/succession-plans', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('listSuccessionPlans forwards pagination', async () => {
    client.get.mockResolvedValue({ data: [] });
    await api.listSuccessionPlans(10, 5);
    expect(client.get).toHaveBeenCalledWith('/succession-plans', {
      params: { offset: 10, limit: 5 },
    });
  });

  it('getSuccessionPlan GETs by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'sp1' } });
    await api.getSuccessionPlan('sp1');
    expect(client.get).toHaveBeenCalledWith('/succession-plans/sp1');
  });

  it('createSuccessionPlan POSTs the payload', async () => {
    const payload = { name: 'Radish waves' } as never;
    client.post.mockResolvedValue({ data: { key: 'sp1' } });
    await api.createSuccessionPlan(payload);
    expect(client.post).toHaveBeenCalledWith('/succession-plans', payload);
  });

  it('updateSuccessionPlan PUTs by key', async () => {
    const payload = { interval_days: 14 } as never;
    client.put.mockResolvedValue({ data: { key: 'sp1' } });
    await api.updateSuccessionPlan('sp1', payload);
    expect(client.put).toHaveBeenCalledWith('/succession-plans/sp1', payload);
  });

  it('deleteSuccessionPlan DELETEs by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await api.deleteSuccessionPlan('sp1');
    expect(client.delete).toHaveBeenCalledWith('/succession-plans/sp1');
  });

  it('generateRuns POSTs to the generate path', async () => {
    client.post.mockResolvedValue({ data: { generated: 3 } });
    await api.generateRuns('sp1');
    expect(client.post).toHaveBeenCalledWith('/succession-plans/sp1/generate');
  });

  it('generateNextRun POSTs to the generate-next path', async () => {
    client.post.mockResolvedValue({ data: { generated: 1 } });
    await api.generateNextRun('sp1');
    expect(client.post).toHaveBeenCalledWith('/succession-plans/sp1/generate-next');
  });
});
