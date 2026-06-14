import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createElement, type ReactNode } from 'react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { useTableLocalState, useTableUrlState, type TableStateConfig } from '@/hooks/useTableState';

// Mock localStorage for environments where it may not be available
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

describe('useTableLocalState', () => {
  beforeEach(() => {
    storageMap.clear();
    vi.clearAllMocks();
  });

  it('returns default values', () => {
    const { result } = renderHook(() => useTableLocalState());
    expect(result.current.search).toBe('');
    expect(result.current.sort).toBeNull();
    expect(result.current.page).toBe(0);
    expect(result.current.pageSize).toBe(25);
  });

  it('uses defaultSort', () => {
    const { result } = renderHook(() =>
      useTableLocalState({ defaultSort: { column: 'name', direction: 'asc' } }),
    );
    expect(result.current.sort).toEqual({ column: 'name', direction: 'asc' });
  });

  it('toggles sort asc → desc → null', () => {
    const { result } = renderHook(() => useTableLocalState());

    act(() => result.current.setSort('name'));
    expect(result.current.sort).toEqual({ column: 'name', direction: 'asc' });

    act(() => result.current.setSort('name'));
    expect(result.current.sort).toEqual({ column: 'name', direction: 'desc' });

    act(() => result.current.setSort('name'));
    expect(result.current.sort).toBeNull();
  });

  it('resets page when setting search', () => {
    const { result } = renderHook(() => useTableLocalState());

    act(() => result.current.setPage(3));
    expect(result.current.page).toBe(3);

    act(() => result.current.setSearch('test'));
    expect(result.current.search).toBe('test');
    expect(result.current.page).toBe(0);
  });

  it('resets page when setting sort', () => {
    const { result } = renderHook(() => useTableLocalState());

    act(() => result.current.setPage(5));
    expect(result.current.page).toBe(5);

    act(() => result.current.setSort('name'));
    expect(result.current.page).toBe(0);
  });

  it('persists pageSize to localStorage', () => {
    const { result } = renderHook(() =>
      useTableLocalState({ pageSizeStorageKey: 'test-pagesize' }),
    );

    act(() => result.current.setPageSize(50));
    expect(result.current.pageSize).toBe(50);
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('test-pagesize', '50');
  });

  it('reads pageSize from localStorage on init', () => {
    storageMap.set('test-pagesize', '100');
    const { result } = renderHook(() =>
      useTableLocalState({ pageSizeStorageKey: 'test-pagesize' }),
    );
    expect(result.current.pageSize).toBe(100);
  });

  it('resetAll restores defaults', () => {
    const { result } = renderHook(() =>
      useTableLocalState({ defaultSort: { column: 'id', direction: 'asc' } }),
    );

    act(() => {
      result.current.setSearch('test');
      result.current.setSort('name');
      result.current.setPage(3);
    });

    act(() => result.current.resetAll());
    expect(result.current.search).toBe('');
    expect(result.current.sort).toEqual({ column: 'id', direction: 'asc' });
    expect(result.current.page).toBe(0);
  });

  it('switching sort column starts at asc', () => {
    const { result } = renderHook(() => useTableLocalState());

    act(() => result.current.setSort('name'));
    act(() => result.current.setSort('name')); // now desc
    expect(result.current.sort).toEqual({ column: 'name', direction: 'desc' });

    act(() => result.current.setSort('date')); // different column
    expect(result.current.sort).toEqual({ column: 'date', direction: 'asc' });
  });

  it('uses custom defaultPageSize', () => {
    const { result } = renderHook(() =>
      useTableLocalState({ defaultPageSize: 10 }),
    );
    expect(result.current.pageSize).toBe(10);
  });

  it('handles missing localStorage gracefully', () => {
    mockLocalStorage.getItem.mockImplementationOnce(() => {
      throw new Error('storage disabled');
    });

    const { result } = renderHook(() =>
      useTableLocalState({ pageSizeStorageKey: 'test', defaultPageSize: 15 }),
    );
    expect(result.current.pageSize).toBe(15);
  });

  it('swallows a localStorage write failure when persisting pageSize', () => {
    mockLocalStorage.setItem.mockImplementationOnce(() => {
      throw new Error('quota exceeded');
    });
    const { result } = renderHook(() =>
      useTableLocalState({ pageSizeStorageKey: 'test-pagesize' }),
    );
    act(() => result.current.setPageSize(50));
    expect(result.current.pageSize).toBe(50);
  });

  it('ignores a non-positive stored pageSize and uses the fallback', () => {
    storageMap.set('test-pagesize', '0');
    const { result } = renderHook(() =>
      useTableLocalState({ pageSizeStorageKey: 'test-pagesize', defaultPageSize: 25 }),
    );
    expect(result.current.pageSize).toBe(25);
  });
});

