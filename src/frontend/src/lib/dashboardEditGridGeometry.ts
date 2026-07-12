/**
 * REQ-045 §3.8 — shared, single-source geometry for the dashboard edit surface.
 *
 * Two edit-mode hit areas live at a tile's top-right / right edge and must never
 * overlap (DASH-1, #487): the per-widget ⋮ kebab menu (WidgetFrame) and the east
 * width-resize handle (react-grid-layout, restyled in DashboardEditGrid). Both
 * files derive their positions from the constants here so the non-overlap
 * guarantee is verifiable in one place (`eastResizeHandleOverlapsKebab`) instead
 * of being split across two components' inline styles.
 *
 * All values are px in the tile's own (`.react-grid-item`) coordinate space,
 * whose origin is the tile's top-left corner.
 */

/** react-grid-layout row height (px) — one grid row. */
export const EDIT_GRID_ROW_HEIGHT = 44;

/** react-grid-layout vertical/horizontal margin between tiles (px). */
export const EDIT_GRID_MARGIN = 16;

/**
 * Enlarged resize-handle hit area (px), U-006 / UI-NFR-001 R-011 (MUSS ≥48px
 * touch target). Applied to `.react-resizable-handle` in DashboardEditGrid.
 */
export const RESIZE_HANDLE_SIZE = 48;

/**
 * Vertical offset applied to the *east* handle on top of react-resizable's
 * `top: 50%` (px). react-resizable ships `margin-top: -10px`, a value calibrated
 * for its original 20px handle so a 20px handle is centred on the right edge.
 * The U-006 enlargement to {@link RESIZE_HANDLE_SIZE}px leaves that -10px in
 * place, which shifts the enlarged hit area's top edge up to `H/2 - 10` — into
 * the kebab band on short tiles (#487). We reset it to 0 so the enlarged handle's
 * top edge sits exactly on the tile's vertical middle (`H/2`), clearing the
 * kebab on every tile ≥ h=2 while staying a full 48px ew-resize target.
 */
export const RESIZE_HANDLE_MARGIN_TOP = 0;

/** Inset of the kebab button from the tile's top and right edges (px). */
export const WIDGET_KEBAB_INSET = 4;

/**
 * Kebab button touch target (px), UI-NFR-001 R-011 (MUSS ≥48px). Must match the
 * IconButton size in WidgetFrame.
 */
export const WIDGET_KEBAB_SIZE = 48;

/** Rendered pixel height of a tile that spans `h` grid rows. */
export function tilePixelHeight(h: number): number {
  return h * EDIT_GRID_ROW_HEIGHT + (h - 1) * EDIT_GRID_MARGIN;
}

/** Vertical [top, bottom) band the kebab button occupies in the tile. */
export function widgetKebabVerticalBand(): { top: number; bottom: number } {
  return { top: WIDGET_KEBAB_INSET, bottom: WIDGET_KEBAB_INSET + WIDGET_KEBAB_SIZE };
}

/**
 * Vertical [top, bottom) band the east resize handle occupies on a tile of the
 * given pixel height. react-resizable positions it at `top: 50%` plus
 * `marginTop`; the enlarged handle then extends {@link RESIZE_HANDLE_SIZE}px
 * downward from that top edge.
 */
export function eastResizeHandleVerticalBand(
  tileHeightPx: number,
  marginTop: number = RESIZE_HANDLE_MARGIN_TOP,
): { top: number; bottom: number } {
  const top = tileHeightPx / 2 + marginTop;
  return { top, bottom: top + RESIZE_HANDLE_SIZE };
}

/**
 * Whether the east resize handle and the kebab button vertically overlap on a
 * tile spanning `h` grid rows. Both sit flush against the tile's right edge, so
 * they always overlap horizontally — the vertical bands are the discriminator.
 * A `marginTop` argument lets callers/tests model the pre-fix regression
 * (`marginTop = -10`) against the corrected value.
 */
export function eastResizeHandleOverlapsKebab(
  h: number,
  marginTop: number = RESIZE_HANDLE_MARGIN_TOP,
): boolean {
  const handle = eastResizeHandleVerticalBand(tilePixelHeight(h), marginTop);
  const kebab = widgetKebabVerticalBand();
  // Half-open bands: touching edges (handle.top === kebab.bottom) is not overlap.
  return handle.top < kebab.bottom && kebab.top < handle.bottom;
}
