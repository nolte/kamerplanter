/** Level-of-detail rules (GP-NFR-067) and the culling margin (GP-NFR-010), one place for both renderers. */

/** Viewport culling keeps objects within this fraction of the viewport size around it (GP-NFR-010). */
export const CULL_MARGIN = 0.2;

/** A bed name appears from this on-screen bed width. */
export const LABEL_MIN_PX = 60;
/** A garden object icon appears from this on-screen size. */
export const ICON_MIN_PX = 24;
/** Plant markers appear from this marker spacing; below it a bed shows one cluster with a count. */
export const MARKER_MIN_SPACING_PX = 10;
/** Label text is constant on screen, not scaled by the zoom. */
export const LABEL_FONT_PX = 12;
export const FIELD_LABEL_FONT_PX = 16;
/** Visible marker and icon sizes. */
export const MARKER_RADIUS_PX = 4;
export const ICON_SIZE_PX = 16;
/** Pointer tolerance around shapes and around markers. */
export const HIT_SLOP_PX = 4;
export const MARKER_HIT_RADIUS_PX = 8;

export function labelFontPx(fieldMode: boolean | undefined): number {
  return fieldMode ? FIELD_LABEL_FONT_PX : LABEL_FONT_PX;
}

/** A bed with fewer than two markers has no spacing (`Infinity`) and always shows its marker. */
export function markersVisible(minSpacingM: number, pxPerM: number): boolean {
  // The epsilon absorbs float noise: 0.1 m spacing computed as 0.09999999999999998 is 10 px.
  return minSpacingM * pxPerM >= MARKER_MIN_SPACING_PX - 1e-6;
}
