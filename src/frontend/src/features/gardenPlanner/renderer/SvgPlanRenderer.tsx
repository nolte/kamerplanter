import { lazy, memo, Suspense, useMemo, type ReactNode, type Ref } from 'react';
import { styled, useTheme } from '@mui/material/styles';
import type { PlanModel } from '../model/planModel';
import { BasePlanRenderer } from './BasePlanRenderer';
import { OBJECT_ICON_PATHS } from './icons';
import { ICON_SIZE_PX, MARKER_RADIUS_PX, labelFontPx } from './lod';
import { ICON_LINE_GAP_EM, labelAnchorOf } from './labelLayout';
import { PlantBadge, PlantMarkerBody } from './PlantMarker';
import { UnderlayLayer } from '../underlay/UnderlayLayer';
import { WateredLayer, ZoneLayer } from './ZoneOverlays';
import { ConditionLayer, FROST_CONDITION, MOISTURE_CONDITION, SUN_CONDITION } from './ConditionOverlays';
import { DETAIL_PX_PER_M, PLANT_INFO_ID, STATE_MARKER_RADIUS_PX } from './plantMarkerStyle';
import type { MarkerEntry } from './planIndex';
import {
  activationKeyUp,
  activationKeys,
  BADGE_FONT_PX,
  clusterAriaLabel,
  markerAriaLabel,
  markerFill,
  num,
  pathData,
  planPalette,
  shapeAriaLabel,
  shapeIconKind,
  shapeStyle,
  taskBadgeOf,
  type PlanPalette,
  type TaskBadgeBox,
} from './planDrawing';
import {
  buildScene,
  type SceneCluster,
  type SceneMarker,
  type SceneMarkerBatch,
  type SceneShape,
} from './scene';
import type { PlantMarkerState, RenderOptions, RenderSelection, RendererLabels, Viewport } from './types';

export { planPalette, type PlanPalette };

// The companion-planting layer (GP-FR-134) is its own chunk (UI-NFR-003): nothing of it loads until it is switched on.
const CompanionLayer = lazy(() => import('./CompanionOverlay'));

/**
 * The MVP renderer (D-01): SVG in React behind the {@link PlanRenderer} boundary.
 *
 * - Zoom and pan are the `viewBox` (user unit = 1 m, y negated so the model's y-up shows up), so a
 *   pan or zoom changes one attribute; the object nodes are memoised and re-render only when their
 *   own props change (GP-NFR-008, GP-NFR-034).
 * - Only objects within the viewport plus 20 % are in the DOM (GP-NFR-010), with the LOD table of
 *   GP-NFR-067 deciding labels, icons, markers and clusters.
 * - A drag moves the dragged node with a CSS transform and no React render (GP-NFR-011).
 * - Every object is a `<g role="button" aria-label>`; one of them is the roving tab stop
 *   (GP-NFR-068), the rest `tabindex="-1"`.
 */
export class SvgPlanRenderer extends BasePlanRenderer {
  private root: SVGSVGElement | null = null;
  private dragNode: SVGElement | null = null;
  private dragKey: string | null = null;

  private readonly setRoot = (element: SVGSVGElement | null): void => {
    this.root = element;
    if (!element) {
      this.dragNode = null;
      this.dragKey = null;
    }
  };

  protected draw(
    model: PlanModel,
    viewport: Viewport,
    selection: RenderSelection,
    options: RenderOptions,
  ): ReactNode {
    return (
      <PlanSvg
        svgRef={this.setRoot}
        model={model}
        viewport={viewport}
        selection={selection}
        options={options}
      />
    );
  }

  setDragOffset(key: string | null, dxPx = 0, dyPx = 0): void {
    if (this.dragNode && key !== this.dragKey) {
      this.dragNode.style.transform = '';
      this.dragNode = null;
      this.dragKey = null;
    }
    const viewport = this.currentViewport;
    if (key === null || !this.root || !viewport) return;
    if (!this.dragNode) {
      for (const node of this.root.querySelectorAll<SVGElement>('[data-plan-key]')) {
        if (node.getAttribute('data-plan-key') === key) {
          this.dragNode = node;
          this.dragKey = key;
          break;
        }
      }
    }
    // CSS lengths on an SVG element are user units, and a user unit is a metre here.
    if (this.dragNode) {
      this.dragNode.style.transform = `translate(${dxPx / viewport.pxPerM}px, ${dyPx / viewport.pxPerM}px)`;
    }
  }
}

