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

import * as season from '@/api/endpoints/season';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('season endpoints', () => {
  it('getSeasonOverview GETs the aggregated overview', async () => {
    client.get.mockResolvedValue({ data: { sites: [] } });
    const result = await season.getSeasonOverview();
    expect(client.get).toHaveBeenCalledWith('/season/overview');
    expect(result).toEqual({ sites: [] });
  });

  it('getPlantOverwintering GETs the per-plant profile', async () => {
    client.get.mockResolvedValue({ data: { key: 'ow1' } });
    await season.getPlantOverwintering('plant-1');
    expect(client.get).toHaveBeenCalledWith('/plants/plant-1/overwintering');
  });

  it('getPlantOverwinteringStatus GETs the status subresource', async () => {
    client.get.mockResolvedValue({ data: { site_overwinterable: true } });
    await season.getPlantOverwinteringStatus('plant-1');
    expect(client.get).toHaveBeenCalledWith('/plants/plant-1/overwintering/status');
  });

  it('overridePlantOverwintering PATCHes the override patch', async () => {
    const patch = { protection_method: 'fleece' } as never;
    client.patch.mockResolvedValue({ data: { key: 'ow1' } });
    await season.overridePlantOverwintering('plant-1', patch);
    expect(client.patch).toHaveBeenCalledWith('/plants/plant-1/overwintering', patch);
  });

  it('resetPlantOverwintering POSTs the reset with an empty body', async () => {
    client.post.mockResolvedValue({ data: { key: 'ow1' } });
    await season.resetPlantOverwintering('plant-1');
    expect(client.post).toHaveBeenCalledWith('/plants/plant-1/overwintering/reset', {});
  });
});
