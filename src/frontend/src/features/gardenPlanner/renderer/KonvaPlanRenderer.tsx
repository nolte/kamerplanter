/**
 * The second renderer behind the {@link PlanRenderer} boundary (REQ-053 D-01, Anhang A 52): the plan painted onto a
 * Konva stage, for plans large enough that the SVG renderer misses the drag budget (GP-NFR-033, WP 9.6 measurement).
 * `createRenderer.ts` loads this module as its own chunk and only for such plans; everything else stays on SVG.
 *
 * Three stacked surfaces, one viewport:
 *
 * 1. **Underlay** (SVG, bottom): the background picture, when the layer is on - an `<image>` with its calibration
 *    transform, exactly the SVG renderer's `UnderlayLayer`.
 * 2. **Konva stage** (canvas, middle): every bed, object, name, icon, task badge, cluster and plant marker, drawn from
 *    the same {@link buildScene} result as the SVG (culling, LOD, label anchors). Two layers: the plan, and a drag
 *    layer that holds only the dragged node - a pointer move repaints that one node, never the plan (GP-NFR-011). The
 *    stage does not listen: hit testing reads the model ({@link BasePlanRenderer}), so Konva draws no hit canvas.
 * 3. **Overlay** (SVG, top): the accessible plan and the layers whose contract is DOM. Every object is the same
 *    focusable `<g role="button" data-plan-key aria-label>` the SVG renderer draws, with an unpainted outline that
 *    shows the focus ring (GP-NFR-020/068) - so the keyboard path, the roving tab stop, the editor's focus requests
 *    and the plant info bubble's anchor work unchanged; the list view stays the accessible alternative (§9.7). The
 *    zone, watering and site-condition layers and the companion layer are the SVG renderer's components (the
 *    companion lines carry `data-companion-edge` pointer targets, a task badge `data-plan-badge`). They sit above
 *    the canvas, so on this renderer they also cover the plant markers.
 */
import { lazy, memo, Suspense, useCallback, useLayoutEffect, useMemo, type ReactNode } from 'react';
import { styled, useTheme, type Theme } from '@mui/material/styles';
import type { Context } from 'konva/lib/Context';
import type { Layer as KonvaLayer } from 'konva/lib/Layer';
import { Layer, Shape, Stage } from 'react-konva/lib/ReactKonvaCore';
import type { PlanModel } from '../model/planModel';
import { UnderlayLayer } from '../underlay/UnderlayLayer';
import { BasePlanRenderer } from './BasePlanRenderer';
import { ConditionLayer, FROST_CONDITION, MOISTURE_CONDITION, SUN_CONDITION } from './ConditionOverlays';
import { drawDragged, drawScene, drawsNode, type DragPreview, type DrawFrame } from './konvaDraw';
import { MARKER_RADIUS_PX, labelFontPx } from './lod';
import {
  activationKeys,
  clusterAriaLabel,
  markerAriaLabel,
  num,
  pathData,
  planPalette,
  shapeAriaLabel,
  taskBadgeOf,
} from './planDrawing';
import { PLANT_INFO_ID, STATE_MARKER_RADIUS_PX } from './plantMarkerStyle';
import { buildScene, type Scene, type SceneCluster, type SceneMarker, type SceneShape } from './scene';
import type { PlantMarkerState, RenderOptions, RenderSelection, RendererLabels, Viewport } from './types';
import { WateredLayer, ZoneLayer } from './ZoneOverlays';

const CompanionLayer = lazy(() => import('./CompanionOverlay'));

/** What the renderer instance knows of the mounted stage: its two layers and the frame they draw. */
interface Surface {
  main: KonvaLayer | null;
  drag: KonvaLayer | null;
  scene: Scene | null;
  /** The accessible overlay: its node of the dragged object follows the drag (focus ring, badge target). */
  overlay: SVGSVGElement | null;
}

export class KonvaPlanRenderer extends BasePlanRenderer {
  private preview: DragPreview | null = null;
  private readonly surface: Surface = { main: null, drag: null, scene: null, overlay: null };
  private overlayNode: SVGElement | null = null;

