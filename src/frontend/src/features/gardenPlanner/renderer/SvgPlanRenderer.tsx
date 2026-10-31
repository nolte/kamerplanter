import { memo, useMemo, type KeyboardEvent, type ReactNode, type Ref } from 'react';
import { alpha, styled, useTheme, type Theme } from '@mui/material/styles';
import type { PlanModel } from '../model/planModel';
import type { BedStatus, GardenObject, PlanLocation, Point } from '../model/types';
import { BasePlanRenderer } from './BasePlanRenderer';
import { OBJECT_ICON_PATHS } from './icons';
import { ICON_SIZE_PX, MARKER_RADIUS_PX, labelFontPx } from './lod';
import { ICON_LINE_GAP_EM, labelAnchorOf } from './labelLayout';
import { PlantBadge, PlantMarkerBody } from './PlantMarker';
import { UnderlayLayer } from '../underlay/UnderlayLayer';
import { WateredLayer, ZoneLayer } from './ZoneOverlays';
import { ConditionLayer, FROST_CONDITION, MOISTURE_CONDITION, SUN_CONDITION } from './ConditionOverlays';
import { DETAIL_PX_PER_M, PLANT_INFO_ID, STATE_MARKER_RADIUS_PX } from './plantMarkerStyle';
import type { MarkerEntry, ShapeEntry } from './planIndex';
import {
  buildScene,
  type SceneCluster,
  type SceneMarker,
  type SceneMarkerBatch,
  type SceneShape,
} from './scene';
import type { PlantMarkerState, RenderOptions, RenderSelection, RendererLabels, Viewport } from './types';

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

// ── Palette ──────────────────────────────────────────────────────────────────

export interface PlanPalette {
  stroke: string;
  selected: string;
  text: string;
  boundary: string;
  bed: Record<BedStatus, { fill: string; dash?: string }>;
  object: string;
  tree: string;
  lawn: string;
  path: string;
  water: string;
  plant: string;
  slot: string;
  /** Outline of an object a refused save named (GP-UX-017). */
  invalid: string;
  /** Task badge on a bed (GP-FR-089): overdue tasks, otherwise open tasks; the text is the contrast of the fill. */
  badgeOverdue: { fill: string; text: string };
  badgeOpen: { fill: string; text: string };
}

export function planPalette(theme: Theme): PlanPalette {
  const { palette } = theme;
  return {
    stroke: palette.text.secondary,
    selected: palette.primary.main,
    text: palette.text.primary,
    // text.disabled is 2.7:1 on white; a boundary and an empty slot are information (WCAG 1.4.11, 3:1).
    boundary: palette.text.secondary,
    // Planned beds are dashed and retired ones grey, so status is not carried by colour alone.
    bed: {
      active: { fill: alpha(palette.success.main, 0.35) },
      planned: { fill: alpha(palette.info.main, 0.2), dash: '6 4' },
      retired: { fill: alpha(palette.grey[500], 0.2) },
    },
    object: alpha(palette.grey[500], 0.35),
    tree: alpha(palette.success.dark, 0.3),
    lawn: alpha(palette.success.light, 0.2),
    path: alpha(palette.warning.dark, 0.5),
    water: alpha(palette.info.main, 0.4),
    plant: palette.success.dark,
    slot: palette.text.secondary,
    invalid: palette.error.main,
    badgeOverdue: { fill: palette.error.main, text: palette.getContrastText(palette.error.main) },
    badgeOpen: { fill: palette.primary.main, text: palette.getContrastText(palette.primary.main) },
  };
}

function objectFill(object: GardenObject, palette: PlanPalette): string {
  switch (object.object_type) {
    case 'tree':
    case 'shrub':
      return palette.tree;
    case 'lawn':
      return palette.lawn;
    case 'path':
      return palette.path;
    case 'water_source':
      return palette.water;
    default:
      return palette.object;
  }
}

// ── Shape nodes ──────────────────────────────────────────────────────────────

/** Stable, short numbers keep DOM output (and its snapshots) free of float noise. */
function num(value: number): string {
  return String(Number(value.toFixed(3)));
}

function point([x, y]: Point): string {
  return `${num(x)} ${num(-y)}`;
}

function pathData(entry: ShapeEntry): string {
  const { shape } = entry;
  if (shape.kind === 'circle') return '';
  return `M${shape.vertices.map(point).join('L')}${shape.closed ? 'Z' : ''}`;
}

function activationKeys(onActivateKey: ((key: string) => void) | undefined, key: string) {
  return (event: KeyboardEvent<SVGGElement>) => {
    if (onActivateKey && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      onActivateKey(key);
    }
  };
}

interface ShapeNodeProps {
  item: SceneShape;
  pxPerM: number;
  fontPx: number;
  labels: RendererLabels;
  palette: PlanPalette;
  onFocusKey?: (key: string) => void;
  onActivateKey?: (key: string) => void;
}

/** Radius of the task badge on a bed, in screen pixels. */
const BADGE_RADIUS_PX = 11;
/** Font size of the count, in screen pixels. */
const BADGE_FONT_PX = 12;
/** A bed narrower than this on screen shows no badge (the aria-label still carries the count). */
const BADGE_MIN_BED_PX = 44;

