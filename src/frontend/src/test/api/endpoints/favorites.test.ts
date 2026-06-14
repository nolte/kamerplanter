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

import * as favorites from '@/api/endpoints/favorites';

const client = mocks.client;

beforeEach(() => {
  vi.clearAllMocks();
});

describe('favorites endpoints', () => {
  it('listFavorites gets with undefined params when no type', async () => {
    client.get.mockResolvedValue({ data: [] });
    await favorites.listFavorites();
    expect(client.get).toHaveBeenCalledWith('/favorites', { params: undefined });
  });

  it('listFavorites adds type param when provided', async () => {
    client.get.mockResolvedValue({ data: [] });
    await favorites.listFavorites('species');
    expect(client.get).toHaveBeenCalledWith('/favorites', { params: { type: 'species' } });
  });

  it('addFavorite posts with default source', async () => {
    client.post.mockResolvedValue({ data: { key: 'fav1' } });
    await favorites.addFavorite('sp1');
    expect(client.post).toHaveBeenCalledWith('/favorites', {
      target_key: 'sp1',
      source: 'manual',
    });
  });

  it('addFavorite posts with custom source', async () => {
    client.post.mockResolvedValue({ data: { key: 'fav1' } });
    await favorites.addFavorite('sp1', 'onboarding');
    expect(client.post).toHaveBeenCalledWith('/favorites', {
      target_key: 'sp1',
      source: 'onboarding',
    });
  });

  it('removeFavorite deletes by target key', async () => {
    client.delete.mockResolvedValue({ data: undefined });
    await favorites.removeFavorite('sp1');
    expect(client.delete).toHaveBeenCalledWith('/favorites/sp1');
  });

  it('getMatchingNutrientPlans joins species keys into param', async () => {
    client.get.mockResolvedValue({ data: [] });
    await favorites.getMatchingNutrientPlans(['sp1', 'sp2']);
    expect(client.get).toHaveBeenCalledWith('/favorites/nutrient-plans/matching', {
      params: { species_keys: 'sp1,sp2' },
    });
  });
});
