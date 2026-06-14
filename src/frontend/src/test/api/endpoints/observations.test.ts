import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const make = () => ({
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  });
  // observations.ts reads sensor readings via the tenantClient and the
  // global timeseries status via the default client.
  return { globalClient: make(), tenantClient: make() };
});

vi.mock('@/api/client', () => ({
  __esModule: true,
  default: mocks.globalClient,
  tenantClient: mocks.tenantClient,
}));

import * as observations from '@/api/endpoints/observations';

const globalClient = mocks.globalClient;
const tenantClient = mocks.tenantClient;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('observations endpoints', () => {
  it('getSensorReadings gets via tenant client with default raw resolution', async () => {
    tenantClient.get.mockResolvedValue({ data: { readings: [] } });
    await observations.getSensorReadings('se1', '2026-01-01', '2026-01-02');
    expect(tenantClient.get).toHaveBeenCalledWith('/observations/sensors/se1/readings', {
      params: { start: '2026-01-01', end: '2026-01-02', resolution: 'raw' },
    });
  });

  it('getSensorReadings passes explicit resolution', async () => {
    tenantClient.get.mockResolvedValue({ data: { readings: [] } });
    await observations.getSensorReadings('se1', '2026-01-01', '2026-01-02', 'hourly');
    expect(tenantClient.get).toHaveBeenCalledWith('/observations/sensors/se1/readings', {
      params: { start: '2026-01-01', end: '2026-01-02', resolution: 'hourly' },
    });
  });

  it('getTimeseriesStatus gets via global client', async () => {
    globalClient.get.mockResolvedValue({ data: {} });
    await observations.getTimeseriesStatus();
    expect(globalClient.get).toHaveBeenCalledWith('/observations/status');
    expect(tenantClient.get).not.toHaveBeenCalled();
  });
});
