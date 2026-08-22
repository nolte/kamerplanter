/**
 * The server-backed favorites hook and its one-off localStorage carry-over (#1233).
 *
 * The carry-over is the part that can lose user data silently, so it gets the
 * most attention: the storage key is the ONLY place a pre-#1233 favorite lives,
 * and removing it before the posts succeed would drop the difference with no
 * trace. The tests therefore assert when the key survives, not only when it goes.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import * as favoritesApi from '@/api/endpoints/favorites';
import { carryOverLegacyFavorites, useServerFavorites } from '@/hooks/useServerFavorites';

vi.mock('@/api/endpoints/favorites');

const KEY = 'kamerplanter-substrate-favorites';

// jsdom in this environment ships no native localStorage; the map-backed mock
// mirrors what the other storage tests install.
const storageMap = new Map<string, string>();
const mockLocalStorage = {
  getItem: vi.fn((k: string) => storageMap.get(k) ?? null),
  setItem: vi.fn((k: string, v: string) => void storageMap.set(k, v)),
  removeItem: vi.fn((k: string) => void storageMap.delete(k)),
  clear: vi.fn(() => storageMap.clear()),
};

beforeEach(() => {
  storageMap.clear();
  vi.stubGlobal('localStorage', mockLocalStorage);
  vi.mocked(favoritesApi.listFavorites).mockResolvedValue([]);
  vi.mocked(favoritesApi.addFavorite).mockResolvedValue({} as never);
  vi.mocked(favoritesApi.removeFavorite).mockResolvedValue(undefined);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe('carryOverLegacyFavorites', () => {
  it('posts every stored key the server does not already have', async () => {
    storageMap.set(KEY, JSON.stringify(['a', 'b']));

    const carried = await carryOverLegacyFavorites(KEY, new Set());

    expect(vi.mocked(favoritesApi.addFavorite).mock.calls.map((c) => c[0])).toEqual(['a', 'b']);
    expect(carried).toEqual(new Set(['a', 'b']));
  });

  it('skips keys the server already knows', async () => {
    storageMap.set(KEY, JSON.stringify(['a', 'b']));

    await carryOverLegacyFavorites(KEY, new Set(['a']));

    expect(vi.mocked(favoritesApi.addFavorite).mock.calls.map((c) => c[0])).toEqual(['b']);
  });

  it('clears the storage key once every post succeeded', async () => {
    storageMap.set(KEY, JSON.stringify(['a']));

    await carryOverLegacyFavorites(KEY, new Set());

    expect(storageMap.has(KEY)).toBe(false);
  });

  it('KEEPS the storage key when a post failed, so the rest is retried', async () => {
    // The data-loss case. Removing the key here would drop 'b' with no trace:
    // localStorage was its only home.
    storageMap.set(KEY, JSON.stringify(['a', 'b']));
    vi.mocked(favoritesApi.addFavorite)
      .mockResolvedValueOnce({} as never)
      .mockRejectedValueOnce(new Error('offline'));

    const carried = await carryOverLegacyFavorites(KEY, new Set());

    expect(storageMap.get(KEY)).toBe(JSON.stringify(['a', 'b']));
    expect(carried).toEqual(new Set(['a']));
  });

  it('clears the key when everything stored is already on the server', async () => {
    storageMap.set(KEY, JSON.stringify(['a']));

    await carryOverLegacyFavorites(KEY, new Set(['a']));

    expect(favoritesApi.addFavorite).not.toHaveBeenCalled();
    expect(storageMap.has(KEY)).toBe(false);
  });

  it('does nothing when there is no stored key', async () => {
    const carried = await carryOverLegacyFavorites(KEY, new Set());

    expect(carried).toEqual(new Set());
    expect(favoritesApi.addFavorite).not.toHaveBeenCalled();
  });

  it('drops an unparseable value instead of retrying it forever', async () => {
    storageMap.set(KEY, 'not json at all');

    const carried = await carryOverLegacyFavorites(KEY, new Set());

    expect(carried).toEqual(new Set());
  });

  it('discards a stored value that is not an array', async () => {
    storageMap.set(KEY, JSON.stringify({ a: true }));

    await carryOverLegacyFavorites(KEY, new Set());

    expect(favoritesApi.addFavorite).not.toHaveBeenCalled();
    expect(storageMap.has(KEY)).toBe(false);
  });
});

describe('useServerFavorites', () => {
  it('loads the entity type it was given', async () => {
    renderHook(() => useServerFavorites('substrates'));

    await waitFor(() => expect(favoritesApi.listFavorites).toHaveBeenCalledWith('substrates'));
  });

  it('surfaces carried-over favorites without a reload', async () => {
    storageMap.set(KEY, JSON.stringify(['a']));

    const { result } = renderHook(() => useServerFavorites('substrates', KEY));

    await waitFor(() => expect(result.current.isFavorite('a')).toBe(true));
    expect(result.current.hasFavorites).toBe(true);
  });

  it('does not touch localStorage when no legacy key is given', async () => {
    storageMap.set(KEY, JSON.stringify(['a']));

    renderHook(() => useServerFavorites('species'));

    await waitFor(() => expect(favoritesApi.listFavorites).toHaveBeenCalled());
    expect(favoritesApi.addFavorite).not.toHaveBeenCalled();
    expect(storageMap.has(KEY)).toBe(true);
  });

  it('reverts an optimistic add when the server refuses', async () => {
    vi.mocked(favoritesApi.addFavorite).mockRejectedValue(new Error('403'));
    const { result } = renderHook(() => useServerFavorites('substrates'));
    await waitFor(() => expect(favoritesApi.listFavorites).toHaveBeenCalled());

    result.current.toggleFavorite('a');

    await waitFor(() => expect(result.current.isFavorite('a')).toBe(false));
  });

  it('degrades to an empty set when the list call fails', async () => {
    vi.mocked(favoritesApi.listFavorites).mockRejectedValue(new Error('401'));

    const { result } = renderHook(() => useServerFavorites('substrates'));

    await waitFor(() => expect(favoritesApi.listFavorites).toHaveBeenCalled());
    expect(result.current.hasFavorites).toBe(false);
  });
});
