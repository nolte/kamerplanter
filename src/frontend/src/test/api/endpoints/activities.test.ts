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
  // #995: sending no paging argument used to send no `offset`/`limit` either,
  // and the backend then applied its own default of 50 — which is how one of the
  // 51 seeded activities came to be permanently absent from the list view. The
  // paging is now explicit, so the bound is visible in the request rather than
  // inferred from a backend default nobody reads.
  it('listActivities sends the paging defaults explicitly', async () => {
    client.get.mockResolvedValue({ data: [] });
    await activities.listActivities();
    expect(client.get).toHaveBeenCalledWith('/activities', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('listActivities forwards filter params alongside the paging', async () => {
    client.get.mockResolvedValue({ data: [] });
    const params = { category: 'care', scope: 'universal' as const, species: 'sp1' };
    await activities.listActivities(params);
    expect(client.get).toHaveBeenCalledWith('/activities', {
      params: { ...params, offset: 0, limit: 50 },
    });
  });

  it('listAllActivities pages until a short page, keeping the filters', async () => {
    const full = Array.from({ length: 200 }, (_v, i) => ({ key: `a${i}` }));
    client.get
      .mockResolvedValueOnce({ data: full })
      .mockResolvedValueOnce({ data: [{ key: 'tail' }] });

    const all = await activities.listAllActivities({ category: 'care' });

    expect(all).toHaveLength(201);
    expect(client.get).toHaveBeenCalledTimes(2);
    expect(client.get).toHaveBeenNthCalledWith(1, '/activities', {
      params: { category: 'care', offset: 0, limit: 200 },
    });
    expect(client.get).toHaveBeenNthCalledWith(2, '/activities', {
      params: { category: 'care', offset: 200, limit: 200 },
    });
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
