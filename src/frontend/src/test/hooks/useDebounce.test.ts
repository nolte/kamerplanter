import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useDebounce } from '@/hooks/useDebounce';

describe('useDebounce', () => {
  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('hello', 300));
    expect(result.current).toBe('hello');
  });

  it('updates value after delay', () => {
    vi.useFakeTimers();
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'a', delay: 300 } },
    );

    expect(result.current).toBe('a');

    rerender({ value: 'b', delay: 300 });
    expect(result.current).toBe('a'); // not yet updated

    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(result.current).toBe('b');

    vi.useRealTimers();
  });

  it('cancels previous timer on rapid changes', () => {
    vi.useFakeTimers();
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'a' } },
    );

    rerender({ value: 'b' });
    act(() => {
      vi.advanceTimersByTime(100);
    });
    rerender({ value: 'c' });
    act(() => {
      vi.advanceTimersByTime(100);
    });
    // 'b' timer was cancelled, 'c' timer still pending
    expect(result.current).toBe('a');

    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current).toBe('c');

    vi.useRealTimers();
  });

  it('cleans up on unmount', () => {
    vi.useFakeTimers();
    const { result, rerender, unmount } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'a' } },
    );

    rerender({ value: 'b' });
    unmount();

    // Advancing timers after unmount should not cause errors
    act(() => {
      vi.advanceTimersByTime(300);
    });
    // value is still 'a' because the hook was unmounted
    expect(result.current).toBe('a');

    vi.useRealTimers();
  });
});
