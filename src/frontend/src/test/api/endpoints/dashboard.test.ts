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

import * as dashboard from '@/api/endpoints/dashboard';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('dashboard endpoints', () => {
  it('getWidgetCatalog GETs the widget catalog', async () => {
    client.get.mockResolvedValue({ data: { widgets: [] } });
    const result = await dashboard.getWidgetCatalog();
    expect(client.get).toHaveBeenCalledWith('/dashboard/widgets/catalog');
    expect(result).toEqual({ widgets: [] });
  });

  it('getAggregated joins widget keys into a comma-separated param', async () => {
    client.get.mockResolvedValue({ data: {} });
    await dashboard.getAggregated(['plants', 'tasks', 'weather']);
    expect(client.get).toHaveBeenCalledWith('/dashboard/aggregated', {
      params: { widgets: 'plants,tasks,weather' },
    });
  });

  it('getAggregated sends an empty param for no widgets', async () => {
    client.get.mockResolvedValue({ data: {} });
    await dashboard.getAggregated([]);
    expect(client.get).toHaveBeenCalledWith('/dashboard/aggregated', {
      params: { widgets: '' },
    });
  });
});
