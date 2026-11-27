/**
 * The canvas height on a phone with the bottom navigation (#3018, GP-UX-067, TC-053-104). jsdom lays nothing out,
 * so the geometry the nightly measured at 390 x 844 is stubbed on the elements themselves: the canvas area starts
 * 262 px down, the docked bars (TouchBar and tool bar) are 130 px high, and the probe that resolves
 * `--kp-bottom-nav-offset` gets the bar's 56 px. The sticky bars then rest at 844 - 56 - 130 = 658 px; the row gap
 * between canvas and bars is 8 px.
 */
import { renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { availableCanvasHeight, MIN_CANVAS_HEIGHT_PX, useCanvasArea } from './useCanvasArea';

const VIEWPORT = { width: 390, height: 844 };
const AREA_TOP = 262;
const BARS_PX = 130;
const NAV_PX = 56;
const ROW_GAP_PX = 8;

function box(top: number, width: number, height: number): DOMRect {
  return {
    top, bottom: top + height, left: 16, right: 16 + width, width, height, x: 16, y: top, toJSON: () => ({}),
  } as DOMRect;
}

const restores: Array<() => void> = [];

afterEach(() => {
  while (restores.length) restores.pop()?.();
});

function stubWindowHeight(px: number): void {
  const original = Object.getOwnPropertyDescriptor(window, 'innerHeight');
  Object.defineProperty(window, 'innerHeight', { configurable: true, value: px });
  restores.push(() => {
    if (original) Object.defineProperty(window, 'innerHeight', original);
  });
}

/** The probe `bottomNavOffsetPx()` appends measures the bar while it is mounted, 0 otherwise. */
function stubBottomNav(px: number): void {
  const rect = Element.prototype.getBoundingClientRect;
  Element.prototype.getBoundingClientRect = function getBoundingClientRect(this: Element) {
    if (this instanceof HTMLElement && this.style.height.includes('--kp-bottom-nav-offset')) return box(0, 0, px);
    return rect.call(this);
  };
  restores.push(() => {
    Element.prototype.getBoundingClientRect = rect;
  });
}

function measure(withBars: boolean) {
  const area = document.createElement('div');
  vi.spyOn(area, 'getBoundingClientRect').mockReturnValue(box(AREA_TOP, VIEWPORT.width - 47, 400));
  Object.defineProperty(area, 'clientWidth', { configurable: true, get: () => VIEWPORT.width - 47 });
  const bars = document.createElement('div');
  vi.spyOn(bars, 'getBoundingClientRect').mockReturnValue(box(0, VIEWPORT.width - 47, BARS_PX));
  const areaRef = { current: area };
  const barsRef = { current: withBars ? bars : null };
  return renderHook(() => useCanvasArea(areaRef, barsRef)).result.current;
}

describe('useCanvasArea on a phone with the bottom navigation (#3018)', () => {
  it('ends the canvas above the docked bars at 390 x 844 (TC-053-104)', () => {
    stubWindowHeight(VIEWPORT.height);
    stubBottomNav(NAV_PX);
    const size = measure(true);
    expect(size).not.toBeNull();
    const barsTop = VIEWPORT.height - NAV_PX - BARS_PX;
    // The bars sit below the canvas and its row gap, so they cover nothing of the plan.
    expect(AREA_TOP + size!.heightPx + ROW_GAP_PX).toBeLessThanOrEqual(barsTop);
    expect(size!.heightPx).toBe(barsTop - ROW_GAP_PX - AREA_TOP);
  });

  it('takes the bar from the floor only where the bar is there', () => {
    // Desktop and tablet: no docked bars, no bottom navigation - the 400 px floor of GP-UX-067 is whole.
    expect(availableCanvasHeight(600, 400, 0)).toBe(MIN_CANVAS_HEIGHT_PX);
    // A phone too short for even the lowered floor keeps it and scrolls, as before the bar came.
    expect(availableCanvasHeight(667, AREA_TOP, BARS_PX, NAV_PX)).toBe(MIN_CANVAS_HEIGHT_PX - NAV_PX);
  });

  it('keeps the bars below the canvas at every phone height where they were before the bar came', () => {
    // Before #3018 the canvas cleared the bars from 262 + 400 + 8 + 130 = 800 px up. The 56 px bar must not move
    // that threshold: a whole 400 px floor would have moved it to 856 px, past the 844 px of TC-053-104.
    for (const height of [800, 844, 852, 932]) {
      const canvas = availableCanvasHeight(height, AREA_TOP, BARS_PX, NAV_PX);
      expect(AREA_TOP + canvas + ROW_GAP_PX).toBeLessThanOrEqual(height - NAV_PX - BARS_PX);
    }
  });
});