  /** The node of the drag preview right now, or `null` (for tests and the drag layer). */
  get dragPreview(): DragPreview | null {
    return this.preview;
  }

  protected draw(model: PlanModel, viewport: Viewport, selection: RenderSelection, options: RenderOptions): ReactNode {
    return (
      <KonvaPlan renderer={this} model={model} viewport={viewport} selection={selection} options={options} />
    );
  }

  /**
   * Drag preview without a model update (GP-NFR-011): the dragged node leaves the plan layer for the drag layer and
   * moves there by the offset; the plan layer repaints once when the node changes, the drag layer on every move.
   */
  setDragOffset(key: string | null, dxPx = 0, dyPx = 0): void {
    const before = this.preview?.key ?? null;
    const scene = this.surface.scene;
    this.preview = key !== null && scene !== null && drawsNode(scene, key) ? { key, dxPx, dyPx } : null;
    const after = this.preview?.key ?? null;
    if (after !== before) this.surface.main?.batchDraw();
    this.surface.drag?.batchDraw();
    this.moveOverlayNode(after, dxPx, dyPx);
  }

  /** The overlay node moves like the SVG renderer's node: a CSS transform in metres (one user unit = 1 m). */
  private moveOverlayNode(key: string | null, dxPx: number, dyPx: number): void {
    if (this.overlayNode && this.overlayNode.getAttribute('data-plan-key') !== key) {
      this.overlayNode.style.transform = '';
      this.overlayNode = null;
    }
    const viewport = this.currentViewport;
    if (key === null || !this.surface.overlay || !viewport) return;
    if (!this.overlayNode) {
      for (const node of this.surface.overlay.querySelectorAll<SVGElement>('[data-plan-key]')) {
        if (node.getAttribute('data-plan-key') === key) {
          this.overlayNode = node;
          break;
        }
      }
    }
    if (this.overlayNode) {
      this.overlayNode.style.transform = `translate(${dxPx / viewport.pxPerM}px, ${dyPx / viewport.pxPerM}px)`;
    }
  }

  /** @internal The stage reports its layers and the scene it draws. */
  attach(part: Partial<Surface>): void {
    Object.assign(this.surface, part);
    if (part.overlay === null) this.overlayNode = null;
    if (part.scene !== undefined && this.preview && (part.scene === null || !drawsNode(part.scene, this.preview.key))) {
      this.preview = null;
    }
  }

  /** @internal The key the plan layer leaves out because the drag layer draws it. */
  get excludedKey(): string | null {
    return this.preview?.key ?? null;
  }
}

// ── Component ────────────────────────────────────────────────────────────────

const Root = styled('div')({
  position: 'relative',
  display: 'block',
  // GP-NFR-066: no panning, text selection or long-press callout on the drawing surface.
  touchAction: 'none',
  userSelect: 'none',
  WebkitTouchCallout: 'none',
  // The overlays draw text in metres (viewBox): an inherited letter spacing would count in metres too (#2764).
  letterSpacing: 'normal',
  wordSpacing: 'normal',
});

const Layered = styled('div')({ position: 'absolute', inset: 0, pointerEvents: 'none' });

const Overlay = styled('svg')(({ theme }) => ({
  position: 'relative',
  zIndex: 2,
  display: 'block',
  '& .gp-obj': { outline: 'none' },
  '& .gp-obj:focus-visible .gp-shape': {
    stroke: theme.palette.primary.main,
    strokeWidth: 3,
    strokeDasharray: 'none',
  },
}));

/** `getContrastText` per fill, computed once per theme: a frame asks it for every stated plant. */
function contrastOf(theme: Theme): (fill: string) => string {
  const cache = new Map<string, string>();
  return (fill) => {
    let text = cache.get(fill);
    if (text === undefined) {
      text = theme.palette.getContrastText(fill);
      cache.set(fill, text);
    }
    return text;
  };
}

function createPath(d: string): Path2D {
  return new Path2D(d);
}

interface KonvaPlanProps {
  renderer: KonvaPlanRenderer;
  model: PlanModel;
  viewport: Viewport;
  selection: RenderSelection;
  options: RenderOptions;
}

