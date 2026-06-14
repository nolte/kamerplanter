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

import * as logs from '@/api/endpoints/watering-logs';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('watering-logs endpoints — CRUD', () => {
  it('listWateringLogs gets paginated logs', async () => {
    client.get.mockResolvedValue({ data: [] });
    await logs.listWateringLogs(5, 10);
    expect(client.get).toHaveBeenCalledWith('/watering-logs', {
      params: { offset: 5, limit: 10 },
    });
  });

  it('getWateringLog gets log by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'w1' } });
    await logs.getWateringLog('w1');
    expect(client.get).toHaveBeenCalledWith('/watering-logs/w1');
  });

  it('createWateringLog posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'w1' } });
    const payload = { volume_liters: 1 } as never;
    await logs.createWateringLog(payload);
    expect(client.post).toHaveBeenCalledWith('/watering-logs', payload);
  });

  it('updateWateringLog puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'w1' } });
    const payload = { volume_liters: 2 } as never;
    await logs.updateWateringLog('w1', payload);
    expect(client.put).toHaveBeenCalledWith('/watering-logs/w1', payload);
  });

  it('deleteWateringLog deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await logs.deleteWateringLog('w1');
    expect(client.delete).toHaveBeenCalledWith('/watering-logs/w1');
  });
});

describe('watering-logs endpoints — queries', () => {
  it('getPlantWateringHistory gets plant logs', async () => {
    client.get.mockResolvedValue({ data: [] });
    await logs.getPlantWateringHistory('pl1');
    expect(client.get).toHaveBeenCalledWith('/watering-logs/plant/pl1', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('analyzeRunoff gets runoff analysis', async () => {
    client.get.mockResolvedValue({ data: { ec: 1 } });
    await logs.analyzeRunoff('w1');
    expect(client.get).toHaveBeenCalledWith('/watering-logs/w1/runoff');
  });

  it('getSlotWateringLogs gets slot logs', async () => {
    client.get.mockResolvedValue({ data: [] });
    await logs.getSlotWateringLogs('sl1', 5, 10);
    expect(client.get).toHaveBeenCalledWith('/slots/sl1/watering-logs', {
      params: { offset: 5, limit: 10 },
    });
  });

  it('getLocationWateringLogs gets location logs', async () => {
    client.get.mockResolvedValue({ data: [] });
    await logs.getLocationWateringLogs('loc1');
    expect(client.get).toHaveBeenCalledWith('/locations/loc1/watering-logs', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('getLocationWateringStats gets stats', async () => {
    client.get.mockResolvedValue({ data: {} });
    await logs.getLocationWateringStats('loc1');
    expect(client.get).toHaveBeenCalledWith('/locations/loc1/watering-stats');
  });
});