/** Render a hook inside a memory data router so useSearchParams works. */
function renderUrlState(config: TableStateConfig, initialUrl = '/') {
  function wrapper({ children }: { children: ReactNode }) {
    const router = createMemoryRouter([{ path: '*', element: children }], {
      initialEntries: [initialUrl],
    });
    return createElement(RouterProvider, { router });
  }
  return renderHook(() => useTableUrlState(config), { wrapper });
}

describe('useTableUrlState', () => {
  beforeEach(() => {
    storageMap.clear();
    vi.clearAllMocks();
  });

  it('returns defaults when no query params are present', () => {
    const { result } = renderUrlState({});
    expect(result.current.search).toBe('');
    expect(result.current.sort).toBeNull();
    expect(result.current.page).toBe(0);
    expect(result.current.pageSize).toBe(25);
  });

  it('reads search, sort, page and pageSize from the URL', () => {
    const { result } = renderUrlState(
      {},
      '/?q=rose&sort=name&dir=desc&page=3&pageSize=50',
    );
    expect(result.current.search).toBe('rose');
    expect(result.current.sort).toEqual({ column: 'name', direction: 'desc' });
    expect(result.current.page).toBe(2); // 1-based in URL → 0-based in state
    expect(result.current.pageSize).toBe(50);
  });

  it('falls back to defaultSort when the URL sort params are incomplete', () => {
    const { result } = renderUrlState(
      { defaultSort: { column: 'id', direction: 'asc' } },
      '/?sort=name',
    );
    expect(result.current.sort).toEqual({ column: 'id', direction: 'asc' });
  });

  it('writes the search term into the URL and clears the page', () => {
    const { result } = renderUrlState({}, '/?page=4');
    act(() => result.current.setSearch('tomato'));
    expect(result.current.search).toBe('tomato');
    expect(result.current.page).toBe(0);
  });

  it('removes the q param when search is cleared', () => {
    const { result } = renderUrlState({}, '/?q=tomato');
    act(() => result.current.setSearch(''));
    expect(result.current.search).toBe('');
  });

  it('cycles sort asc → desc → cleared without a default sort', () => {
    const { result } = renderUrlState({});
    act(() => result.current.setSort('name'));
    expect(result.current.sort).toEqual({ column: 'name', direction: 'asc' });
    act(() => result.current.setSort('name'));
    expect(result.current.sort).toEqual({ column: 'name', direction: 'desc' });
    act(() => result.current.setSort('name'));
    expect(result.current.sort).toBeNull();
  });

  it('falls back to the default sort instead of clearing when one is configured', () => {
    const { result } = renderUrlState({ defaultSort: { column: 'id', direction: 'asc' } });
    act(() => result.current.setSort('name'));
    act(() => result.current.setSort('name')); // now desc
    act(() => result.current.setSort('name')); // back to default
    expect(result.current.sort).toEqual({ column: 'id', direction: 'asc' });
  });

  it('switching to a different sort column starts at asc', () => {
    const { result } = renderUrlState({}, '/?sort=name&dir=desc');
    act(() => result.current.setSort('date'));
    expect(result.current.sort).toEqual({ column: 'date', direction: 'asc' });
  });

  it('sets and clears the page param', () => {
    const { result } = renderUrlState({});
    act(() => result.current.setPage(2));
    expect(result.current.page).toBe(2);
    act(() => result.current.setPage(0));
    expect(result.current.page).toBe(0);
  });

  it('persists pageSize to localStorage and the URL', () => {
    const { result } = renderUrlState({ pageSizeStorageKey: 'url-pagesize' });
    act(() => result.current.setPageSize(100));
    expect(result.current.pageSize).toBe(100);
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('url-pagesize', '100');
  });

  it('resetAll clears every query param', () => {
    const { result } = renderUrlState({}, '/?q=rose&sort=name&dir=asc&page=2');
    act(() => result.current.resetAll());
    expect(result.current.search).toBe('');
    expect(result.current.sort).toBeNull();
    expect(result.current.page).toBe(0);
  });
});
