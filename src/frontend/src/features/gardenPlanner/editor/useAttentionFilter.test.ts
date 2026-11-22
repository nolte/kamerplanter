import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useAttentionFilter } from './useAttentionFilter';

/** The filter "only plants that need attention" (GP-UX-061, #2488): a per-user choice in localStorage. */
const KEY = 'kp_garden_plan_attention_filter';

afterEach(() => {
  window.localStorage.clear();
  vi.restoreAllMocks();
});

describe('useAttentionFilter', () => {
  it('starts off without a stored choice', () => {
    const { result } = renderHook(() => useAttentionFilter());
    expect(result.current[0]).toBe(false);
  });

  it('stores the choice and restores it on the next visit', () => {
    const { result } = renderHook(() => useAttentionFilter());
    act(() => result.current[1](true));
    expect(result.current[0]).toBe(true);
    expect(window.localStorage.getItem(KEY)).toBe('true');
    expect(renderHook(() => useAttentionFilter()).result.current[0]).toBe(true);
    act(() => result.current[1](false));
    expect(window.localStorage.getItem(KEY)).toBe('false');
    expect(renderHook(() => useAttentionFilter()).result.current[0]).toBe(false);
  });

  it('reads anything but "true" as off', () => {
    window.localStorage.setItem(KEY, 'yes');
    expect(renderHook(() => useAttentionFilter()).result.current[0]).toBe(false);
  });

  it('keeps the choice for this visit when the storage is blocked', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    const { result } = renderHook(() => useAttentionFilter());
    expect(result.current[0]).toBe(false);
    act(() => result.current[1](true));
    expect(result.current[0]).toBe(true);
  });

  it('keeps the same tuple while nothing changes (useMemo)', () => {
    const { result, rerender } = renderHook(() => useAttentionFilter());
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });
});
