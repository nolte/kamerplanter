import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Viewport } from '../renderer';
import { stepZoom, zoomAround, type ZoomView } from '../model/units';
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

  it('drops a pending burst when the route draws a view of its own (fit, a focused bed)', () => {
    vi.useFakeTimers();
    const t = setup();
    act(() => t.result.current.zoomTo(60, [400, 400], true)); // a wheel burst, still pending
    expect(t.layer.style.transform).not.toBe('');
    const fitted: Viewport = { ...VIEW, pxPerM: 20, originM: [-5, 25] };
    t.rerender({ viewport: fitted }); // "fit" - not the hook's own commit
    expect(t.layer.style.transform).toBe('');
    expect(t.result.current.newestView()).toEqual(fitted);
    act(() => vi.advanceTimersByTime(WHEEL_COMMIT_IDLE_MS * 2));
    expect(t.onZoom).not.toHaveBeenCalled(); // the fit stays
    expect(t.onPan).not.toHaveBeenCalled();
  });

  it('commits a burst that returns to the drawn scale onto the view on screen, also over an undrawn commit', () => {
    vi.useFakeTimers();
    // The route as it is: onZoom zooms the drawn view (absolute), onPan adds to its newest state (functional).
    let state: ZoomView = VIEW;
    const onZoom = vi.fn((pxPerM: number, anchorPx: [number, number]) => {
      state = zoomAround(VIEW, pxPerM, anchorPx, 1);
    });
    const t = setup(onZoom);
    t.onPan.mockImplementation((dx, dy) => {
      state = { pxPerM: state.pxPerM, originM: [state.originM[0] - dx / state.pxPerM, state.originM[1] + dy / state.pxPerM] };
    });
    act(() => t.result.current.zoomTo(80, [100, 100])); // committed, not drawn yet
    act(() => t.result.current.zoomTo(40, [700, 300], true)); // a wheel burst back to the drawn scale
    const shown = t.result.current.newestView();
    act(() => vi.advanceTimersByTime(WHEEL_COMMIT_IDLE_MS * 2));
    expect(state.pxPerM).toBeCloseTo(shown.pxPerM, 9);
    expect(state.originM[0]).toBeCloseTo(shown.originM[0], 9);
    expect(state.originM[1]).toBeCloseTo(shown.originM[1], 9);
  });
});
