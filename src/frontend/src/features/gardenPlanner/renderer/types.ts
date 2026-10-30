/**
 * The renderer boundary (REQ-053 §19.4, GP-NFR-009). The editor (tools, handles, snap, undo) talks
 * to a {@link PlanRenderer} and never imports a rendering library: `SvgPlanRenderer` is the MVP,
 * a Konva renderer can follow behind the same interface (D-01), and `HeadlessPlanRenderer` is the
 * test double. An ESLint `no-restricted-imports` block enforces it for `editor/**`.
 */
import type { ReactNode } from 'react';
import type { PlanModel } from '../model/planModel';
import type { AttentionCode, Lifecycle } from '../model/plantState';
import type { Geometry, GardenObjectType, PlanUnderlay, Point } from '../model/types';

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

/**
 * What a plant marker shows of its state (REQ-053 GP-UX-059/060/062), prepared by the caller from the
 * plant-states answer and the i18n texts: the renderer draws it and prints `ariaLabel`, nothing else.
 */
export interface PlantMarkerState {
  lifecycle: Lifecycle;
  /** The one badge: the highest-priority reason that needs attention (GP-UX-060), else `null`. */
  badge: AttentionCode | null;
  /** Species initial on the disc (GP-UX-015). */
  initial: string;
  /** Phase progress 0…1 for the ring segment at detail zoom; `null` when the phase has no typical length. */
  progress: number | null;
  /** Species, phase and what needs attention, e.g. "Tomate, Blüte, 2 Aufgaben überfällig" (GP-UX-062). */
  ariaLabel: string;
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
  /** "{n} Pflanzen · {m} mit Handlungsbedarf" for a cluster whose plant states are known (GP-FR-190). */
  clusterSummary?: (params: { count: number; attention: number }) => string;
  objectType: (type: GardenObjectType) => string;
  /** Short dimension text: "2 × 1 m", "Ø 3 m" or "4 m²". */
  size: (geometry: Geometry, areaM2: number) => string;
}

/** One irrigation zone as the zone layer draws it: outline and hatching over its beds (GP-FR-110). */
export interface ZoneLayerEntry {
  key: string;
  /** The zone's own colour (`#RRGGBB`); the hatching direction and the dash differ per zone, so colour is never the only cue. */
  color: string;
  /** Position in the zone list: picks the hatching variant, so neighbouring zones look different without their colour. */
  variant: number;
  locationKeys: readonly string[];
}

/** One bed's "days since the last watering" for the layer of that name (GP-UX-031). */
export interface WateredLayerEntry {
  days: number;
  /** `d0_1` | `d2_3` | `d4_7` | `d8plus`: picks the pattern. */
  wateredClass: 'd0_1' | 'd2_3' | 'd4_7' | 'd8plus';
}

/** The background picture as the renderer draws it (GP-FR-033): a loaded `blob:` URL, its size in pixels and the placement. */
export interface UnderlayRenderEntry {
  href: string;
  widthPx: number;
  heightPx: number;
  underlay: PlanUnderlay;
}

export interface RenderOptions {
  labels: RendererLabels;
  /** The underlay layer; absent = hidden (or no picture). Drawn below every object, in the editor only. */
  underlayLayer?: UnderlayRenderEntry;
  /** The zone layer; absent = hidden. Decorative: the zone of a bed is also written in the properties panel. */
  zoneLayer?: readonly ZoneLayerEntry[];
  /**
   * The "last watered" layer by bed key; absent = hidden. `label` words a bed's number ("3 days since"), which is
   * all the layer says - it never claims that a bed needs water.
   */
  wateredLayer?: { byBed: Readonly<Record<string, WateredLayerEntry>>; label: (days: number) => string };
  /**
   * The site-condition layers (GP-FR-169): sun window, drainage and frost risk of each bed, drawn as pattern + glyph
   * from the plan's own site conditions. Absent or `false` = hidden; a bed without a value gets nothing.
   */
  sunLayer?: boolean;
  moistureLayer?: boolean;
  frostLayer?: boolean;
  /** Field mode raises the on-screen label size from 12 to 16 px (GP-NFR-067). */
  fieldMode?: boolean;
  /** The bed whose plants are the current focus level (GP-NFR-068: Enter enters a bed). */
  enteredLocationKey?: string | null;
  /**
   * Fill of a plant marker by the plant's phase definition key (GP-FR-067). Absent or unknown = the
   * default plant colour. The marker also carries a ring, so the phase colour is never the only cue.
   */
  phaseColors?: Readonly<Record<string, string>>;
  /**
   * The state of the plants of the entered bed by plant key (GP-UX-059). A plant without an entry keeps the
   * plain marker; a bed whose states are known shows "{n} Pflanzen · {m} mit Handlungsbedarf" as a cluster.
   */
  plantStates?: Readonly<Record<string, PlantMarkerState>>;
  /**
   * Keys of objects a refused save named (GP-UX-017): drawn with a red outline, and the panel explains why.
   * Never colour alone - the outline is also heavier.
   */
  invalidKeys?: ReadonlySet<string>;
  /** The plant whose info bubble is open; its marker points at it with `aria-describedby` (GP-UX-058). */
  describedPlantKey?: string | null;
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
