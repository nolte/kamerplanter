/**
 * The countdown keeps its state updaters pure and releases the audio context (#3022).
 */
import { act, renderHook } from '@testing-library/react';
import { StrictMode, createElement, type ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useCountdownTimer } from '@/hooks/useCountdownTimer';

const created: Array<{ close: ReturnType<typeof vi.fn>; oscillators: Array<{ onended: (() => void) | null }> }> = [];

class FakeAudioContext {
  currentTime = 0;
  destination = {};
  close = vi.fn(() => Promise.resolve());
  oscillators: Array<{ onended: (() => void) | null }> = [];

  constructor() {
    created.push(this);
  }

  createOscillator() {
    const osc = {
      frequency: { value: 0 },
      onended: null as (() => void) | null,
      connect: vi.fn(),
      start: vi.fn(),
      stop: vi.fn(),
    };
    this.oscillators.push(osc);
    return osc;
  }

  createGain() {
    return { gain: { value: 0 }, connect: vi.fn() };
  }
}

const strict = ({ children }: { children: ReactNode }) => createElement(StrictMode, null, children);

beforeEach(() => {
  vi.useFakeTimers();
  created.length = 0;
  vi.stubGlobal('AudioContext', FakeAudioContext);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('useCountdownTimer', () => {
  it('expires once and beeps once under StrictMode', () => {
    const { result } = renderHook(() => useCountdownTimer(2), { wrapper: strict });

    act(() => result.current.start());
    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(result.current.remaining).toBe(0);
    expect(result.current.expired).toBe(true);
    expect(result.current.running).toBe(false);
    expect(created).toHaveLength(1);
  });

  it('closes the audio context once the tone has ended', () => {
    const { result } = renderHook(() => useCountdownTimer(1));

    act(() => result.current.start());
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    act(() => created[0]?.oscillators[0]?.onended?.());

    expect(created[0]?.close).toHaveBeenCalledTimes(1);
  });

  it('closes a still-open audio context on unmount', () => {
    const { result, unmount } = renderHook(() => useCountdownTimer(1));

    act(() => result.current.start());
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    unmount();

    expect(created[0]?.close).toHaveBeenCalled();
  });
});
