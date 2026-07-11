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

import * as postHarvest from '@/api/endpoints/postHarvest';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('post-harvest endpoints', () => {
  it('getBatches lists with pagination', async () => {
    client.get.mockResolvedValue({ data: [] });
    await postHarvest.getBatches(10, 20);
    expect(client.get).toHaveBeenCalledWith('/post-harvest', {
      params: { offset: 10, limit: 20 },
    });
  });

  it('getBatchesForHarvest filters by harvest_batch', async () => {
    client.get.mockResolvedValue({ data: [] });
    await postHarvest.getBatchesForHarvest('hb1');
    expect(client.get).toHaveBeenCalledWith('/post-harvest', {
      params: { harvest_batch: 'hb1' },
    });
  });

  it('startDrying posts payload to start-drying', async () => {
    client.post.mockResolvedValue({ data: { key: 'ph1' } });
    const payload = { harvest_batch_key: 'hb1' };
    await postHarvest.startDrying(payload);
    expect(client.post).toHaveBeenCalledWith('/post-harvest/start-drying', payload);
  });

  it('getBatch fetches detail', async () => {
    client.get.mockResolvedValue({ data: { batch: {} } });
    await postHarvest.getBatch('ph1');
    expect(client.get).toHaveBeenCalledWith('/post-harvest/ph1');
  });

  it('advanceStage posts target_stage', async () => {
    client.post.mockResolvedValue({ data: { key: 'ph1' } });
    await postHarvest.advanceStage('ph1', 'curing');
    expect(client.post).toHaveBeenCalledWith('/post-harvest/ph1/advance', {
      target_stage: 'curing',
    });
  });

  it('recordDryingProgress posts weight', async () => {
    client.post.mockResolvedValue({ data: { key: 'dp1' } });
    await postHarvest.recordDryingProgress('ph1', { current_weight_g: 180 });
    expect(client.post).toHaveBeenCalledWith('/post-harvest/ph1/drying-progress', {
      current_weight_g: 180,
    });
  });

  it('recordObservation posts observation', async () => {
    client.post.mockResolvedValue({ data: { key: 'obs1' } });
    await postHarvest.recordObservation('ph1', { rh_percent: 68 });
    expect(client.post).toHaveBeenCalledWith('/post-harvest/ph1/observations', {
      rh_percent: 68,
    });
  });

  it('getMoldAlerts fetches alerts', async () => {
    client.get.mockResolvedValue({ data: [] });
    await postHarvest.getMoldAlerts('ph1');
    expect(client.get).toHaveBeenCalledWith('/post-harvest/ph1/mold-alerts');
  });

  it('deleteBatch deletes', async () => {
    client.delete.mockResolvedValue({ data: null });
    await postHarvest.deleteBatch('ph1');
    expect(client.delete).toHaveBeenCalledWith('/post-harvest/ph1');
  });

  it('getDryingProgress lists progress', async () => {
    client.get.mockResolvedValue({ data: [] });
    await postHarvest.getDryingProgress('ph1');
    expect(client.get).toHaveBeenCalledWith('/post-harvest/ph1/drying-progress');
  });

  it('getObservations lists observations', async () => {
    client.get.mockResolvedValue({ data: [] });
    await postHarvest.getObservations('ph1');
    expect(client.get).toHaveBeenCalledWith('/post-harvest/ph1/observations');
  });
});
