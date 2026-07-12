import { describe, it, expect } from 'vitest';
import {
  EDIT_GRID_MARGIN,
  EDIT_GRID_ROW_HEIGHT,
  RESIZE_HANDLE_MARGIN_TOP,
  RESIZE_HANDLE_SIZE,
  WIDGET_KEBAB_INSET,
  WIDGET_KEBAB_SIZE,
  eastResizeHandleOverlapsKebab,
  eastResizeHandleVerticalBand,
  tilePixelHeight,
  widgetKebabVerticalBand,
} from '@/lib/dashboardEditGridGeometry';

/**
 * DASH-1 (#487) — in edit mode the enlarged east resize handle and the ⋮ kebab
 * button both sit at a tile's right edge. On a minimum-height (h=2) tile they
 * must NOT overlap, or a corner tap starts a width-resize instead of opening the
 * menu. jsdom cannot lay elements out (getBoundingClientRect is all zeros), so
 * this asserts the CSS *constraints* both components derive from the shared
 * geometry module — the strongest guarantee a unit test can give. A real
 * pointer-event / live touch test on an h=2 tile is still required to prove
 * pointer-event routing (a unit test cannot exercise hit-testing).
 */
describe('dashboardEditGridGeometry — resize handle vs. kebab separation (#487)', () => {
  it('models an h=2 tile as 104px (2*44 + 1*16), the issue geometry', () => {
    expect(tilePixelHeight(2)).toBe(104);
    // Sanity on the constants the two components share.
    expect(EDIT_GRID_ROW_HEIGHT).toBe(44);
    expect(EDIT_GRID_MARGIN).toBe(16);
    expect(RESIZE_HANDLE_SIZE).toBe(48);
    expect(WIDGET_KEBAB_SIZE).toBe(48);
    expect(WIDGET_KEBAB_INSET).toBe(4);
  });

  it('places the kebab band at 4…52px (48px target from the 4px inset, R-011)', () => {
    expect(widgetKebabVerticalBand()).toEqual({ top: 4, bottom: 52 });
  });

  it('re-centres the enlarged east handle on the tile middle (margin-top 0)', () => {
    // The fix: margin-top reset from react-resizable's 20px-calibrated -10px to 0.
    expect(RESIZE_HANDLE_MARGIN_TOP).toBe(0);
    // On an h=2 tile (104px) the corrected handle's top edge sits at H/2 = 52px,
    // exactly level with the kebab's 52px bottom edge — 48px tall, ending at
    // 100px, still inside the 104px tile.
    const band = eastResizeHandleVerticalBand(tilePixelHeight(2));
    expect(band).toEqual({ top: 52, bottom: 100 });
    expect(band.bottom).toBeLessThanOrEqual(tilePixelHeight(2));
    expect(band.bottom - band.top).toBe(RESIZE_HANDLE_SIZE); // ≥48px, U-006 kept
  });

  it('does NOT overlap the kebab on a minimum-height (h=2) tile — the fix', () => {
    expect(eastResizeHandleOverlapsKebab(2)).toBe(false);
  });

  it('keeps the handle clear of the kebab on every taller tile too', () => {
    for (let h = 2; h <= 12; h += 1) {
      expect(eastResizeHandleOverlapsKebab(h)).toBe(false);
    }
  });

  it('regression guard: the pre-fix margin-top (-10px) DID overlap on h=2', () => {
    // Proves the test is meaningful — with react-resizable's uncorrected
    // -10px the enlarged handle reached up to 42px, overlapping the 4…52px
    // kebab band by ~10px (the exact defect reported in #487).
    const preFix = eastResizeHandleVerticalBand(tilePixelHeight(2), -10);
    expect(preFix.top).toBe(42);
    expect(eastResizeHandleOverlapsKebab(2, -10)).toBe(true);
  });
});