function KonvaPlan({ renderer, model, viewport, selection, options }: KonvaPlanProps) {
  const theme = useTheme();
  const {
    enteredLocationKey,
    fieldMode,
    labels,
    onFocusKey,
    onActivateKey,
    phaseColors,
    plantStates,
    plantStateLayer,
    describedPlantKey,
    invalidKeys,
    zoneLayer,
    wateredLayer,
    sunLayer,
    moistureLayer,
    frostLayer,
    underlayLayer,
    companionLayer,
    dimensionsOnOverlay,
  } = options;
  const scene = useMemo(
    () =>
      buildScene(model, viewport, selection, {
        enteredLocationKey,
        plantStates,
        invalidKeys,
        plantStateLayer,
        fieldMode,
        dimensionsOnOverlay,
      }),
    [model, viewport, selection, enteredLocationKey, plantStates, invalidKeys, plantStateLayer, fieldMode, dimensionsOnOverlay],
  );
  const palette = useMemo(() => planPalette(theme), [theme]);
  const contrastText = useMemo(() => contrastOf(theme), [theme]);
  const fontPx = labelFontPx(fieldMode);
  const frame = useMemo<DrawFrame>(
    () => ({
      scene,
      viewport,
      palette,
      labels,
      fontPx,
      fontFamily: theme.typography.fontFamily ?? 'sans-serif',
      phaseColors,
      plantStates,
      contrastText,
      path: createPath,
    }),
    [scene, viewport, palette, labels, fontPx, theme, phaseColors, plantStates, contrastText],
  );
  useLayoutEffect(() => renderer.attach({ scene }), [renderer, scene]);

  // A new frame is a new scene function: react-konva applies it and repaints the layer. A drag repaints without React.
  const drawPlan = useCallback(
    (context: Context) => drawScene(context._context, frame, renderer.excludedKey),
    [frame, renderer],
  );
  const drawDrag = useCallback(
    (context: Context) => drawDragged(context._context, frame, renderer.dragPreview),
    [frame, renderer],
  );
  const mainRef = useCallback((layer: KonvaLayer | null) => renderer.attach({ main: layer }), [renderer]);
  const dragRef = useCallback((layer: KonvaLayer | null) => renderer.attach({ drag: layer }), [renderer]);
  const overlayRef = useCallback((svg: SVGSVGElement | null) => renderer.attach({ overlay: svg }), [renderer]);

  const batchedMarkers = useMemo(
    () => scene.markerBatches.reduce((sum, batch) => sum + batch.markers.length, 0),
    [scene],
  );
  const { pxPerM } = viewport;
  const [ox, oy] = viewport.originM;
  const viewBox = `${num(ox)} ${num(-oy)} ${num(viewport.widthPx / pxPerM)} ${num(viewport.heightPx / pxPerM)}`;

  return (
    <Root style={{ width: viewport.widthPx, height: viewport.heightPx }}>
      {/* First in the DOM: the accessible surface is the plan's `svg` for every caller that looks one up. */}
      <Overlay
        ref={overlayRef}
        xmlns="http://www.w3.org/2000/svg"
        width={viewport.widthPx}
        height={viewport.heightPx}
        viewBox={viewBox}
        role="group"
        aria-roledescription={labels.canvasRole}
        aria-label={labels.canvas}
        data-testid="garden-plan-svg"
        data-renderer="konva"
        // What the canvas drew beyond the accessible targets, for the E2E census (WP 9.6 probe): the markers drawn
        // one by one and the decorative markers drawn in batches. The SVG renderer's DOM shows both itself.
        data-plan-markers-single={scene.markers.length}
        data-plan-markers-batched={batchedMarkers}
      >
        {scene.shapes.map((item) => (
          <ShapeTarget
            key={item.entry.key}
            item={item}
            pxPerM={pxPerM}
            labels={labels}
            onFocusKey={onFocusKey}
            onActivateKey={onActivateKey}
          />
        ))}
        {zoneLayer && zoneLayer.length > 0 ? (
          <ZoneLayer shapes={scene.shapes} zones={zoneLayer} pxPerM={pxPerM} theme={theme} />
        ) : null}
        {wateredLayer ? (
          <WateredLayer shapes={scene.shapes} layer={wateredLayer} pxPerM={pxPerM} fontPx={fontPx} theme={theme} />
        ) : null}
        {sunLayer ? <ConditionLayer spec={SUN_CONDITION} shapes={scene.shapes} pxPerM={pxPerM} theme={theme} /> : null}
        {moistureLayer ? (
          <ConditionLayer spec={MOISTURE_CONDITION} shapes={scene.shapes} pxPerM={pxPerM} theme={theme} />
        ) : null}
        {frostLayer ? <ConditionLayer spec={FROST_CONDITION} shapes={scene.shapes} pxPerM={pxPerM} theme={theme} /> : null}
        {scene.clusters.map((cluster) => (
          <ClusterTarget key={cluster.locationKey} cluster={cluster} pxPerM={pxPerM} fontPx={fontPx} labels={labels} />
        ))}
        {companionLayer && companionLayer.lines.length > 0 ? (
          <Suspense fallback={null}>
            <CompanionLayer lines={companionLayer.lines} viewport={viewport} />
          </Suspense>
        ) : null}
        {scene.markers.map((marker) =>
          marker.interactive ? (
            <MarkerTarget
              key={marker.entry.key}
              marker={marker}
              pxPerM={pxPerM}
              labels={labels}
              state={marker.layerState ?? plantStates?.[marker.entry.key]}
              described={describedPlantKey === marker.entry.key}
              onFocusKey={onFocusKey}
              onActivateKey={onActivateKey}
            />
          ) : null,
        )}
      </Overlay>
      <Layered style={{ zIndex: 1 }} aria-hidden="true" data-testid="garden-plan-konva">
        <Stage width={viewport.widthPx} height={viewport.heightPx} listening={false}>
          <Layer ref={mainRef} listening={false}>
            <Shape sceneFunc={drawPlan} listening={false} perfectDrawEnabled={false} />
          </Layer>
          <Layer ref={dragRef} listening={false}>
            <Shape sceneFunc={drawDrag} listening={false} perfectDrawEnabled={false} />
          </Layer>
        </Stage>
      </Layered>
      {underlayLayer ? (
        <Layered style={{ zIndex: 0 }} aria-hidden="true">
          <svg width={viewport.widthPx} height={viewport.heightPx} viewBox={viewBox} style={{ display: 'block' }}>
            <UnderlayLayer layer={underlayLayer} />
          </svg>
        </Layered>
      ) : null}
    </Root>
  );
}

