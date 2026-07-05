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

import * as harvest from '@/api/endpoints/harvest';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('harvest endpoints — indicators', () => {
  it('getIndicators gets paginated indicators', async () => {
    client.get.mockResolvedValue({ data: [] });
    await harvest.getIndicators(5, 10);
    expect(client.get).toHaveBeenCalledWith('/harvest/indicators', {
      params: { offset: 5, limit: 10 },
    });
  });

  it('createIndicator posts payload', async () => {
    client.post.mockResolvedValue({ data: { key: 'i1' } });
    const payload = { name: 'Trichomes' } as never;
    await harvest.createIndicator(payload);
    expect(client.post).toHaveBeenCalledWith('/harvest/indicators', payload);
  });

  it('getIndicatorsForSpecies gets species indicators', async () => {
    client.get.mockResolvedValue({ data: [] });
    await harvest.getIndicatorsForSpecies('sp1');
    expect(client.get).toHaveBeenCalledWith('/harvest/species/sp1/indicators');
  });
});

describe('harvest endpoints — observations & readiness', () => {
  it('createObservation posts plant observation', async () => {
    client.post.mockResolvedValue({ data: { key: 'o1' } });
    const payload = { value: 'amber' } as never;
    await harvest.createObservation('pl1', payload);
    expect(client.post).toHaveBeenCalledWith('/harvest/plants/pl1/observations', payload);
  });

  it('getObservations gets paginated observations', async () => {
    client.get.mockResolvedValue({ data: [] });
    await harvest.getObservations('pl1');
    expect(client.get).toHaveBeenCalledWith('/harvest/plants/pl1/observations', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('assessReadiness gets readiness for plant', async () => {
    client.get.mockResolvedValue({ data: { ready: true } });
    await harvest.assessReadiness('pl1');
    expect(client.get).toHaveBeenCalledWith('/harvest/plants/pl1/readiness');
  });
});

describe('harvest endpoints — batches', () => {
  it('getBatches gets paginated batches', async () => {
    client.get.mockResolvedValue({ data: [] });
    await harvest.getBatches();
    expect(client.get).toHaveBeenCalledWith('/harvest/batches', {
      params: { offset: 0, limit: 50 },
    });
  });

  it('createBatch posts batch for plant', async () => {
    client.post.mockResolvedValue({ data: { key: 'b1' } });
    const payload = { weight_g: 100 } as never;
    await harvest.createBatch('pl1', payload);
    expect(client.post).toHaveBeenCalledWith('/harvest/plants/pl1/batches', payload);
  });

  it('getBatch gets batch by key', async () => {
    client.get.mockResolvedValue({ data: { key: 'b1' } });
    await harvest.getBatch('b1');
    expect(client.get).toHaveBeenCalledWith('/harvest/batches/b1');
  });

  it('updateBatch puts batch by key', async () => {
    client.put.mockResolvedValue({ data: { key: 'b1' } });
    const payload = { weight_g: 120 } as never;
    await harvest.updateBatch('b1', payload);
    expect(client.put).toHaveBeenCalledWith('/harvest/batches/b1', payload);
  });

  it('completeHarvest posts to the plant complete endpoint with empty body', async () => {
    client.post.mockResolvedValue({
      data: { plant_key: 'pl1', termination_type: 'harvested', removed_on: '2026-07-05' },
    });
    await harvest.completeHarvest('pl1');
    expect(client.post).toHaveBeenCalledWith('/harvest/plants/pl1/complete', {});
  });

  it('completeHarvest passes an explicit on_date when given', async () => {
    client.post.mockResolvedValue({
      data: { plant_key: 'pl1', termination_type: 'harvested', removed_on: '2026-06-01' },
    });
    await harvest.completeHarvest('pl1', '2026-06-01');
    expect(client.post).toHaveBeenCalledWith('/harvest/plants/pl1/complete', {
      on_date: '2026-06-01',
    });
  });
});

describe('harvest endpoints — quality, yield, stats', () => {
  it('createQualityAssessment posts assessment for batch', async () => {
    client.post.mockResolvedValue({ data: { key: 'q1' } });
    const payload = { score: 9 } as never;
    await harvest.createQualityAssessment('b1', payload);
    expect(client.post).toHaveBeenCalledWith('/harvest/batches/b1/quality', payload);
  });

  it('getQuality gets quality assessment', async () => {
    client.get.mockResolvedValue({ data: null });
    await expect(harvest.getQuality('b1')).resolves.toBeNull();
    expect(client.get).toHaveBeenCalledWith('/harvest/batches/b1/quality');
  });

  it('createYieldMetric posts yield for batch', async () => {
    client.post.mockResolvedValue({ data: { key: 'y1' } });
    const payload = { grams: 50 } as never;
    await harvest.createYieldMetric('b1', payload);
    expect(client.post).toHaveBeenCalledWith('/harvest/batches/b1/yield', payload);
  });

  it('getYield gets yield metric', async () => {
    client.get.mockResolvedValue({ data: null });
    await expect(harvest.getYield('b1')).resolves.toBeNull();
    expect(client.get).toHaveBeenCalledWith('/harvest/batches/b1/yield');
  });

  it('getYieldStats gets stats with default days_back', async () => {
    client.get.mockResolvedValue({ data: {} });
    await harvest.getYieldStats('sp1');
    expect(client.get).toHaveBeenCalledWith('/harvest/species/sp1/yield-stats', {
      params: { days_back: 365 },
    });
  });

  it('getYieldStats passes custom days_back', async () => {
    client.get.mockResolvedValue({ data: {} });
    await harvest.getYieldStats('sp1', 90);
    expect(client.get).toHaveBeenCalledWith('/harvest/species/sp1/yield-stats', {
      params: { days_back: 90 },
    });
  });
});
