import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useLocalFavorites } from '@/hooks/useLocalFavorites';

const storageMap = new Map<string, string>();
const mockLocalStorage = {
  getItem: vi.fn((key: string) => storageMap.get(key) ?? null),
  setItem: vi.fn((key: string, value: string) => storageMap.set(key, value)),
  removeItem: vi.fn((key: string) => storageMap.delete(key)),
  clear: vi.fn(() => storageMap.clear()),
  get length() { return storageMap.size; },
  key: vi.fn(() => null),
};

Object.defineProperty(globalThis, 'localStorage', { value: mockLocalStorage, writable: true });

const KEY = 'kamerplanter-test-favorites';

describe('useLocalFavorites', () => {
  beforeEach(() => {
    storageMap.clear();
    vi.clearAllMocks();
  });

  it('starts empty when nothing is stored', () => {
    const { result } = renderHook(() => useLocalFavorites(KEY));
    expect(result.current.favorites.size).toBe(0);
    expect(result.current.hasFavorites).toBe(false);
  });

  it('hydrates from a previously stored list', () => {
    storageMap.set(KEY, JSON.stringify(['a', 'b']));
    const { result } = renderHook(() => useLocalFavorites(KEY));
    expect(result.current.isFavorite('a')).toBe(true);
    expect(result.current.isFavorite('b')).toBe(true);
    expect(result.current.hasFavorites).toBe(true);
  });

  it('falls back to an empty set when stored JSON is corrupt', () => {
    storageMap.set(KEY, '{not json');
    const { result } = renderHook(() => useLocalFavorites(KEY));
    expect(result.current.favorites.size).toBe(0);
  });

  it('adds a favorite and persists it', () => {
    const { result } = renderHook(() => useLocalFavorites(KEY));
    act(() => result.current.toggleFavorite('x'));
    expect(result.current.isFavorite('x')).toBe(true);
    expect(result.current.hasFavorites).toBe(true);
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(KEY, JSON.stringify(['x']));
  });

  it('removes a favorite that was already set', () => {
    storageMap.set(KEY, JSON.stringify(['x']));
    const { result } = renderHook(() => useLocalFavorites(KEY));
    act(() => result.current.toggleFavorite('x'));
    expect(result.current.isFavorite('x')).toBe(false);
    expect(result.current.hasFavorites).toBe(false);
  });

  it('reports non-members as not favorite', () => {
    const { result } = renderHook(() => useLocalFavorites(KEY));
    expect(result.current.isFavorite('missing')).toBe(false);
  });
});
