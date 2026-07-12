import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useFamilyFavorites } from '@/hooks/useFamilyFavorites';
import * as favoritesApi from '@/api/endpoints/favorites';

// Isolated module mock — no contact with the real HTTP client or handlers.ts.
vi.mock('@/api/endpoints/favorites');

const mockListFavorites = vi.mocked(favoritesApi.listFavorites);
const mockAddFavorite = vi.mocked(favoritesApi.addFavorite);
const mockRemoveFavorite = vi.mocked(favoritesApi.removeFavorite);

function favoriteEntry(targetKey: string) {
  return { target_key: targetKey } as Awaited<ReturnType<typeof favoritesApi.listFavorites>>[number];
}

describe('useFamilyFavorites', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListFavorites.mockResolvedValue([]);
    mockAddFavorite.mockResolvedValue(favoriteEntry('fam-x'));
    mockRemoveFavorite.mockResolvedValue(undefined);
  });

  it('loads botanical-family favorites on mount', async () => {
    mockListFavorites.mockResolvedValue([favoriteEntry('fam-a'), favoriteEntry('fam-b')]);
    const { result } = renderHook(() => useFamilyFavorites());

    await waitFor(() => expect(result.current.isFavorite('fam-a')).toBe(true));
    expect(result.current.isFavorite('fam-b')).toBe(true);
    // Scoped to the family collection so species favorites don't leak in.
    expect(mockListFavorites).toHaveBeenCalledWith('botanical_families');
  });

  it('starts empty when the backend load fails (e.g. light mode)', async () => {
    mockListFavorites.mockRejectedValue(new Error('unauthenticated'));
    const { result } = renderHook(() => useFamilyFavorites());

    await waitFor(() => expect(mockListFavorites).toHaveBeenCalled());
    expect(result.current.favorites.size).toBe(0);
  });

  it('adds a favorite optimistically and calls the add endpoint', async () => {
    const { result } = renderHook(() => useFamilyFavorites());
    await waitFor(() => expect(mockListFavorites).toHaveBeenCalled());

    act(() => result.current.toggleFavorite('fam-x'));
    expect(result.current.isFavorite('fam-x')).toBe(true);
    await waitFor(() => expect(mockAddFavorite).toHaveBeenCalledWith('fam-x', 'manual'));
  });

  it('removes a favorite optimistically and calls the remove endpoint', async () => {
    mockListFavorites.mockResolvedValue([favoriteEntry('fam-x')]);
    const { result } = renderHook(() => useFamilyFavorites());
    await waitFor(() => expect(result.current.isFavorite('fam-x')).toBe(true));

    act(() => result.current.toggleFavorite('fam-x'));
    expect(result.current.isFavorite('fam-x')).toBe(false);
    await waitFor(() => expect(mockRemoveFavorite).toHaveBeenCalledWith('fam-x'));
  });

  it('reverts an added favorite when the add call rejects', async () => {
    mockAddFavorite.mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useFamilyFavorites());
    await waitFor(() => expect(mockListFavorites).toHaveBeenCalled());

    act(() => result.current.toggleFavorite('fam-x'));
    await waitFor(() => expect(result.current.isFavorite('fam-x')).toBe(false));
  });

  it('reverts a removed favorite when the remove call rejects', async () => {
    mockListFavorites.mockResolvedValue([favoriteEntry('fam-x')]);
    mockRemoveFavorite.mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useFamilyFavorites());
    await waitFor(() => expect(result.current.isFavorite('fam-x')).toBe(true));

    act(() => result.current.toggleFavorite('fam-x'));
    await waitFor(() => expect(result.current.isFavorite('fam-x')).toBe(true));
  });
});
