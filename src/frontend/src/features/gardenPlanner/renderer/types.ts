/**
 * The renderer boundary (REQ-053 §19.4, GP-NFR-009). The editor (tools, handles, snap, undo) talks
 * to a {@link PlanRenderer} and never imports a rendering library: `SvgPlanRenderer` is the MVP,
 * a Konva renderer can follow behind the same interface (D-01), and `HeadlessPlanRenderer` is the
 * test double. An ESLint `no-restricted-imports` block enforces it for `editor/**`.
 */
import type { ReactNode } from 'react';
import type { PlanModel } from '../model/planModel';
import type { Geometry, GardenObjectType, Point } from '../model/types';

/**
 * What the screen shows. Screen space has its origin top-left with y pointing down; model space is
 * metres with y pointing up (§9.2), so one Viewport carries the flip: model `(originM[0],
 * originM[1])` is the top-left screen corner.
 */
export interface Viewport {
  /** Model coordinate (metres) at the top-left screen corner: (x_min, y_max). */
  originM: Point;
  /** Zoom as pixels per metre (GP-FR-150: 100 % = 100 px/m). */
  pxPerM: number;
  widthPx: number;
  heightPx: number;
}

export interface RenderSelection {
  /** Keys of selected locations, garden objects and plants. */
  selectedKeys: ReadonlySet<string>;
  /** The roving-tabindex stop (GP-NFR-068); falls back to the first selected, then the first object. */
  focusKey?: string | null;
}

/** Everything the renderer prints as text. Provided by the caller from i18n (no strings here). */
export interface RendererLabels {
  /** `aria-label` of the drawing surface. */
  canvas: string;
  /** `aria-roledescription` of the drawing surface (GP-NFR-068). */
  canvasRole: string;
  boundary: string;
  bed: (params: { name: string; size: string; plants: number; openTasks: number }) => string;
  object: (params: { label: string; typeLabel: string; size: string }) => string;
  plant: (params: { id: string }) => string;
  slot: (params: { id: string }) => string;
  cluster: (params: { count: number }) => string;
  objectType: (type: GardenObjectType) => string;
  /** Short dimension text: "2 × 1 m", "Ø 3 m" or "4 m²". */
  size: (geometry: Geometry, areaM2: number) => string;
}

export interface RenderOptions {
  labels: RendererLabels;
  /** Field mode raises the on-screen label size from 12 to 16 px (GP-NFR-067). */
  fieldMode?: boolean;
  /** The bed whose plants are the current focus level (GP-NFR-068: Enter enters a bed). */
  enteredLocationKey?: string | null;
  /** An object received focus (keyboard or pointer). */
  onFocusKey?: (key: string) => void;
  /** Enter or Space on a focused object. */
  onActivateKey?: (key: string) => void;
}

export interface PlanRenderer {
  /**
   * Draw `model` into `viewport`. Also remembers both as the scene the other methods answer
   * about: the renderer holds no state but caches (GP-NFR-005).
   */
  render(
    model: PlanModel,
    viewport: Viewport,
    selection: RenderSelection,
    options: RenderOptions,
  ): ReactNode;
  /** The topmost key at a screen point (GP-UX-032), or `null`. */
  hitTest(pointPx: Point): string | null;
  /** The whole stack at a screen point, topmost first (GP-UX-033, GP-NFR-065). */
  hitTestAll(pointPx: Point): string[];
  toScreen(pointM: Point): Point;
  toModel(pointPx: Point): Point;
  /**
   * Drag preview without a model update (GP-NFR-011): move the object's node by a screen offset via
   * a CSS transform. `null` clears every preview. The model changes on release only.
   */
  setDragOffset(key: string | null, dxPx?: number, dyPx?: number): void;
}
