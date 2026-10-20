import { describe, expect, it } from 'vitest';
import type { Viewport } from '../renderer';
import {
  fromMiniMap,
  MINI_MAP_PX,
  miniMapScale,
  miniMapVisible,
  panToCentre,
  toMiniMap,
  viewportBox,
} from './miniMap';

// 40 px per metre, 800 x 400 px: the viewport shows 20 x 10 m = 200 m2
const VIEW: Viewport = { originM: [5, 15], pxPerM: 40, widthPx: 800, heightPx: 400 };

describe('mini-map visibility (GP-UX-014, §9.6)', () => {
  it('shows the part of the plan the viewport covers', () => {
    expect(viewportBox(VIEW)).toEqual([5, 5, 25, 15]);
  });

  it('is hidden while the site fits the viewport or is up to four viewports large', () => {
    expect(miniMapVisible([0, 0, 20, 10], VIEW)).toBe(false);
    expect(miniMapVisible([0, 0, 40, 20], VIEW)).toBe(false); // exactly 4 x 200 m2
  });

  it('shows when the site exceeds four times the viewport', () => {
    expect(miniMapVisible([0, 0, 40.5, 20], VIEW)).toBe(true);
    expect(miniMapVisible([0, 0, 100, 100], VIEW)).toBe(true);
  });

  it('is hidden without content or a usable viewport', () => {
    expect(miniMapVisible(null, VIEW)).toBe(false);
    expect(miniMapVisible([0, 0, 100, 100], { ...VIEW, pxPerM: 0 })).toBe(false);
  });
});

describe('mini-map geometry', () => {
  const extent: [number, number, number, number] = [0, 0, 100, 50];

  it('fits the longer side into 120 px and centres the shorter one', () => {
    const fit = miniMapScale(extent);
    expect(fit.scale).toBeCloseTo(MINI_MAP_PX / 100);
    expect(fit.offsetPx[0]).toBeCloseTo(0);
    expect(fit.offsetPx[1]).toBeCloseTo(30);
  });

  it('maps a point there and back, with y flipped', () => {
    const fit = miniMapScale(extent);
    const pixel = toMiniMap([100, 50], extent, fit);
    expect(pixel[0]).toBeCloseTo(120);
    expect(pixel[1]).toBeCloseTo(30);
    const back = fromMiniMap(toMiniMap([25, 10], extent, fit), extent, fit);
    expect(back[0]).toBeCloseTo(25);
    expect(back[1]).toBeCloseTo(10);
  });

  it('clamps a click outside the plan to its edge', () => {
    const fit = miniMapScale(extent);
    expect(fromMiniMap([-50, 500], extent, fit)).toEqual([0, 0]);
  });
});

describe('panToCentre', () => {
  it('pans so the clicked point becomes the middle of the view', () => {
    // the view's middle is (15, 10); the target is 10 m right and 5 m up of it
    const [dx, dy] = panToCentre(VIEW, [25, 15]);
    expect(dx).toBeCloseTo(-400);
    expect(dy).toBeCloseTo(200);
    // applying the pan like the route does: origin - dx/px, origin + dy/px
    const moved = { ...VIEW, originM: [VIEW.originM[0] - dx / 40, VIEW.originM[1] + dy / 40] as [number, number] };
    const box = viewportBox(moved);
    expect([(box[0] + box[2]) / 2, (box[1] + box[3]) / 2]).toEqual([25, 15]);
  });
});
