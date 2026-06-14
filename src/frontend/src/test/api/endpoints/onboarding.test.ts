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

import * as onboarding from '@/api/endpoints/onboarding';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('onboarding endpoints', () => {
  it('getState gets /onboarding/state', async () => {
    client.get.mockResolvedValue({ data: { step: 0 } });
    await onboarding.getState();
    expect(client.get).toHaveBeenCalledWith('/onboarding/state');
  });

  it('complete posts payload to /onboarding/complete', async () => {
    client.post.mockResolvedValue({ data: {} });
    const payload = { kit_id: 'k1', plant_count: 3 };
    await onboarding.complete(payload);
    expect(client.post).toHaveBeenCalledWith('/onboarding/complete', payload);
  });

  it('skip posts to /onboarding/skip', async () => {
    client.post.mockResolvedValue({ data: { step: 0 } });
    await onboarding.skip();
    expect(client.post).toHaveBeenCalledWith('/onboarding/skip');
  });

  it('updateProgress patches /onboarding/state', async () => {
    client.patch.mockResolvedValue({ data: { step: 2 } });
    const payload = { wizard_step: 2 };
    await onboarding.updateProgress(payload);
    expect(client.patch).toHaveBeenCalledWith('/onboarding/state', payload);
  });

  it('reset posts to /onboarding/reset', async () => {
    client.post.mockResolvedValue({ data: { step: 0 } });
    await onboarding.reset();
    expect(client.post).toHaveBeenCalledWith('/onboarding/reset');
  });
});
