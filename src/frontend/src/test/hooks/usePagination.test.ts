import { renderHook, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { usePagination } from '@/hooks/usePagination';

describe('usePagination', () => {
  it('initializes with default values', () => {
    const { result } = renderHook(() => usePagination());
    expect(result.current.page).toBe(0);
    expect(result.current.rowsPerPage).toBe(50);
    expect(result.current.offset).toBe(0);
  });

  it('accepts custom initial rowsPerPage', () => {
    const { result } = renderHook(() => usePagination(25));
    expect(result.current.rowsPerPage).toBe(25);
  });

  it('setPage updates page and offset', () => {
    const { result } = renderHook(() => usePagination(10));
    act(() => result.current.setPage(2));
    expect(result.current.page).toBe(2);
    expect(result.current.offset).toBe(20);
  });

  it('setRowsPerPage resets to page 0', () => {
    const { result } = renderHook(() => usePagination(50));
    act(() => result.current.setPage(3));
    expect(result.current.page).toBe(3);
    act(() => result.current.setRowsPerPage(25));
    expect(result.current.page).toBe(0);
    expect(result.current.rowsPerPage).toBe(25);
    expect(result.current.offset).toBe(0);
  });

  it('calculates offset correctly', () => {
    const { result } = renderHook(() => usePagination(10));
    act(() => result.current.setPage(5));
    expect(result.current.offset).toBe(50);
  });
});
