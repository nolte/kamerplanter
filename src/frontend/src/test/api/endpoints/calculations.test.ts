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

import * as calc from '@/api/endpoints/calculations';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('calculations endpoints', () => {
  it('calculateVPD posts to /calculations/vpd', async () => {
    client.post.mockResolvedValue({ data: { vpd: 1.2 } });
    const payload = { temp_c: 25, rh: 60 } as never;
    await calc.calculateVPD(payload);
    expect(client.post).toHaveBeenCalledWith('/calculations/vpd', payload);
  });

  it('calculateGDD posts to /calculations/gdd', async () => {
    client.post.mockResolvedValue({ data: { gdd: 10 } });
    const payload = { tmax: 30, tmin: 15, tbase: 10 } as never;
    await calc.calculateGDD(payload);
    expect(client.post).toHaveBeenCalledWith('/calculations/gdd', payload);
  });

  it('calculatePhotoperiodTransition posts to photoperiod-transition', async () => {
    client.post.mockResolvedValue({ data: [] });
    const payload = { start_hours: 18 } as never;
    await calc.calculatePhotoperiodTransition(payload);
    expect(client.post).toHaveBeenCalledWith('/calculations/photoperiod-transition', payload);
  });

  it('calculateSunTimes posts to sun-times', async () => {
    client.post.mockResolvedValue({ data: {} });
    const payload = { lat: 52, lon: 13 } as never;
    await calc.calculateSunTimes(payload);
    expect(client.post).toHaveBeenCalledWith('/calculations/sun-times', payload);
  });

  it('calculateSlotCapacity posts to slot-capacity', async () => {
    client.post.mockResolvedValue({ data: {} });
    const payload = { slot_key: 'sl1' } as never;
    await calc.calculateSlotCapacity(payload);
    expect(client.post).toHaveBeenCalledWith('/calculations/slot-capacity', payload);
  });
});
