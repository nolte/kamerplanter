import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useAsyncOptions } from '@/hooks/useAsyncOptions';

describe('useAsyncOptions', () => {
  it('fills options and keeps error false on success', async () => {
    const loader = vi.fn().mockResolvedValue(['a', 'b']);
    const { result } = renderHook(() => useAsyncOptions(loader));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.options).toEqual(['a', 'b']);
    expect(result.current.error).toBe(false);
    expect(loader).toHaveBeenCalledTimes(1);
  });

  it('sets error and keeps an empty option list on rejection', async () => {
    const loader = vi.fn().mockRejectedValue(new Error('boom'));
    const { result } = renderHook(() => useAsyncOptions(loader));

    await waitFor(() => expect(result.current.error).toBe(true));
    expect(result.current.options).toEqual([]);
    expect(result.current.loading).toBe(false);
  });

  it('does not call the loader when disabled', async () => {
    const loader = vi.fn().mockResolvedValue([1]);
    const { result } = renderHook(() => useAsyncOptions(loader, { enabled: false }));

    // Give any (erroneous) effect a chance to run.
    await Promise.resolve();
    expect(loader).not.toHaveBeenCalled();
    expect(result.current.options).toEqual([]);
  });

  it('re-runs the loader when reload() is called', async () => {
    const loader = vi.fn().mockResolvedValue([1]);
    const { result } = renderHook(() => useAsyncOptions(loader));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(loader).toHaveBeenCalledTimes(1);

    act(() => result.current.reload());
    await waitFor(() => expect(loader).toHaveBeenCalledTimes(2));
  });

  it('returns a referentially stable object across rerenders without state change', async () => {
    const loader = vi.fn().mockResolvedValue(['a']);
    const { result, rerender } = renderHook(() => useAsyncOptions(loader));

    await waitFor(() => expect(result.current.loading).toBe(false));
    const first = result.current;
    rerender();
    // FRONTEND.md §6.1: object return MUST be useMemo-stabilised.
    expect(result.current).toBe(first);
  });

  it('does not update state after unmount while a load is pending', async () => {
    let resolveLoader: (v: string[]) => void = () => {};
    const loader = vi.fn(
      () =>
        new Promise<string[]>((resolve) => {
          resolveLoader = resolve;
        }),
    );
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { unmount } = renderHook(() => useAsyncOptions(loader));

    unmount();
    // Resolve after unmount — the cancelled guard must prevent a state update.
    await act(async () => {
      resolveLoader(['late']);
      await Promise.resolve();
    });

    expect(errorSpy).not.toHaveBeenCalledWith(
      expect.stringContaining('unmounted'),
    );
    errorSpy.mockRestore();
  });
});
