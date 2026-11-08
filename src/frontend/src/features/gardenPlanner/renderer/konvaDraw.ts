/**
 * The Konva renderer's drawing (REQ-053 D-01): a {@link Scene} painted onto a 2D canvas context in screen pixels,
 * the same scene, LOD, colours and label anchors the SVG renderer turns into DOM. Pure functions of a context and a
 * frame - no Konva, no React - so the test can hand them a recording context instead of a real canvas (jsdom has
 * none) and assert what is drawn where.
 *
 * Every stroke is in screen pixels (the SVG renderer's `non-scaling-stroke`), every text at its constant screen size.
 */
import { labelAnchorOf, ICON_LINE_GAP_EM } from './labelLayout';
import { ICON_SIZE_PX, MARKER_RADIUS_PX } from './lod';
import { OBJECT_ICON_PATHS } from './icons';
import {
  BADGE_FONT_PX,
  dashList,
  markerFill,
  shapeIconKind,
  shapeStyle,
  taskBadgeOf,
  type PlanPalette,
} from './planDrawing';
import {
  BADGE_OFFSET_SHARE,
  BADGE_OUTLINE,
  BADGE_RADIUS_SHARE,
  BADGE_STYLES,
  DETAIL_PX_PER_M,
  RING_STYLES,
  STATE_MARKER_RADIUS_PX,
} from './plantMarkerStyle';
import type { MarkerEntry } from './planIndex';
import type { Scene, SceneCluster, SceneMarker, SceneMarkerBatch, SceneShape } from './scene';
import type { PlantMarkerState, RendererLabels, Viewport } from './types';
import type { AttentionCode } from '../model/plantState';
import type { Point } from '../model/types';

/** The part of `CanvasRenderingContext2D` the drawing uses; a test passes a recorder with the same shape. */
export type PlanCanvasContext = Pick<
  CanvasRenderingContext2D,
  | 'save'
  | 'restore'
  | 'translate'
  | 'scale'
  | 'beginPath'
  | 'closePath'
  | 'moveTo'
  | 'lineTo'
  | 'arc'
  | 'fill'
  | 'stroke'
  | 'fillText'
  | 'setLineDash'
  | 'fillStyle'
  | 'strokeStyle'
  | 'lineWidth'
  | 'lineCap'
  | 'lineJoin'
  | 'globalAlpha'
  | 'font'
  | 'textAlign'
  | 'textBaseline'
>;

/** Builds a path from SVG path data (icons and badge glyphs); `Path2D` in a browser. */
export type PathFactory = (d: string) => Path2D;

/** Everything a frame needs besides the context: the scene and how it looks. */
export interface DrawFrame {
  scene: Scene;
  viewport: Viewport;
  palette: PlanPalette;
  labels: RendererLabels;
  fontPx: number;
  fontFamily: string;
  phaseColors?: Readonly<Record<string, string>>;
  plantStates?: Readonly<Record<string, PlantMarkerState>>;
  /** The text colour that reads on `fill` (MUI's `getContrastText`), for the species initial on a disc. */
  contrastText: (fill: string) => string;
  path: PathFactory;
}

/** The latest drag preview (GP-NFR-011): which node and by how many screen pixels. */
export interface DragPreview {
  key: string;
  dxPx: number;
  dyPx: number;
}

const TAU = Math.PI * 2;

function screen(frame: DrawFrame, [x, y]: Point): Point {
  const { originM, pxPerM } = frame.viewport;
  return [(x - originM[0]) * pxPerM, (originM[1] - y) * pxPerM];
}

function font(frame: DrawFrame, px: number, bold = false): string {
  return `${bold ? '700 ' : ''}${px}px ${frame.fontFamily}`;
}

function strokeWith(ctx: PlanCanvasContext, color: string, width: number, dash: number[] = []): void {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.setLineDash(dash);
  ctx.stroke();
}

// ── Shapes ───────────────────────────────────────────────────────────────────

