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

import * as activities from '@/api/endpoints/activities';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('activities endpoints', () => {
  it('listActivities gets with undefined params by default', async () => {
    client.get.mockResolvedValue({ data: [] });
    await activities.listActivities();
    expect(client.get).toHaveBeenCalledWith('/activities', { params: undefined });
  });

  it('listActivities forwards filter params', async () => {
    client.get.mockResolvedValue({ data: [] });
    const params = { category: 'care', scope: 'universal' as const, species: 'sp1' };
    await activities.listActivities(params);
    expect(client.get).toHaveBeenCalledWith('/activities', { params });
  });

  it('getActivity gets activity by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'a1' } });
    await activities.getActivity('a1');
    expect(client.get).toHaveBeenCalledWith('/activities/a1');
  });

  it('createActivity posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'a1' } });
    const payload = { name: 'Prune' } as never;
    await activities.createActivity(payload);
    expect(client.post).toHaveBeenCalledWith('/activities', payload);
  });

  it('updateActivity puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'a1' } });
    const payload = { name: 'X' } as never;
    await activities.updateActivity('a1', payload);
    expect(client.put).toHaveBeenCalledWith('/activities/a1', payload);
  });

  it('deleteActivity deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await activities.deleteActivity('a1');
    expect(client.delete).toHaveBeenCalledWith('/activities/a1');
  });
});