// ── Accessible targets (unpainted) ───────────────────────────────────────────

/**
 * Unpainted: the canvas shows the object; the outline carries the focus ring, the geometry for `getBBox` and the
 * pointer target. `pointer-events` makes an unpainted area a target where the SVG renderer's painted one is (the fill
 * of a bed, the stroke of the boundary), so `elementFromPoint` and `event.target` name the same object on both.
 */
const UNPAINTED = { fill: 'none', stroke: 'none', vectorEffect: 'non-scaling-stroke', pointerEvents: 'visibleFill' } as const;

interface ShapeTargetProps {
  item: SceneShape;
  pxPerM: number;
  labels: RendererLabels;
  onFocusKey?: (key: string) => void;
  onActivateKey?: (key: string) => void;
}

const ShapeTarget = memo(function ShapeTarget({ item, pxPerM, labels, onFocusKey, onActivateKey }: ShapeTargetProps) {
  const { entry, selected } = item;
  const d = useMemo(() => pathData(entry), [entry]);
  const badge = taskBadgeOf(entry, pxPerM);
  return (
    <g
      className="gp-obj"
      data-plan-key={entry.key}
      data-plan-kind={entry.kind}
      data-plan-invalid={item.invalid ? 'true' : undefined}
      role="button"
      tabIndex={item.tabStop ? 0 : -1}
      aria-label={shapeAriaLabel(item, labels)}
      aria-pressed={selected}
      onFocus={onFocusKey ? () => onFocusKey(entry.key) : undefined}
      onKeyDown={onActivateKey ? activationKeys(onActivateKey, entry.key) : undefined}
    >
      {entry.shape.kind === 'circle' ? (
        <circle
          className="gp-shape"
          cx={num(entry.shape.center[0])}
          cy={num(-entry.shape.center[1])}
          r={num(entry.shape.radiusM)}
          {...UNPAINTED}
        />
      ) : entry.geometry.kind === 'point' ? (
        <circle
          className="gp-shape"
          cx={num(entry.shape.vertices[0][0])}
          cy={num(-entry.shape.vertices[0][1])}
          r={num((MARKER_RADIUS_PX * 1.5) / pxPerM)}
          {...UNPAINTED}
        />
      ) : entry.geometry.kind === 'polyline' ? (
        // A fence or path is its wide stroke, in metres like the drawing.
        <path
          className="gp-shape"
          d={d}
          fill="none"
          stroke="none"
          strokeWidth={num(entry.geometry.width_m)}
          strokeLinecap="round"
          strokeLinejoin="round"
          pointerEvents="visibleStroke"
        />
      ) : entry.kind === 'boundary' ? (
        // The boundary is a frame: only its edge is a target, as in the SVG renderer.
        <path className="gp-shape" d={d} {...UNPAINTED} strokeWidth={2} pointerEvents="visibleStroke" />
      ) : (
        <path className="gp-shape" d={d} {...UNPAINTED} />
      )}
      {badge ? (
        // The click target the editor recognises (`data-plan-badge`); the canvas draws the badge itself.
        <g
          className="gp-badge"
          data-plan-badge={badge.locationKey}
          data-overdue={badge.overdue ? 'true' : 'false'}
          aria-hidden="true"
          style={{ cursor: 'pointer' }}
        >
          <rect
            x={num(badge.left)}
            y={num(badge.top)}
            width={num(badge.width)}
            height={num(badge.height)}
            fill="none"
            pointerEvents="all"
          />
        </g>
      ) : null}
    </g>
  );
});

