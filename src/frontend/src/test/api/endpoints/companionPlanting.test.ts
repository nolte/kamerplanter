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

import * as companion from '@/api/endpoints/companionPlanting';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('companionPlanting endpoints', () => {
  it('getCompatibleSpecies gets compatible list', async () => {
    client.get.mockResolvedValue({ data: [] });
    await companion.getCompatibleSpecies('sp1');
    expect(client.get).toHaveBeenCalledWith('/companion-planting/species/sp1/compatible');
  });

  it('getIncompatibleSpecies gets incompatible list', async () => {
    client.get.mockResolvedValue({ data: [] });
    await companion.getIncompatibleSpecies('sp1');
    expect(client.get).toHaveBeenCalledWith('/companion-planting/species/sp1/incompatible');
  });

  it('setCompatible posts compatibility payload', async () => {
    client.post.mockResolvedValue({ data: undefined });
    const payload = { species_a: 'sp1', species_b: 'sp2' } as never;
    await companion.setCompatible(payload);
    expect(client.post).toHaveBeenCalledWith('/companion-planting/compatible', payload);
  });

  it('setIncompatible posts incompatibility payload', async () => {
    client.post.mockResolvedValue({ data: undefined });
    const payload = { species_a: 'sp1', species_b: 'sp2' } as never;
    await companion.setIncompatible(payload);
    expect(client.post).toHaveBeenCalledWith('/companion-planting/incompatible', payload);
  });
});
