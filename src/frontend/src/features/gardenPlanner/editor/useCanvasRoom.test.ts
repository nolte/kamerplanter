/**
 * The measured room of the canvas (#3034): the canvas row less the tool rail and its gap, measured on the page. jsdom
 * lays nothing out, so the row's `clientWidth` and the rail's box are stubbed on the two elements themselves (no
 * prototype is touched).
 */
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PANEL_GAP_PX } from './layout';
import { useCanvasRoom } from './useCanvasRoom';

interface Laid {
  row: HTMLDivElement;
  rail: HTMLDivElement;
  /** Lays the row out `px` wide (0: hidden, nothing laid out). */
  setRow: (px: number) => void;
}

function layout(rowPx: number, railPx: number): Laid {
  let rowWidth = rowPx;
  const row = document.createElement('div');
  const rail = document.createElement('div');
  Object.defineProperty(row, 'clientWidth', { configurable: true, get: () => rowWidth });
  vi.spyOn(rail, 'getBoundingClientRect').mockReturnValue({
    top: 0, bottom: 600, left: 0, right: railPx, width: railPx, height: 600, x: 0, y: 0, toJSON: () => ({}),
  });
  return {
    row,
    rail,
    setRow: (px: number) => {
      rowWidth = px;
    },
  };
}

function measureOf(laid: Laid, railShown: boolean) {
  let renders = 0;
  // Stable refs, as the editor's `useRef`s are.
  const rowRef = { current: laid.row };
  const railRef = { current: laid.rail };
  const hook = renderHook(
    ({ shown }: { shown: boolean }) => {
      renders += 1;
      return useCanvasRoom(rowRef, railRef, shown);
    },
    { initialProps: { shown: railShown } },
  );
  return { hook, renders: () => renders };
}

const resize = () =>
  act(() => {
    window.dispatchEvent(new Event('resize'));
  });

describe('useCanvasRoom (#3034)', () => {
  it('is the row less the rail and its gap while the rail is shown', () => {
    // 820 px window: the row is 548 px, the rail 112 px.
    const { hook } = measureOf(layout(548, 112), true);
    expect(hook.result.current).toBe(548 - 112 - PANEL_GAP_PX);
  });

  it('is the whole row without the rail (the list view), and follows the rail appearing again', () => {
    const { hook } = measureOf(layout(548, 112), false);
    expect(hook.result.current).toBe(548);
    hook.rerender({ shown: true });
    expect(hook.result.current).toBe(548 - 112 - PANEL_GAP_PX);
    hook.rerender({ shown: false });
    expect(hook.result.current).toBe(548);
  });

  it('measures again when the window resizes', () => {
    const laid = layout(1094, 112);
    const { hook } = measureOf(laid, true);
    expect(hook.result.current).toBe(1094 - 112 - PANEL_GAP_PX);
    laid.setRow(548);
    resize();
    expect(hook.result.current).toBe(548 - 112 - PANEL_GAP_PX);
  });

  it('keeps the last width while nothing is laid out (width 0, a hidden tab), and null before the first', () => {
    const laid = layout(0, 112);
    const { hook } = measureOf(laid, true);
    expect(hook.result.current).toBeNull();
    laid.setRow(548);
    resize();
    expect(hook.result.current).toBe(548 - 112 - PANEL_GAP_PX);
    laid.setRow(0);
    resize();
    expect(hook.result.current).toBe(548 - 112 - PANEL_GAP_PX);
  });

  it('renders nothing again for a resize that leaves the width as it was', () => {
    const laid = layout(1094, 112);
    const { hook, renders } = measureOf(laid, true);
    const before = renders();
    resize();
    resize();
    expect(renders()).toBe(before);
    expect(hook.result.current).toBe(1094 - 112 - PANEL_GAP_PX);
  });
});