const ClusterTarget = memo(function ClusterTarget({
  cluster,
  pxPerM,
  fontPx,
  labels,
}: {
  cluster: SceneCluster;
  pxPerM: number;
  fontPx: number;
  labels: RendererLabels;
}) {
  return (
    <g data-plan-cluster={cluster.locationKey} role="img" aria-label={clusterAriaLabel(cluster, labels)} pointerEvents="none">
      <circle cx={num(cluster.x)} cy={num(-cluster.y)} r={num((fontPx * 0.9) / pxPerM)} fill="none" />
    </g>
  );
});

interface MarkerTargetProps {
  marker: SceneMarker;
  pxPerM: number;
  labels: RendererLabels;
  state?: PlantMarkerState;
  described: boolean;
  onFocusKey?: (key: string) => void;
  onActivateKey?: (key: string) => void;
}

/** A focusable plant or slot of the entered bed; decorative markers live on the canvas only, as in a batch. */
const MarkerTarget = memo(function MarkerTarget({
  marker,
  pxPerM,
  labels,
  state,
  described,
  onFocusKey,
  onActivateKey,
}: MarkerTargetProps) {
  const { entry, selected, tabStop } = marker;
  const stated = entry.kind === 'plant' && state !== undefined;
  const base = stated ? STATE_MARKER_RADIUS_PX : MARKER_RADIUS_PX;
  const radius = (selected ? base * 1.5 : base) / pxPerM;
  return (
    <g
      className="gp-obj"
      data-plan-key={entry.key}
      data-plan-kind={entry.kind}
      role="button"
      tabIndex={tabStop ? 0 : -1}
      aria-label={markerAriaLabel(entry, labels, state)}
      aria-describedby={described ? PLANT_INFO_ID : undefined}
      aria-pressed={selected}
      onFocus={onFocusKey ? () => onFocusKey(entry.key) : undefined}
      onKeyDown={onActivateKey ? activationKeys(onActivateKey, entry.key) : undefined}
    >
      <circle className="gp-shape" cx={num(entry.x)} cy={num(-entry.y)} r={num(radius)} {...UNPAINTED} />
    </g>
  );
});
