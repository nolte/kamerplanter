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

import * as prefs from '@/api/endpoints/userPreferences';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('userPreferences endpoints', () => {
  it('getPreferences gets /user-preferences', async () => {
    client.get.mockResolvedValue({ data: { theme: 'dark' } });
    await expect(prefs.getPreferences()).resolves.toEqual({ theme: 'dark' });
    expect(client.get).toHaveBeenCalledWith('/user-preferences');
  });

  it('updatePreferences patches updates', async () => {
    client.patch.mockResolvedValue({ data: { theme: 'light' } });
    const updates = { theme: 'light', watering_can_liters: 5 };
    await prefs.updatePreferences(updates);
    expect(client.patch).toHaveBeenCalledWith('/user-preferences', updates);
  });
});
