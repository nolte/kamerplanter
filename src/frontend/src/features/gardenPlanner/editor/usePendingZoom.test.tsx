import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Viewport } from '../renderer';
import { stepZoom } from '../model/units';
import { usePendingZoom } from './usePendingZoom';
import { WHEEL_COMMIT_IDLE_MS } from './wheelZoom';

const VIEW: Viewport = { originM: [0, 20], pxPerM: 40, widthPx: 800, heightPx: 800 };

function setup(onZoom = vi.fn<(pxPerM: number, anchorPx: [number, number]) => void>()) {
  const layer = document.createElement('div');
  const canvas = document.createElement('div');
  document.body.append(canvas);
  const canvasRef = { current: canvas };
  const onPan = vi.fn<(dx: number, dy: number) => void>();
  const hook = renderHook(({ viewport }) =>
    usePendingZoom({ viewport, onZoom, onPan, minPxPerM: 1, canvasRef, canvasKey: 'plan' }),
  { initialProps: { viewport: VIEW } });
  act(() => hook.result.current.attachLayer(layer));
  return { ...hook, layer, canvas, onZoom, onPan };
}

afterEach(() => {
  vi.useRealTimers();
  document.body.innerHTML = '';
});

describe('usePendingZoom (GP-NFR-034)', () => {
  it('steps from a view committed but not drawn yet, so a second step does not lose the first', () => {
    // The route does not draw in between: onZoom is called, the viewport prop stays.
    const t = setup();
    act(() => t.result.current.zoomTo(80, [400, 400]));
    act(() => t.result.current.zoomTo(t.result.current.newestView().pxPerM * 2, [400, 400]));
    expect(t.onZoom.mock.calls.map(([pxPerM]) => pxPerM)).toEqual([80, 160]);
  });

  it('lets a button step from a pending wheel burst and commits once', () => {
    vi.useFakeTimers();
    const t = setup();
    act(() => t.result.current.zoomTo(60, [400, 400], true)); // a wheel notch: pending, nothing committed
    expect(t.onZoom).not.toHaveBeenCalled();
    const next = stepZoom(t.result.current.newestView().pxPerM, 1, 1);
    act(() => t.result.current.zoomTo(next, [400, 400])); // the "+" button
    expect(t.onZoom).toHaveBeenCalledTimes(1);
    expect(t.onZoom.mock.calls[0][0]).toBeCloseTo(next, 9);
    act(() => vi.advanceTimersByTime(WHEEL_COMMIT_IDLE_MS * 2));
    expect(t.onZoom).toHaveBeenCalledTimes(1); // the burst was part of that commit
  });

  it('clears the layer transform when the route draws the new view, and also when it draws none', () => {
    vi.useFakeTimers();
    const t = setup();
    act(() => t.result.current.zoomTo(80, [400, 400]));
    expect(t.layer.style.transform).toMatch(/scale\(2\)/);
    t.rerender({ viewport: { ...VIEW, pxPerM: 80, originM: [5, 15] } });
    expect(t.layer.style.transform).toBe('');
    act(() => t.result.current.zoomTo(160, [400, 400])); // refused by the route: no new viewport arrives
    expect(t.layer.style.transform).toMatch(/scale\(2\)/);
    act(() => vi.advanceTimersByTime(300));
    expect(t.layer.style.transform).toBe('');
  });

  it('commits a pending burst before a press, so the press works on the view on screen', () => {
    vi.useFakeTimers();
    const t = setup();
    act(() => t.result.current.zoomTo(60, [400, 400], true));
    expect(t.onZoom).not.toHaveBeenCalled();
    act(() => {
      t.canvas.dispatchEvent(new Event('pointerdown', { bubbles: true }));
    });
    expect(t.onZoom).toHaveBeenCalledTimes(1);
    expect(t.onZoom.mock.calls[0][0]).toBeCloseTo(60, 9);
  });
});
