import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useAbortableLoad } from '@/hooks/useAbortableLoad';

describe('useAbortableLoad (#3014)', () => {
  it('supersedes the previous run when a new one begins', () => {
    const { result } = renderHook(() => useAbortableLoad());
    const first = result.current();
    const second = result.current();

    expect(first.isCurrent()).toBe(false);
    expect(first.signal.aborted).toBe(true);
    expect(second.isCurrent()).toBe(true);
    expect(second.signal.aborted).toBe(false);
  });

  it('ends the running load on unmount', () => {
    const { result, unmount } = renderHook(() => useAbortableLoad());
    const ticket = result.current();
    unmount();

    expect(ticket.isCurrent()).toBe(false);
    expect(ticket.signal.aborted).toBe(true);
  });

  it('returns the same begin function across renders', () => {
    const { result, rerender } = renderHook(() => useAbortableLoad());
    const begin = result.current;
    rerender();
    expect(result.current).toBe(begin);
  });
});
