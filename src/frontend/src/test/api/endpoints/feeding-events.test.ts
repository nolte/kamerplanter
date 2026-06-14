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

import * as feeding from '@/api/endpoints/feeding-events';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('feeding-events endpoints', () => {
  it('listFeedingEvents gets paginated events', async () => {
    client.get.mockResolvedValue({ data: [] });
    await feeding.listFeedingEvents(5, 10);
    expect(client.get).toHaveBeenCalledWith('/feeding-events', {
      params: { offset: 5, limit: 10 },
    });
  });

  it('getFeedingEvent gets event by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'fe1' } });
    await feeding.getFeedingEvent('fe1');
    expect(client.get).toHaveBeenCalledWith('/feeding-events/fe1');
  });

  it('createFeedingEvent posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'fe1' } });
    const payload = { volume_liters: 1 } as never;
    await feeding.createFeedingEvent(payload);
    expect(client.post).toHaveBeenCalledWith('/feeding-events', payload);
  });

  it('updateFeedingEvent puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'fe1' } });
    const payload = { volume_liters: 2 };
    await feeding.updateFeedingEvent('fe1', payload);
    expect(client.put).toHaveBeenCalledWith('/feeding-events/fe1', payload);
  });

  it('deleteFeedingEvent deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await feeding.deleteFeedingEvent('fe1');
    expect(client.delete).toHaveBeenCalledWith('/feeding-events/fe1');
  });

  it('getPlantFeedingHistory gets plant feeding logs', async () => {
    client.get.mockResolvedValue({ data: [] });
    await feeding.getPlantFeedingHistory('pl1');
    expect(client.get).toHaveBeenCalledWith('/feeding-events/plant/pl1', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('analyzeRunoff gets runoff analysis', async () => {
    client.get.mockResolvedValue({ data: {} });
    await feeding.analyzeRunoff('fe1');
    expect(client.get).toHaveBeenCalledWith('/feeding-events/fe1/runoff');
  });
});