function shapeStyle(entry: ShapeEntry, selected: boolean, invalid: boolean, palette: PlanPalette) {
  const location = entry.kind === 'location' ? (entry.source as PlanLocation) : null;
  const object = entry.kind === 'gardenObject' ? (entry.source as GardenObject) : null;
  const bed = location ? palette.bed[location.bed_status] : null;
  return {
    fill:
      entry.kind === 'boundary'
        ? 'none'
        : bed
          ? bed.fill
          : objectFill(object as GardenObject, palette),
    stroke: invalid
      ? palette.invalid
      : selected
        ? palette.selected
        : entry.kind === 'boundary'
          ? palette.boundary
          : palette.stroke,
    strokeWidth: invalid ? 4 : selected ? 3 : entry.kind === 'boundary' ? 2 : 1,
    strokeDasharray: invalid ? undefined : entry.kind === 'boundary' ? '10 6' : bed?.dash,
  };
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
  const widthPx = (entry.bbox[2] - entry.bbox[0]) * pxPerM;

  const size = labels.size(entry.geometry, entry.areaM2 || entry.bboxAreaM2);
  let ariaLabel: string;
  let iconPath: string | null = null;
  if (entry.kind === 'location') {
    const location = entry.source as PlanLocation;
    ariaLabel = labels.bed({
      name: location.name,
      size,
      plants: item.plantCount,
      openTasks: location.open_task_count,
    });
  } else if (entry.kind === 'gardenObject') {
    const object = entry.source as GardenObject;
    ariaLabel = labels.object({
      label: object.label,
      typeLabel: labels.objectType(object.object_type),
      size,
    });
    iconPath = OBJECT_ICON_PATHS[object.object_type];
  } else {
    ariaLabel = labels.boundary;
  }

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
      {entry.kind === 'location' && widthPx >= BADGE_MIN_BED_PX
        ? (() => {
            const location = entry.source as PlanLocation;
            if (location.open_task_count <= 0) return null;
            // The top-right corner of the box, except on a circle, where that corner lies outside the bed: there
            // the badge sits on the rim at 45 degrees.
            const badgeCorner: Point =
              entry.shape.kind === 'circle'
                ? [
                    entry.shape.center[0] + entry.shape.radiusM * Math.SQRT1_2,
                    -(entry.shape.center[1] + entry.shape.radiusM * Math.SQRT1_2),
                  ]
                : [entry.bbox[2], -entry.bbox[3]];
            return (
              <TaskBadge
                locationKey={entry.key}
                openCount={location.open_task_count}
                overdueCount={location.overdue_task_count}
                x={badgeCorner[0]}
                y={badgeCorner[1]}
                pxPerM={pxPerM}
                palette={palette}
              />
            );
          })()
        : null}
    </g>
  );
});

// ── Task badge ───────────────────────────────────────────────────────────────

interface TaskBadgeProps {
  locationKey: string;
  openCount: number;
  overdueCount: number;
  /** Where the badge's top-right corner sits, in drawing coordinates (y already flipped). */
  x: number;
  y: number;
  pxPerM: number;
  palette: PlanPalette;
}

/**
 * The open-task badge of a bed (GP-FR-089): the count of open tasks, red when some are overdue. It is
 * decorative for assistive technology - the bed's accessible name already says how many tasks are open,
 * and the properties panel offers the care tab as a button. The `data-plan-badge` marker lets the editor
 * recognise a click on it and open the care tab.
 */
function TaskBadge({ locationKey, openCount, overdueCount, x, y, pxPerM, palette }: TaskBadgeProps) {
  const colors = overdueCount > 0 ? palette.badgeOverdue : palette.badgeOpen;
  const text = openCount > 99 ? '99+' : String(openCount);
  const height = (2 * BADGE_RADIUS_PX) / pxPerM;
  // One digit is a circle; more grow into a pill so the number never spills out of its badge.
  const width = Math.max(height, (text.length * BADGE_FONT_PX * 0.62 + 10) / pxPerM);
  const left = x - width;
  return (
    <g
      className="gp-badge"
      data-plan-badge={locationKey}
      data-overdue={overdueCount > 0 ? 'true' : 'false'}
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

/** The fill of a plant marker: its phase's colour, else the plant default. */
function markerFill(phaseKey: string | null | undefined, palette: PlanPalette, phaseColors?: Readonly<Record<string, string>>) {
  return (phaseKey && phaseColors?.[phaseKey]) || palette.plant;
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
      aria-label={
        plant ? (state?.ariaLabel ?? labels.plant({ id: entry.displayId })) : labels.slot({ id: entry.displayId })
      }
      aria-describedby={described ? PLANT_INFO_ID : undefined}
      aria-pressed={selected}
      onFocus={onFocusKey ? () => onFocusKey(entry.key) : undefined}
      onKeyDown={onActivateKey ? activationKeys(onActivateKey, entry.key) : undefined}
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
      aria-label={
        cluster.attention !== null && labels.clusterSummary
          ? labels.clusterSummary({ count: cluster.count, attention: cluster.attention })
          : labels.cluster({ count: cluster.count })
      }
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
