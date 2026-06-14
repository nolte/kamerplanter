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

import * as watering from '@/api/endpoints/wateringConfirm';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('wateringConfirm endpoints', () => {
  it('confirmWatering posts to /watering-events/confirm and returns data', async () => {
    client.post.mockResolvedValue({ data: { confirmed: true } });
    const payload = { run_key: 'r1' } as never;
    await expect(watering.confirmWatering(payload)).resolves.toEqual({ confirmed: true });
    expect(client.post).toHaveBeenCalledWith('/watering-events/confirm', payload);
  });

  it('quickConfirmWatering posts to /watering-events/quick-confirm', async () => {
    client.post.mockResolvedValue({ data: { confirmed: true } });
    const payload = { plant_key: 'p1' } as never;
    await expect(watering.quickConfirmWatering(payload)).resolves.toEqual({ confirmed: true });
    expect(client.post).toHaveBeenCalledWith('/watering-events/quick-confirm', payload);
  });
});
