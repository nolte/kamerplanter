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

import * as activityPlans from '@/api/endpoints/activityPlans';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('activityPlans endpoints', () => {
  it('generatePlan posts request and returns data', async () => {
    client.post.mockResolvedValue({ data: { tasks: [] } });
    const req = { plant_key: 'p1' } as never;
    await expect(activityPlans.generatePlan(req)).resolves.toEqual({ tasks: [] });
    expect(client.post).toHaveBeenCalledWith('/activity-plans/generate', req);
  });

  it('applyPlan posts request and returns data', async () => {
    client.post.mockResolvedValue({ data: { created: 2 } });
    const req = { plan_key: 'pl1' } as never;
    await expect(activityPlans.applyPlan(req)).resolves.toEqual({ created: 2 });
    expect(client.post).toHaveBeenCalledWith('/activity-plans/apply', req);
  });

  it('updateTaskTemplate patches template by key', async () => {
    client.patch.mockResolvedValue({ data: { key: 't1' } });
    const req = { name: 'X' } as never;
    await expect(activityPlans.updateTaskTemplate('t1', req)).resolves.toEqual({ key: 't1' });
    expect(client.patch).toHaveBeenCalledWith('/activity-plans/templates/t1', req);
  });

  it('deleteTaskTemplate deletes template by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await activityPlans.deleteTaskTemplate('t1');
    expect(client.delete).toHaveBeenCalledWith('/activity-plans/templates/t1');
  });
});
