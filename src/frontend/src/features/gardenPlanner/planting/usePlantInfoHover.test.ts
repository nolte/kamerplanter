import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { HOVER_DELAY_MS, LEAVE_GRACE_MS, usePlantInfoHover } from './usePlantInfoHover';

/** GP-UX-058 / WCAG 1.4.13: 300 ms dwell, hoverable, dismissible with Esc, none while drawing or on touch. */

let under: string | null = null;
const keyAt = () => under;
const mouse = { clientX: 10, clientY: 10, pointerType: 'mouse' };

function setup(suppressed = false) {
  return renderHook(({ off }) => usePlantInfoHover({ keyAt, suppressed: off }), { initialProps: { off: suppressed } });
}

beforeEach(() => {
  vi.useFakeTimers();
  under = null;
});
afterEach(() => vi.useRealTimers());

describe('usePlantInfoHover', () => {
  it('opens after 300 ms on a marker and not a moment sooner', () => {
    const { result } = setup();
    under = 'pl_1';
    act(() => result.current.onPointerMove(mouse));
    act(() => vi.advanceTimersByTime(HOVER_DELAY_MS - 1));
    expect(result.current.open).toBeNull();
    act(() => vi.advanceTimersByTime(1));
    expect(result.current.open).toEqual({ key: 'pl_1', source: 'hover' });
  });

  it('does not open when the pointer moves on before the dwell is over', () => {
    const { result } = setup();
    under = 'pl_1';
    act(() => result.current.onPointerMove(mouse));
    act(() => vi.advanceTimersByTime(200));
    under = null;
    act(() => result.current.onPointerMove(mouse));
    act(() => vi.advanceTimersByTime(1000));
    expect(result.current.open).toBeNull();
  });

  it('stays while the pointer is on the bubble and closes shortly after it leaves both', () => {
    const { result } = setup();
    under = 'pl_1';
    act(() => result.current.onPointerMove(mouse));
    act(() => vi.advanceTimersByTime(HOVER_DELAY_MS));
    under = null;
    act(() => result.current.onPointerMove(mouse)); // left the marker...
    act(() => result.current.onBubbleEnter()); // ...into the bubble
    act(() => vi.advanceTimersByTime(5000));
    expect(result.current.open).not.toBeNull();
    act(() => result.current.onBubbleLeave());
    act(() => vi.advanceTimersByTime(LEAVE_GRACE_MS));
    expect(result.current.open).toBeNull();
  });

  it('closes on Esc and does not reopen for the same marker until the pointer has left it', () => {
    const { result } = setup();
    under = 'pl_1';
    act(() => result.current.onPointerMove(mouse));
    act(() => vi.advanceTimersByTime(HOVER_DELAY_MS));
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    });
    expect(result.current.open).toBeNull();

    act(() => result.current.onPointerMove(mouse));
    act(() => vi.advanceTimersByTime(2000));
    expect(result.current.open).toBeNull();

    under = null;
    act(() => result.current.onPointerMove(mouse));
    under = 'pl_1';
    act(() => result.current.onPointerMove(mouse));
    act(() => vi.advanceTimersByTime(HOVER_DELAY_MS));
    expect(result.current.open?.key).toBe('pl_1');
  });

  it('never hovers on touch', () => {
    const { result } = setup();
    under = 'pl_1';
    act(() => result.current.onPointerMove({ ...mouse, pointerType: 'touch' }));
    act(() => vi.advanceTimersByTime(2000));
    expect(result.current.open).toBeNull();
  });

  it('shows nothing while suppressed (drawing, dragging, zooming) and closes an open bubble', () => {
    const { result, rerender } = setup();
    under = 'pl_1';
    act(() => result.current.onPointerMove(mouse));
    act(() => vi.advanceTimersByTime(HOVER_DELAY_MS));
    expect(result.current.open).not.toBeNull();
    rerender({ off: true });
    expect(result.current.open).toBeNull();
    act(() => result.current.onPointerMove(mouse));
    act(() => vi.advanceTimersByTime(2000));
    expect(result.current.open).toBeNull();
  });

  it('opens at once on keyboard focus and closes when focus leaves the canvas', () => {
    const { result } = setup();
    act(() => result.current.openByFocus('pl_2'));
    expect(result.current.open).toEqual({ key: 'pl_2', source: 'focus' });
    act(() => result.current.closeFocus());
    expect(result.current.open).toBeNull();
  });

  it('keeps a hover bubble when focus-leave fires (only a focus bubble goes away)', () => {
    const { result } = setup();
    under = 'pl_1';
    act(() => result.current.onPointerMove(mouse));
    act(() => vi.advanceTimersByTime(HOVER_DELAY_MS));
    act(() => result.current.closeFocus());
    expect(result.current.open?.source).toBe('hover');
  });

  it('moves to the next marker after its own dwell', () => {
    const { result } = setup();
    under = 'pl_1';
    act(() => result.current.onPointerMove(mouse));
    act(() => vi.advanceTimersByTime(HOVER_DELAY_MS));
    under = 'pl_2';
    act(() => result.current.onPointerMove(mouse));
    expect(result.current.open?.key).toBe('pl_1');
    act(() => vi.advanceTimersByTime(HOVER_DELAY_MS));
    expect(result.current.open?.key).toBe('pl_2');
  });
});
