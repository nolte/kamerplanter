import { act, renderHook } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useKioskTimeout } from '@/kiosk/useKioskTimeout';

describe('useKioskTimeout', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('shows the warning after the idle period (R-033)', () => {
    const onReset = vi.fn();
    const { result } = renderHook(() =>
      useKioskTimeout({ enabled: true, idleMs: 1000, warningMs: 500, onReset }),
    );

    expect(result.current.showWarning).toBe(false);
    act(() => void vi.advanceTimersByTime(1000));
    expect(result.current.showWarning).toBe(true);
  });

  it('auto-resets to the start page after the warning grace period (R-035)', () => {
    const onReset = vi.fn();
    const { result } = renderHook(() =>
      useKioskTimeout({ enabled: true, idleMs: 1000, warningMs: 3000, onReset }),
    );

    act(() => void vi.advanceTimersByTime(1000));
    expect(result.current.showWarning).toBe(true);
    expect(result.current.remainingSeconds).toBe(3);

    act(() => void vi.advanceTimersByTime(3000));
    expect(onReset).toHaveBeenCalledTimes(1);
    expect(result.current.showWarning).toBe(false);
  });

  it('resets the idle timer on touch interaction (R-036)', () => {
    const onReset = vi.fn();
    const { result } = renderHook(() =>
      useKioskTimeout({ enabled: true, idleMs: 1000, warningMs: 500, onReset }),
    );

    act(() => void vi.advanceTimersByTime(800));
    act(() => window.dispatchEvent(new Event('pointerdown')));
    // Without the reset the warning would have fired at 1000ms.
    act(() => void vi.advanceTimersByTime(400));
    expect(result.current.showWarning).toBe(false);

    act(() => void vi.advanceTimersByTime(600));
    expect(result.current.showWarning).toBe(true);
  });

  it('dismissWarning hides the overlay and restarts the idle timer (R-034)', () => {
    const onReset = vi.fn();
    const { result } = renderHook(() =>
      useKioskTimeout({ enabled: true, idleMs: 1000, warningMs: 500, onReset }),
    );

    act(() => void vi.advanceTimersByTime(1000));
    expect(result.current.showWarning).toBe(true);

    act(() => result.current.dismissWarning());
    expect(result.current.showWarning).toBe(false);
    expect(onReset).not.toHaveBeenCalled();
  });

  it('does nothing while disabled', () => {
    const onReset = vi.fn();
    const { result } = renderHook(() =>
      useKioskTimeout({ enabled: false, idleMs: 1000, warningMs: 500, onReset }),
    );

    act(() => void vi.advanceTimersByTime(5000));
    expect(result.current.showWarning).toBe(false);
    expect(onReset).not.toHaveBeenCalled();
  });
});