// ── Component ────────────────────────────────────────────────────────────────

const Canvas = styled('svg')(({ theme }) => ({
  display: 'block',
  // GP-NFR-066: no panning, text selection or long-press callout on the drawing surface.
  touchAction: 'none',
  userSelect: 'none',
  WebkitTouchCallout: 'none',
  // The drawing is in metres (viewBox), so an inherited letter or word spacing - the page's body type carries
  // 0.15 px - counts in metres too: "B e e t 1", labels running out of the plan (#2764). The plan sets its own.
  letterSpacing: 'normal',
  wordSpacing: 'normal',
  '& .gp-obj': { outline: 'none' },
  '& .gp-obj:focus-visible .gp-shape': {
    stroke: theme.palette.primary.main,
    strokeWidth: 3,
    strokeDasharray: 'none',
  },
}));

interface PlanSvgProps {
  svgRef: Ref<SVGSVGElement>;
  model: PlanModel;
  viewport: Viewport;
  selection: RenderSelection;
  options: RenderOptions;
}

function PlanSvg({ svgRef, model, viewport, selection, options }: PlanSvgProps) {
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
  const { pxPerM } = viewport;
  const fontPx = labelFontPx(fieldMode);
  const [ox, oy] = viewport.originM;
  const viewBox = `${num(ox)} ${num(-oy)} ${num(viewport.widthPx / pxPerM)} ${num(viewport.heightPx / pxPerM)}`;

  return (
    <Canvas
      ref={svgRef}
      xmlns="http://www.w3.org/2000/svg"
      width={viewport.widthPx}
      height={viewport.heightPx}
      viewBox={viewBox}
      role="group"
      aria-roledescription={labels.canvasRole}
      aria-label={labels.canvas}
      data-testid="garden-plan-svg"
      data-renderer="svg"
    >
      {underlayLayer ? <UnderlayLayer layer={underlayLayer} /> : null}
      {scene.shapes.map((item) => (
        <ShapeNode
          key={item.entry.key}
          item={item}
          pxPerM={pxPerM}
          fontPx={fontPx}
          labels={labels}
          palette={palette}
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
      {frostLayer ? (
        <ConditionLayer spec={FROST_CONDITION} shapes={scene.shapes} pxPerM={pxPerM} theme={theme} />
      ) : null}
      {scene.clusters.map((cluster) => (
        <ClusterNode
          key={cluster.locationKey}
          cluster={cluster}
          pxPerM={pxPerM}
          fontPx={fontPx}
          labels={labels}
          palette={palette}
        />
      ))}
      {/* Above the beds and clusters, below the plant markers: a marker stays pressable on top of its lines. */}
      {companionLayer && companionLayer.lines.length > 0 ? (
        <Suspense fallback={null}>
          <CompanionLayer lines={companionLayer.lines} viewport={viewport} />
        </Suspense>
      ) : null}
      {scene.markerBatches.map((batch) => (
        <MarkerBatchNode
          key={batch.locationKey}
          batch={batch}
          pxPerM={pxPerM}
          palette={palette}
          phaseColors={phaseColors}
        />
      ))}
      {scene.markers.map((marker) => (
        <MarkerNode
          key={marker.entry.key}
          marker={marker}
          pxPerM={pxPerM}
          labels={labels}
          palette={palette}
          phaseColors={phaseColors}
          state={marker.layerState ?? plantStates?.[marker.entry.key]}
          described={describedPlantKey === marker.entry.key}
          onFocusKey={onFocusKey}
          onActivateKey={onActivateKey}
        />
      ))}
    </Canvas>
  );
}

// ── Shape nodes ──────────────────────────────────────────────────────────────

interface ShapeNodeProps {
  item: SceneShape;
  pxPerM: number;
  fontPx: number;
  labels: RendererLabels;
  palette: PlanPalette;
  onFocusKey?: (key: string) => void;
  onActivateKey?: (key: string) => void;
}

const ShapeNode = memo(function ShapeNode({
  item,
  pxPerM,
  fontPx,
  labels,
  palette,
  onFocusKey,
  onActivateKey,
}: ShapeNodeProps) {
  const { entry, selected } = item;
  const style = shapeStyle(entry, selected, item.invalid, palette);
  const d = useMemo(() => pathData(entry), [entry]);
  // The name and the type icon sit at the shared label anchor - a polygon's pole of inaccessibility (GP-UX-047).
  const centre = labelAnchorOf(entry.geometry).point;
  const fontSize = fontPx / pxPerM;

  const size = labels.size(entry.geometry, entry.areaM2 || entry.bboxAreaM2);
  const ariaLabel = shapeAriaLabel(item, labels);
  const iconKind = shapeIconKind(entry);
  const iconPath = iconKind ? OBJECT_ICON_PATHS[iconKind] : null;
  const badge = taskBadgeOf(entry, pxPerM);

  const { label } = item;
  const cx = centre[0];
  const cy = -centre[1];
  const lineGap = (fontPx * ICON_LINE_GAP_EM) / pxPerM;
  const iconScale = ICON_SIZE_PX / 24 / pxPerM;
  const iconShift = label ? lineGap : 0;

  return (
    <g
      className="gp-obj"
      data-plan-key={entry.key}
      data-plan-kind={entry.kind}
      data-plan-invalid={item.invalid ? 'true' : undefined}
      role="button"
      tabIndex={item.tabStop ? 0 : -1}
      aria-label={ariaLabel}
      aria-pressed={selected}
      onFocus={onFocusKey ? () => onFocusKey(entry.key) : undefined}
      onKeyDown={onActivateKey ? activationKeys(onActivateKey, entry.key) : undefined}
      onKeyUp={onActivateKey ? activationKeyUp(onActivateKey, entry.key) : undefined}
    >
      {entry.shape.kind === 'circle' ? (
        <circle
          className="gp-shape"
          cx={num(entry.shape.center[0])}
          cy={num(-entry.shape.center[1])}
          r={num(entry.shape.radiusM)}
          {...style}
          vectorEffect="non-scaling-stroke"
        />
      ) : entry.geometry.kind === 'polyline' ? (
        <path
          className="gp-shape"
          d={d}
          fill="none"
          stroke={style.fill}
          strokeWidth={num(entry.geometry.width_m)}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ) : entry.geometry.kind === 'point' ? (
        <circle
          className="gp-shape"
          cx={num(entry.shape.vertices[0][0])}
          cy={num(-entry.shape.vertices[0][1])}
          r={num((MARKER_RADIUS_PX * 1.5) / pxPerM)}
          {...style}
          vectorEffect="non-scaling-stroke"
        />
      ) : (
        <path className="gp-shape" d={d} {...style} vectorEffect="non-scaling-stroke" />
      )}
      {iconPath && item.showIcon ? (
        <path
          d={iconPath}
          transform={`translate(${num(cx)} ${num(cy - iconShift)}) scale(${iconScale.toPrecision(4)}) translate(-12 -12)`}
          fill="none"
          stroke={palette.text}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        />
      ) : null}
      {label ? (
        <text
          data-testid={`garden-plan-label-${entry.key}`}
          x={num(label.x)}
          y={num(-label.y + (item.showIcon ? lineGap : fontSize / 3))}
          fontSize={fontSize.toPrecision(4)}
          textAnchor="middle"
          fill={palette.text}
          pointerEvents="none"
          aria-hidden="true"
        >
          {label.text}
        </text>
      ) : null}
      {item.showDimensions ? (
        // Outside, centred above the top edge (GP-UX-047).
        <text
          x={num((entry.bbox[0] + entry.bbox[2]) / 2)}
          y={num(-entry.bbox[3] - fontSize * 0.5)}
          fontSize={fontSize.toPrecision(4)}
          textAnchor="middle"
          fill={palette.selected}
          pointerEvents="none"
          aria-hidden="true"
        >
          {size}
        </text>
      ) : null}
      {badge ? <TaskBadge badge={badge} pxPerM={pxPerM} palette={palette} /> : null}
    </g>
  );
});

// ── Task badge ───────────────────────────────────────────────────────────────

interface TaskBadgeProps {
  badge: TaskBadgeBox;
  pxPerM: number;
  palette: PlanPalette;
}

/**
 * The open-task badge of a bed (GP-FR-089): the count of open tasks, red when some are overdue. It is
 * decorative for assistive technology - the bed's accessible name already says how many tasks are open,
 * and the properties panel offers the care tab as a button. The `data-plan-badge` marker lets the editor
 * recognise a click on it and open the care tab.
 */
function TaskBadge({ badge, pxPerM, palette }: TaskBadgeProps) {
  const colors = badge.overdue ? palette.badgeOverdue : palette.badgeOpen;
  const { text, left, top: y, width, height } = badge;
  const locationKey = badge.locationKey;
  return (
    <g
      className="gp-badge"
      data-plan-badge={locationKey}
      data-overdue={badge.overdue ? 'true' : 'false'}
      aria-hidden="true"
      style={{ cursor: 'pointer' }}
    >
      <rect
        x={num(left)}
        y={num(y)}
        width={num(width)}
        height={num(height)}
        rx={num(height / 2)}
        fill={colors.fill}
        stroke={colors.text}
        strokeWidth={1}
        vectorEffect="non-scaling-stroke"
      />
      <text
        x={num(left + width / 2)}
        y={num(y + height / 2)}
        fontSize={(BADGE_FONT_PX / pxPerM).toPrecision(4)}
        fontWeight="bold"
        textAnchor="middle"
        dominantBaseline="central"
        fill={colors.text}
        pointerEvents="none"
      >
        {text}
      </text>
    </g>
  );
}

// ── Markers and clusters ─────────────────────────────────────────────────────

interface MarkerNodeProps {
  marker: SceneMarker;
  pxPerM: number;
  labels: RendererLabels;
  palette: PlanPalette;
  phaseColors?: Readonly<Record<string, string>>;
  /** The plant's state (GP-UX-059); without one the plain marker is drawn. */
  state?: PlantMarkerState;
  /** The info bubble of this plant is open: point at it (GP-UX-058). */
  described?: boolean;
  onFocusKey?: (key: string) => void;
  onActivateKey?: (key: string) => void;
}

const MarkerNode = memo(function MarkerNode({
  marker,
  pxPerM,
  labels,
  palette,
  phaseColors,
  state,
  described,
  onFocusKey,
  onActivateKey,
}: MarkerNodeProps) {
  const { entry, selected, interactive, tabStop, layerState } = marker;
  const theme = useTheme();
  const plant = entry.kind === 'plant';
  // Inside the entered bed every known state is drawn; elsewhere the plant-state layer decides (GP-UX-061).
  const stated = plant && state !== undefined && (interactive || layerState !== undefined);
  const baseRadiusPx = stated ? STATE_MARKER_RADIUS_PX : MARKER_RADIUS_PX;
  const radius = (selected ? baseRadiusPx * 1.5 : baseRadiusPx) / pxPerM;
  const fill = markerFill(entry.phaseKey, palette, phaseColors);
  const circle = stated ? (
    <PlantMarkerBody
      entry={entry}
      state={state}
      radius={radius}
      pxPerM={pxPerM}
      fill={fill}
      ringColor={palette.text}
      initialColor={theme.palette.getContrastText(fill)}
      selectedColor={palette.selected}
      selected={selected}
      detail={pxPerM >= DETAIL_PX_PER_M}
    />
  ) : (
    <circle
      className="gp-shape"
      data-plan-key={interactive ? undefined : entry.key}
      data-plan-kind={interactive ? undefined : entry.kind}
      cx={num(entry.x)}
      cy={num(-entry.y)}
      r={num(radius)}
      fill={plant ? markerFill(entry.phaseKey, palette, phaseColors) : 'none'}
      // A standing plant has a solid ring in the text colour (never the fill alone); an empty or
      // planned position is dashed.
      stroke={selected ? palette.selected : plant ? palette.text : palette.slot}
      strokeWidth={selected ? 3 : 1}
      strokeDasharray={plant ? undefined : '2 2'}
      vectorEffect="non-scaling-stroke"
      aria-hidden={interactive ? undefined : 'true'}
    />
  );
  if (!interactive) {
    if (!stated) return circle;
    // A layer marker is decorative, like a batch: the bed's label carries the count, the bed view the details.
    return (
      <g data-plan-key={entry.key} data-plan-kind={entry.kind} data-plan-state-layer="true" aria-hidden="true" pointerEvents="none">
        {circle}
      </g>
    );
  }
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
      onKeyUp={onActivateKey ? activationKeyUp(onActivateKey, entry.key) : undefined}
    >
      {circle}
    </g>
  );
});

interface MarkerBatchNodeProps {
  batch: SceneMarkerBatch;
  pxPerM: number;
  palette: PlanPalette;
  phaseColors?: Readonly<Record<string, string>>;
}

/** `r`-radius circles as path commands: two arcs per circle. */
function circlesPath(points: readonly { x: number; y: number }[], r: number): string {
  return points
    .map(
      ({ x, y }) =>
        `M${num(x - r)} ${num(-y)}a${num(r)} ${num(r)} 0 1 0 ${num(2 * r)} 0a${num(r)} ${num(r)} 0 1 0 ${num(-2 * r)} 0`,
    )
    .join('');
}

const MarkerBatchNode = memo(function MarkerBatchNode({
  batch,
  pxPerM,
  palette,
  phaseColors,
}: MarkerBatchNodeProps) {
  const radius = MARKER_RADIUS_PX / pxPerM;
  // One path per fill: a bed in several phases keeps the batch cheap (a handful of paths, not one per plant).
  const byFill = new Map<string, MarkerEntry[]>();
  for (const marker of batch.markers) {
    if (marker.kind !== 'plant') continue;
    const fill = markerFill(marker.phaseKey, palette, phaseColors);
    const group = byFill.get(fill);
    if (group) group.push(marker);
    else byFill.set(fill, [marker]);
  }
  const slots = circlesPath(
    batch.markers.filter((m) => m.kind === 'slot'),
    radius,
  );
  return (
    <g data-plan-markers={batch.locationKey} aria-hidden="true" pointerEvents="none">
      {[...byFill].map(([fill, markers]) => (
        <path
          key={fill}
          d={circlesPath(markers, radius)}
          fill={fill}
          stroke={palette.text}
          vectorEffect="non-scaling-stroke"
        />
      ))}
      {slots ? (
        <path
          d={slots}
          fill="none"
          stroke={palette.slot}
          strokeDasharray="2 2"
          vectorEffect="non-scaling-stroke"
        />
      ) : null}
    </g>
  );
});

interface ClusterNodeProps {
  cluster: SceneCluster;
  pxPerM: number;
  fontPx: number;
  labels: RendererLabels;
  palette: PlanPalette;
}

const ClusterNode = memo(function ClusterNode({
  cluster,
  pxPerM,
  fontPx,
  labels,
  palette,
}: ClusterNodeProps) {
  const radius = (fontPx * 0.9) / pxPerM;
  return (
    <g
      data-plan-cluster={cluster.locationKey}
      role="img"
      aria-label={clusterAriaLabel(cluster, labels)}
      pointerEvents="none"
    >
      <circle
        cx={num(cluster.x)}
        cy={num(-cluster.y)}
        r={num(radius)}
        fill={palette.plant}
        fillOpacity={0.85}
      />
      <text
        x={num(cluster.x)}
        y={num(-cluster.y + fontPx / 3 / pxPerM)}
        fontSize={(fontPx / pxPerM).toPrecision(4)}
        textAnchor="middle"
        fill="#fff"
        aria-hidden="true"
      >
        {cluster.shownCount}
      </text>
      {cluster.attention && cluster.topBadge ? (
        <PlantBadge code={cluster.topBadge} x={cluster.x + radius * 0.85} y={-cluster.y - radius * 0.85} radius={radius * 0.55} />
      ) : null}
    </g>
  );
});
