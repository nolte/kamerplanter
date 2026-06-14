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

import * as events from '@/api/endpoints/watering-events';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('watering-events endpoints', () => {
  it('createWateringEvent posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'we1' } });
    const payload = { volume_liters: 1 } as never;
    await events.createWateringEvent(payload);
    expect(client.post).toHaveBeenCalledWith('/watering-events', payload);
  });

  it('getWateringEvent gets event by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'we1' } });
    await events.getWateringEvent('we1');
    expect(client.get).toHaveBeenCalledWith('/watering-events/we1');
  });

  it('listWateringEvents gets paginated events', async () => {
    client.get.mockResolvedValue({ data: [] });
    await events.listWateringEvents(5, 10);
    expect(client.get).toHaveBeenCalledWith('/watering-events', {
      params: { offset: 5, limit: 10 },
    });
  });

  it('getPlantWateringEvents gets plant events', async () => {
    client.get.mockResolvedValue({ data: [] });
    await events.getPlantWateringEvents('pl1');
    expect(client.get).toHaveBeenCalledWith('/plant-instances/pl1/watering-events', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('getLocationWateringEvents gets location events', async () => {
    client.get.mockResolvedValue({ data: [] });
    await events.getLocationWateringEvents('loc1');
    expect(client.get).toHaveBeenCalledWith('/locations/loc1/watering-events', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('getLocationWateringStats gets location stats', async () => {
    client.get.mockResolvedValue({ data: {} });
    await events.getLocationWateringStats('loc1');
    expect(client.get).toHaveBeenCalledWith('/locations/loc1/watering-stats');
  });

  it('getWateringVolumeSuggestion gets with default hemisphere and undefined reference date', async () => {
    client.get.mockResolvedValue({ data: {} });
    await events.getWateringVolumeSuggestion('pl1');
    expect(client.get).toHaveBeenCalledWith(
      '/plant-instances/pl1/watering-volume-suggestion',
      { params: { reference_date: undefined, hemisphere: 'north' } },
    );
  });

  it('getWateringVolumeSuggestion passes reference date and hemisphere', async () => {
    client.get.mockResolvedValue({ data: {} });
    await events.getWateringVolumeSuggestion('pl1', '2026-06-14', 'south');
    expect(client.get).toHaveBeenCalledWith(
      '/plant-instances/pl1/watering-volume-suggestion',
      { params: { reference_date: '2026-06-14', hemisphere: 'south' } },
    );
  });
});
