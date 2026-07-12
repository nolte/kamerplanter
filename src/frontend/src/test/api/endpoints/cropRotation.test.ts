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

import * as cropRotation from '@/api/endpoints/cropRotation';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('cropRotation endpoints', () => {
  it('getSuccessors gets successors for family', async () => {
    client.get.mockResolvedValue({ data: [] });
    await cropRotation.getSuccessors('fa1');
    expect(client.get).toHaveBeenCalledWith('/crop-rotation/families/fa1/successors');
  });

  it('setSuccessor posts successor payload', async () => {
    client.post.mockResolvedValue({ data: undefined });
    const payload = { family_key: 'fa1', successor_key: 'fa2' } as never;
    await cropRotation.setSuccessor(payload);
    expect(client.post).toHaveBeenCalledWith('/crop-rotation/successors', payload);
  });

  it('getRotationCounts gets the whole-catalogue successor-count map', async () => {
    client.get.mockResolvedValue({ data: { solanaceae: 3, fabaceae: 1 } });
    const counts = await cropRotation.getRotationCounts();
    expect(client.get).toHaveBeenCalledWith('/crop-rotation/counts');
    expect(counts).toEqual({ solanaceae: 3, fabaceae: 1 });
  });
});
