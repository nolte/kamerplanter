import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({ client: { get: vi.fn(), post: vi.fn() } }));

vi.mock('@/api/client', () => ({
  __esModule: true,
  default: mocks.client,
  tenantClient: mocks.client,
}));

import { getGardenPlan } from './gardenPlan';

beforeEach(() => {
  vi.clearAllMocks();
  mocks.client.get.mockResolvedValue({ data: { site_key: 'site_1' } });
});

describe('getGardenPlan (GP-API-001)', () => {
  it('sends no query parameters when neither include nor asOf is given', async () => {
    await getGardenPlan('site_1');
    expect(mocks.client.get).toHaveBeenCalledWith('/sites/site_1/plan', { params: undefined });
  });

  it('sends include alone as before', async () => {
    await getGardenPlan('site_1', ['tasks']);
    expect(mocks.client.get).toHaveBeenCalledWith('/sites/site_1/plan', {
      params: { include: 'tasks' },
    });
  });

  it('sends as_of for the historical plant state (#2901)', async () => {
    await getGardenPlan('site_1', undefined, '2025-07-15');
    expect(mocks.client.get).toHaveBeenCalledWith('/sites/site_1/plan', {
      params: { as_of: '2025-07-15' },
    });
  });

  it('sends include and as_of together', async () => {
    await getGardenPlan('site_1', ['plants', 'zones'], '2025-07-15');
    expect(mocks.client.get).toHaveBeenCalledWith('/sites/site_1/plan', {
      params: { include: 'plants,zones', as_of: '2025-07-15' },
    });
  });
});