function traceShape(ctx: PlanCanvasContext, frame: DrawFrame, item: SceneShape): void {
  const { entry } = item;
  ctx.beginPath();
  if (entry.shape.kind === 'circle') {
    const [cx, cy] = screen(frame, entry.shape.center);
    ctx.arc(cx, cy, entry.shape.radiusM * frame.viewport.pxPerM, 0, TAU);
    return;
  }
  if (entry.geometry.kind === 'point') {
    const [cx, cy] = screen(frame, entry.shape.vertices[0]);
    ctx.arc(cx, cy, MARKER_RADIUS_PX * 1.5, 0, TAU);
    return;
  }
  entry.shape.vertices.forEach((vertex, index) => {
    const [x, y] = screen(frame, vertex);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  if (entry.shape.closed) ctx.closePath();
}

/** One bed, garden object or the boundary: outline, type icon, name, dimensions and task badge, like `ShapeNode`. */
export function drawShape(ctx: PlanCanvasContext, frame: DrawFrame, item: SceneShape): void {
  const { entry } = item;
  const { pxPerM } = frame.viewport;
  const { palette, fontPx } = frame;
  const style = shapeStyle(entry, item.selected, item.invalid, palette);

  traceShape(ctx, frame, item);
  if (entry.geometry.kind === 'polyline') {
    // A fence or path is a wide stroke in its fill colour, as in the SVG.
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    strokeWith(ctx, style.fill, entry.geometry.width_m * pxPerM);
  } else {
    if (style.fill !== 'none') {
      ctx.fillStyle = style.fill;
      ctx.fill();
    }
    ctx.lineCap = 'butt';
    ctx.lineJoin = 'miter';
    strokeWith(ctx, style.stroke, style.strokeWidth, dashList(style.strokeDasharray));
  }

  const [cx, cy] = screen(frame, labelAnchorOf(entry.geometry).point);
  const lineGapPx = fontPx * ICON_LINE_GAP_EM;
  const { label } = item;
  const iconKind = shapeIconKind(entry);
  if (iconKind && item.showIcon) {
    const scale = ICON_SIZE_PX / 24;
    ctx.save();
    ctx.translate(cx, cy - (label ? lineGapPx : 0));
    ctx.scale(scale, scale);
    ctx.translate(-12, -12);
    ctx.strokeStyle = palette.text;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.setLineDash([]);
    ctx.stroke(frame.path(OBJECT_ICON_PATHS[iconKind]));
    ctx.restore();
  }

  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  if (label) {
    const [lx, ly] = screen(frame, [label.x, label.y]);
    ctx.font = font(frame, fontPx);
    ctx.fillStyle = palette.text;
    ctx.fillText(label.text, lx, ly + (item.showIcon ? lineGapPx : fontPx / 3));
  }
  if (item.showDimensions) {
    // Outside, centred above the top edge (GP-UX-047).
    const [dx, dy] = screen(frame, [(entry.bbox[0] + entry.bbox[2]) / 2, entry.bbox[3]]);
    ctx.font = font(frame, fontPx);
    ctx.fillStyle = palette.selected;
    ctx.fillText(frame.labels.size(entry.geometry, entry.areaM2 || entry.bboxAreaM2), dx, dy - fontPx * 0.5);
  }

  const badge = taskBadgeOf(entry, pxPerM);
  if (badge) {
    const colors = badge.overdue ? palette.badgeOverdue : palette.badgeOpen;
    // The badge box is in metres of the drawing (y down): back to pixels by the zoom.
    const left = (badge.left - frame.viewport.originM[0]) * pxPerM;
    const top = (badge.top + frame.viewport.originM[1]) * pxPerM;
    const width = badge.width * pxPerM;
    const height = badge.height * pxPerM;
    const r = height / 2;
    ctx.beginPath();
    ctx.arc(left + r, top + r, r, Math.PI / 2, (3 * Math.PI) / 2);
    ctx.lineTo(left + width - r, top);
    ctx.arc(left + width - r, top + r, r, -Math.PI / 2, Math.PI / 2);
    ctx.closePath();
    ctx.fillStyle = colors.fill;
    ctx.fill();
    strokeWith(ctx, colors.text, 1);
    ctx.font = font(frame, BADGE_FONT_PX, true);
    ctx.fillStyle = colors.text;
    ctx.textBaseline = 'middle';
    ctx.fillText(badge.text, left + width / 2, top + height / 2);
    ctx.textBaseline = 'alphabetic';
  }
}

// ── Plant badge, markers, clusters ───────────────────────────────────────────

/** One attention badge (GP-UX-060) centred at (`x`, `y`) px, `radiusPx` large: outline shape plus glyph. */
function drawPlantBadge(
  ctx: PlanCanvasContext,
  frame: DrawFrame,
  code: AttentionCode,
  x: number,
  y: number,
  radiusPx: number,
): void {
  const style = BADGE_STYLES[code];
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(radiusPx, radiusPx);
  ctx.setLineDash([]);
  ctx.fillStyle = style.fill;
  ctx.fill(frame.path(style.outline));
  ctx.strokeStyle = BADGE_OUTLINE;
  ctx.lineWidth = 1.5 / radiusPx;
  ctx.stroke(frame.path(style.outline));
  ctx.lineWidth = 1.4 / radiusPx;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.stroke(frame.path(style.glyph));
  ctx.restore();
}

function circle(ctx: PlanCanvasContext, x: number, y: number, r: number): void {
  ctx.beginPath();
  ctx.arc(x, y, r, 0, TAU);
}

/** The state channels of one plant (GP-UX-059/060), like `PlantMarkerBody`. */
function drawStatedMarker(
  ctx: PlanCanvasContext,
  frame: DrawFrame,
  entry: MarkerEntry,
  state: PlantMarkerState,
  radius: number,
  selected: boolean,
): void {
  const ring = RING_STYLES[state.lifecycle];
  const [cx, cy] = screen(frame, [entry.x, entry.y]);
  const fill = markerFill(entry.phaseKey, frame.palette, frame.phaseColors);
  const stroke = selected ? frame.palette.selected : frame.palette.text;

  circle(ctx, cx, cy, radius);
  if (ring.discOpacity > 0) {
    ctx.globalAlpha = ring.discOpacity;
    ctx.fillStyle = fill;
    ctx.fill();
  }
  ctx.globalAlpha = ring.ringOpacity;
  strokeWith(ctx, stroke, selected ? 3 : 1.5, dashList(ring.dash));
  ctx.globalAlpha = 1;
  if (ring.double) {
    circle(ctx, cx, cy, radius + 2.5);
    strokeWith(ctx, stroke, 1.5);
  }
  if (ring.seeds) {
    ctx.fillStyle = frame.palette.text;
    for (const [dx, dy] of [
      [-0.35, 0.25],
      [0.3, 0.3],
      [0, -0.35],
    ]) {
      circle(ctx, cx + dx * radius, cy + dy * radius, radius * 0.12);
      ctx.fill();
    }
  }
  if (ring.cross) {
    const d = radius * 0.6;
    ctx.beginPath();
    ctx.moveTo(cx - d, cy - d);
    ctx.lineTo(cx + d, cy + d);
    ctx.moveTo(cx + d, cy - d);
    ctx.lineTo(cx - d, cy + d);
    ctx.lineCap = 'round';
    strokeWith(ctx, frame.palette.text, 2);
  }
  const detail = frame.viewport.pxPerM >= DETAIL_PX_PER_M;
  if (detail && state.progress !== null && !ring.cross && state.progress > 0) {
    // From twelve o'clock clockwise by the phase's share (R-014).
    const share = Math.min(Math.max(state.progress, 0), 1);
    ctx.beginPath();
    ctx.arc(cx, cy, radius + 5, -Math.PI / 2, -Math.PI / 2 + share * TAU);
    ctx.lineCap = 'round';
    strokeWith(ctx, fill, 3);
  }
  if (!ring.cross && state.initial) {
    ctx.font = font(frame, radius * 1.15, true);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = frame.contrastText(fill);
    ctx.fillText(state.initial, cx, cy + radius * 0.38);
  }
  if (state.badge) {
    drawPlantBadge(
      ctx,
      frame,
      state.badge,
      cx + radius * BADGE_OFFSET_SHARE,
      cy - radius * BADGE_OFFSET_SHARE,
      radius * BADGE_RADIUS_SHARE,
    );
  }
}

/** One individually drawn marker, like `MarkerNode`: the state channels when known, else the plain disc or ring. */
export function drawMarker(ctx: PlanCanvasContext, frame: DrawFrame, marker: SceneMarker): void {
  const { entry, selected, interactive, layerState } = marker;
  const plant = entry.kind === 'plant';
  const state = layerState ?? frame.plantStates?.[entry.key];
  const stated = plant && state !== undefined && (interactive || layerState !== undefined);
  const base = stated ? STATE_MARKER_RADIUS_PX : MARKER_RADIUS_PX;
  const radius = selected ? base * 1.5 : base;
  if (stated && state) {
    drawStatedMarker(ctx, frame, entry, state, radius, selected);
    return;
  }
  const [cx, cy] = screen(frame, [entry.x, entry.y]);
  circle(ctx, cx, cy, radius);
  if (plant) {
    ctx.fillStyle = markerFill(entry.phaseKey, frame.palette, frame.phaseColors);
    ctx.fill();
  }
  // A standing plant has a solid ring in the text colour (never the fill alone); an empty or planned position is dashed.
  strokeWith(
    ctx,
    selected ? frame.palette.selected : plant ? frame.palette.text : frame.palette.slot,
    selected ? 3 : 1,
    plant ? [] : [2, 2],
  );
}

/** A bed's decorative markers as one path per fill (GP-ACC-033): the canvas twin of `MarkerBatchNode`. */
export function drawMarkerBatch(ctx: PlanCanvasContext, frame: DrawFrame, batch: SceneMarkerBatch): void {
  const r = MARKER_RADIUS_PX;
  const byFill = new Map<string, MarkerEntry[]>();
  const slots: MarkerEntry[] = [];
  for (const marker of batch.markers) {
    if (marker.kind !== 'plant') {
      slots.push(marker);
      continue;
    }
    const fill = markerFill(marker.phaseKey, frame.palette, frame.phaseColors);
    const group = byFill.get(fill);
    if (group) group.push(marker);
    else byFill.set(fill, [marker]);
  }
  const trace = (markers: readonly MarkerEntry[]) => {
    ctx.beginPath();
    for (const marker of markers) {
      const [x, y] = screen(frame, [marker.x, marker.y]);
      ctx.moveTo(x + r, y);
      ctx.arc(x, y, r, 0, TAU);
    }
  };
  for (const [fill, markers] of byFill) {
    trace(markers);
    ctx.fillStyle = fill;
    ctx.fill();
    strokeWith(ctx, frame.palette.text, 1);
  }
  if (slots.length > 0) {
    trace(slots);
    strokeWith(ctx, frame.palette.slot, 1, [2, 2]);
  }
}

/** One summary per dense bed (GP-NFR-067), like `ClusterNode`. */
export function drawCluster(ctx: PlanCanvasContext, frame: DrawFrame, cluster: SceneCluster): void {
  const radius = frame.fontPx * 0.9;
  const [cx, cy] = screen(frame, [cluster.x, cluster.y]);
  circle(ctx, cx, cy, radius);
  ctx.globalAlpha = 0.85;
  ctx.fillStyle = frame.palette.plant;
  ctx.fill();
  ctx.globalAlpha = 1;
  ctx.font = font(frame, frame.fontPx);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = '#fff';
  ctx.fillText(String(cluster.shownCount), cx, cy + frame.fontPx / 3);
  if (cluster.attention && cluster.topBadge) {
    drawPlantBadge(ctx, frame, cluster.topBadge, cx + radius * 0.85, cy - radius * 0.85, radius * 0.55);
  }
}

// ── Frame ────────────────────────────────────────────────────────────────────

/**
 * The whole scene in paint order (shapes, clusters, marker batches, markers), leaving out the node that is being
 * dragged: that one is drawn by {@link drawDragged} on its own layer, so a pointer move repaints one object and not
 * the plan (GP-NFR-011, GP-NFR-033).
 */
export function drawScene(ctx: PlanCanvasContext, frame: DrawFrame, excludeKey: string | null = null): void {
  const { scene } = frame;
  for (const item of scene.shapes) if (item.entry.key !== excludeKey) drawShape(ctx, frame, item);
  for (const cluster of scene.clusters) drawCluster(ctx, frame, cluster);
  for (const batch of scene.markerBatches) drawMarkerBatch(ctx, frame, batch);
  for (const marker of scene.markers) if (marker.entry.key !== excludeKey) drawMarker(ctx, frame, marker);
}

/** Whether the scene draws `key` as a node of its own (a shape or an individual marker) - only those move in a drag. */
export function drawsNode(scene: Scene, key: string): boolean {
  return (
    scene.shapes.some((item) => item.entry.key === key) || scene.markers.some((marker) => marker.entry.key === key)
  );
}

/** The dragged node, shifted by the preview offset; nothing when the scene does not draw it. */
export function drawDragged(ctx: PlanCanvasContext, frame: DrawFrame, preview: DragPreview | null): void {
  if (!preview) return;
  const shape = frame.scene.shapes.find((item) => item.entry.key === preview.key);
  const marker = shape ? undefined : frame.scene.markers.find((item) => item.entry.key === preview.key);
  if (!shape && !marker) return;
  ctx.save();
  ctx.translate(preview.dxPx, preview.dyPx);
  if (shape) drawShape(ctx, frame, shape);
  else if (marker) drawMarker(ctx, frame, marker);
  ctx.restore();
}
