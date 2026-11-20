/** Layout constants shared by the editor and the page that fits the plan into it. */

/**
 * Width of the side panel (REQ-053 §17.3, GP-UX-068): docked beside the canvas from md up (#2885) where the canvas
 * keeps at least `MIN_CANVAS_WIDTH_PX`, a drawer over the canvas where it would not (#3034). Wide enough for the four
 * tab labels in one line. A collapsed panel takes no width at all (AC-5).
 */
export const PANEL_WIDTH_PX = 344;

/** The gap between the canvas area and the docked panel (the canvas row's `gap: 1`), and between the rail and it. */
export const PANEL_GAP_PX = 8;

/**
 * The canvas is never narrower than this beside a docked panel (#3034, operator decision): where docking the panel
 * would leave the canvas less, the panel opens as a drawer over the canvas instead. 320 CSS px is the reflow width of
 * WCAG 2.2 SC 1.4.10 - the narrowest width a page has to work at - and holds the zoom overlay (about 260 px in German)
 * with its insets. At 820 px (the app sidebar of 240 px beside it) a docked panel left the canvas 76 px.
 */
export const MIN_CANVAS_WIDTH_PX = 320;

/** The inset of the zoom overlay from the top and the right edge of the canvas area. */
export const ZOOM_OVERLAY_INSET_PX = 8;

/** Height of the zoom overlay: one row of 48 px targets. */
const ZOOM_OVERLAY_HEIGHT_PX = 48;

/**
 * Where the drawer starts below the top of the canvas row: under the zoom overlay in the top right corner, so the
 * drawer never covers the zoom controls (WCAG 2.2 SC 2.4.11 - the reason #2885 removed the earlier drawer).
 */
export const DRAWER_TOP_PX = ZOOM_OVERLAY_INSET_PX + ZOOM_OVERLAY_HEIGHT_PX + ZOOM_OVERLAY_INSET_PX;

/**
 * The form of the side panel (GP-UX-069): `docked` beside the canvas, `drawer` over the right edge of the canvas
 * (md and up, where docking would leave the canvas narrower than `MIN_CANVAS_WIDTH_PX`), `sheet` at the bottom
 * below md.
 */
export type SidePanelVariant = 'docked' | 'drawer' | 'sheet';

/**
 * The panel's form from the width actually available (#3034): below md the bottom sheet; from md up docked when the
 * canvas keeps at least `MIN_CANVAS_WIDTH_PX` beside the panel and its gap, else a drawer over the canvas.
 *
 * `canvasRoomPx` is the width the canvas has without a docked panel - the canvas row less the tool rail and its gap,
 * measured on the page, so the app sidebar and the paddings count. `null` (not laid out yet, jsdom) docks.
 */
export function sidePanelVariant(belowMd: boolean, canvasRoomPx: number | null): SidePanelVariant {
  if (belowMd) return 'sheet';
  if (canvasRoomPx === null) return 'docked';
  return canvasRoomPx - PANEL_WIDTH_PX - PANEL_GAP_PX >= MIN_CANVAS_WIDTH_PX ? 'docked' : 'drawer';
}
