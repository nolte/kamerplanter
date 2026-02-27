import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useTableLocalState } from '@/hooks/useTableState';

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
});
