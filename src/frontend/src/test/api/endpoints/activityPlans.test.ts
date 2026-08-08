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
  // #1003 — generation moved to the tenant-scoped client with the two writes.
  // Which plan comes back depends on whether the calling tenant has forked it,
  // and an unprefixed request cannot express that.
  it('generatePlan posts through the tenant-scoped client and returns data', async () => {
    tenantClient.post.mockResolvedValue({ data: { tasks: [] } });
    const req = { plant_key: 'p1' } as never;
    await expect(activityPlans.generatePlan(req)).resolves.toEqual({ tasks: [] });
    expect(tenantClient.post).toHaveBeenCalledWith('/activity-plans/generate', req);
    expect(client.post).not.toHaveBeenCalled();
  });

  // Moved under /t/{slug}/ for #1000: /apply used to be global and took its
  // tenant from the request body, so any user could create tasks in an arbitrary
  // tenant. It now goes through the tenant-scoped client, which prepends the slug.
  it('applyPlan posts request through the tenant-scoped client and returns data', async () => {
    tenantClient.post.mockResolvedValue({ data: { created: 2 } });
    const req = { workflow_template_key: 'wf1', plant_key: 'pl1' } as never;
    await expect(activityPlans.applyPlan(req)).resolves.toEqual({ created: 2 });
    expect(tenantClient.post).toHaveBeenCalledWith('/activity-plans/apply', req);
    expect(client.post).not.toHaveBeenCalled();
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
