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

import * as fertilizers from '@/api/endpoints/fertilizers';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('fertilizers endpoints — CRUD', () => {
  it('fetchFertilizers uses default pagination', async () => {
    client.get.mockResolvedValue({ data: [] });
    await fertilizers.fetchFertilizers();
    expect(client.get).toHaveBeenCalledWith('/fertilizers', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('fetchFertilizers merges filter entries', async () => {
    client.get.mockResolvedValue({ data: [] });
    await fertilizers.fetchFertilizers(5, 10, { type: 'base', brand: 'x' });
    expect(client.get).toHaveBeenCalledWith('/fertilizers', {
      params: { offset: 5, limit: 10, type: 'base', brand: 'x' },
    });
  });

  it('fetchFertilizer gets fertilizer by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'f1' } });
    await fertilizers.fetchFertilizer('f1');
    expect(client.get).toHaveBeenCalledWith('/fertilizers/f1');
  });

  it('createFertilizer posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'f1' } });
    const payload = { name: 'CalMag' } as never;
    await fertilizers.createFertilizer(payload);
    expect(client.post).toHaveBeenCalledWith('/fertilizers', payload);
  });

  it('updateFertilizer puts payload by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'f1' } });
    const payload = { name: 'X' } as never;
    await fertilizers.updateFertilizer('f1', payload);
    expect(client.put).toHaveBeenCalledWith('/fertilizers/f1', payload);
  });

  it('deleteFertilizer deletes by key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await fertilizers.deleteFertilizer('f1');
    expect(client.delete).toHaveBeenCalledWith('/fertilizers/f1');
  });
});

describe('fertilizers endpoints — stocks', () => {
  it('fetchFertilizerStocks gets stocks for fertilizer', async () => {
    client.get.mockResolvedValue({ data: [] });
    await fertilizers.fetchFertilizerStocks('f1');
    expect(client.get).toHaveBeenCalledWith('/fertilizers/f1/stocks');
  });

  it('createFertilizerStock posts stock for fertilizer', async () => {
    client.post.mockResolvedValue({ data: { key: 'st1' } });
    const payload = { amount: 5 } as never;
    await fertilizers.createFertilizerStock('f1', payload);
    expect(client.post).toHaveBeenCalledWith('/fertilizers/f1/stocks', payload);
  });

  it('deleteFertilizerStock deletes stock by composite key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await fertilizers.deleteFertilizerStock('f1', 'st1');
    expect(client.delete).toHaveBeenCalledWith('/fertilizers/f1/stocks/st1');
  });
});

describe('fertilizers endpoints — incompatibilities & usage', () => {
  it('fetchIncompatibilities gets incompatibilities', async () => {
    client.get.mockResolvedValue({ data: [] });
    await fertilizers.fetchIncompatibilities('f1');
    expect(client.get).toHaveBeenCalledWith('/fertilizers/f1/incompatibilities');
  });

  it('fetchNutrientPlanUsage gets nutrient plan usage', async () => {
    client.get.mockResolvedValue({ data: [] });
    await fertilizers.fetchNutrientPlanUsage('f1');
    expect(client.get).toHaveBeenCalledWith('/fertilizers/f1/nutrient-plans');
  });
});
