import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const makeClient = () => ({
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  });
  // Two distinct doubles on purpose: the template writes must go through the
  // tenant-scoped client (#992), and a single shared double could not tell the
  // two apart — it would agree with the module whichever one it imported.
  return { client: makeClient(), tenantClient: makeClient() };
});

vi.mock('@/api/client', () => ({
  __esModule: true,
  default: mocks.client,
  tenantClient: mocks.tenantClient,
}));

import * as activityPlans from '@/api/endpoints/activityPlans';

const client = mocks.client;
const tenantClient = mocks.tenantClient;

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

  it('updateTaskTemplate patches template by key through the tenant-scoped client', async () => {
    tenantClient.patch.mockResolvedValue({ data: { key: 't1' } });
    const req = { name: 'X' } as never;
    await expect(activityPlans.updateTaskTemplate('t1', req)).resolves.toEqual({ key: 't1' });
    expect(tenantClient.patch).toHaveBeenCalledWith('/activity-plans/templates/t1', req);
    expect(client.patch).not.toHaveBeenCalled();
  });

  it('deleteTaskTemplate deletes template by key through the tenant-scoped client', async () => {
    tenantClient.delete.mockResolvedValue({ data: undefined });
    await activityPlans.deleteTaskTemplate('t1');
    expect(tenantClient.delete).toHaveBeenCalledWith('/activity-plans/templates/t1');
    expect(client.delete).not.toHaveBeenCalled();
  });
});
