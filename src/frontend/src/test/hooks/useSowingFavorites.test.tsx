import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useSowingFavorites } from '@/hooks/useSowingFavorites';
import * as favoritesApi from '@/api/endpoints/favorites';

// Isolated module mock — no contact with the real HTTP client or handlers.ts.
vi.mock('@/api/endpoints/favorites');

const mockListFavorites = vi.mocked(favoritesApi.listFavorites);
const mockAddFavorite = vi.mocked(favoritesApi.addFavorite);
const mockRemoveFavorite = vi.mocked(favoritesApi.removeFavorite);

function favoriteEntry(targetKey: string) {
  return { target_key: targetKey } as Awaited<ReturnType<typeof favoritesApi.listFavorites>>[number];
}

describe('useSowingFavorites', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListFavorites.mockResolvedValue([]);
    mockAddFavorite.mockResolvedValue(favoriteEntry('x'));
    mockRemoveFavorite.mockResolvedValue(undefined);
  });

  it('loads favorites from the backend on mount', async () => {
    mockListFavorites.mockResolvedValue([favoriteEntry('a'), favoriteEntry('b')]);
    const { result } = renderHook(() => useSowingFavorites());

    await waitFor(() => expect(result.current.isFavorite('a')).toBe(true));
    expect(result.current.isFavorite('b')).toBe(true);
    expect(mockListFavorites).toHaveBeenCalledWith('species');
  });

  it('starts empty when the backend load fails', async () => {
    mockListFavorites.mockRejectedValue(new Error('unauthenticated'));
    const { result } = renderHook(() => useSowingFavorites());

    await waitFor(() => expect(mockListFavorites).toHaveBeenCalled());
    expect(result.current.favorites.size).toBe(0);
  });

  it('adds a favorite optimistically and calls the add endpoint', async () => {
    const { result } = renderHook(() => useSowingFavorites());
    await waitFor(() => expect(mockListFavorites).toHaveBeenCalled());

    act(() => result.current.toggleFavorite('x'));
    expect(result.current.isFavorite('x')).toBe(true);
    await waitFor(() => expect(mockAddFavorite).toHaveBeenCalledWith('x', 'manual'));
  });

  it('removes a favorite optimistically and calls the remove endpoint', async () => {
    mockListFavorites.mockResolvedValue([favoriteEntry('x')]);
    const { result } = renderHook(() => useSowingFavorites());
    await waitFor(() => expect(result.current.isFavorite('x')).toBe(true));

    act(() => result.current.toggleFavorite('x'));
    expect(result.current.isFavorite('x')).toBe(false);
    await waitFor(() => expect(mockRemoveFavorite).toHaveBeenCalledWith('x'));
  });

  it('reverts an added favorite when the add call rejects', async () => {
    mockAddFavorite.mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useSowingFavorites());
    await waitFor(() => expect(mockListFavorites).toHaveBeenCalled());

    act(() => result.current.toggleFavorite('x'));
    await waitFor(() => expect(result.current.isFavorite('x')).toBe(false));
  });

  it('reverts a removed favorite when the remove call rejects', async () => {
    mockListFavorites.mockResolvedValue([favoriteEntry('x')]);
    mockRemoveFavorite.mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useSowingFavorites());
    await waitFor(() => expect(result.current.isFavorite('x')).toBe(true));

    act(() => result.current.toggleFavorite('x'));
    await waitFor(() => expect(result.current.isFavorite('x')).toBe(true));
  });
});
