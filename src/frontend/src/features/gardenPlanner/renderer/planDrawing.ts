/**
 * What the SVG and the Konva renderer draw alike (REQ-053 D-01, GP-NFR-009): the palette, the style of a shape, the
 * accessible names and the place of a bed's task badge. One module for both, so the two renderers cannot drift apart
 * in colour, name or badge; only the drawing primitive (an SVG node, a canvas call) differs.
 */
import type { KeyboardEvent } from 'react';
import { alpha, type Theme } from '@mui/material/styles';
import type { BedStatus, GardenObject, GardenObjectType, PlanLocation, Point } from '../model/types';
import { textLabelFontM } from '../model/textLabel';
import { labelAnchorOf } from './labelLayout';
import { isAreaLocation, type MarkerEntry, type ShapeEntry } from './planIndex';
import type { SceneCluster, SceneShape } from './scene';
import type { PlantMarkerState, RendererLabels } from './types';

// ── Palette ──────────────────────────────────────────────────────────────────

export interface PlanPalette {
  stroke: string;
  selected: string;
  text: string;
  boundary: string;
  bed: Record<BedStatus, { fill: string; dash?: string }>;
  /** An area location (garden, terrace, greenhouse, #2913): a light wash and a dotted outline, so not by colour alone. */
  area: { fill: string; dash: string };
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
    area: { fill: alpha(palette.secondary.main, 0.08), dash: '2 4' },
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

export function objectFill(object: GardenObject, palette: PlanPalette): string {
  return objectTypeFill(object.object_type, palette);
}

/** The fill of an object class; the object legend draws its swatch with it, so legend and plan cannot drift apart. */
export function objectTypeFill(type: GardenObjectType, palette: PlanPalette): string {
  switch (type) {
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

export interface ShapeStyle {
  fill: string;
  stroke: string;
  /** Screen pixels: strokes do not scale with the zoom. */
  strokeWidth: number;
  /** An SVG dash list in screen pixels ("6 4"), or `undefined` for a solid line. */
  strokeDasharray: string | undefined;
}

/**
 * A caption as drawn (GP-UX-071, #2913): its text centred in its box, turned with it, as large as the box allows - the
 * rule the PDF uses too (`text_label_font_m`). Centre in metres (plan frame), font size in metres, turn in degrees
 * counter-clockwise (the plan's sense; a drawing with y down mirrors it).
 */
export interface CaptionDrawing {
  text: string;
  x: number;
  y: number;
  fontM: number;
  rotationDeg: number;
}

/** The caption of a `text_label` entry, or `null` for every other shape (and for a caption without text). */
export function captionOf(entry: ShapeEntry): CaptionDrawing | null {
  if (entry.kind !== 'gardenObject' || entry.geometry.kind !== 'rect') return null;
  const object = entry.source as GardenObject;
  if (object.object_type !== 'text_label') return null;
  const text = object.label.trim();
  if (text === '') return null;
  const [x, y] = labelAnchorOf(entry.geometry).point;
  return {
    text,
    x,
    y,
    fontM: textLabelFontM(entry.geometry.width_m, entry.geometry.length_m, text),
    rotationDeg: entry.geometry.rotation_deg ?? 0,
  };
}

/** A caption's box is drawn only while it is selected or refused (dashed): on the plan it is its text alone. */
const CAPTION_SELECTED_DASH = '4 3';

export function shapeStyle(entry: ShapeEntry, selected: boolean, invalid: boolean, palette: PlanPalette): ShapeStyle {
  if (captionOf(entry) !== null) {
    return {
      fill: 'none',
      stroke: invalid ? palette.invalid : selected ? palette.selected : 'none',
      strokeWidth: invalid ? 2 : 1,
      strokeDasharray: invalid ? undefined : CAPTION_SELECTED_DASH,
    };
  }
  const location = entry.kind === 'location' ? (entry.source as PlanLocation) : null;
  const object = entry.kind === 'gardenObject' ? (entry.source as GardenObject) : null;
  // An area keeps its own look whatever its `bed_status` (REQ-053 §9.5, #2913).
  const bed = location ? (isAreaLocation(location) ? palette.area : palette.bed[location.bed_status]) : null;
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

/** The fill of a plant marker: its phase's colour, else the plant default. */
export function markerFill(
  phaseKey: string | null | undefined,
  palette: PlanPalette,
  phaseColors?: Readonly<Record<string, string>>,
): string {
  return (phaseKey && phaseColors?.[phaseKey]) || palette.plant;
}

/** An SVG dash list ("6 4") as the canvas wants it. */
export function dashList(dash: string | null | undefined): number[] {
  return dash ? dash.split(/[\s,]+/).filter(Boolean).map(Number) : [];
}

// ── SVG path data ────────────────────────────────────────────────────────────

/** Stable, short numbers keep DOM output (and its snapshots) free of float noise. */
export function num(value: number): string {
  return String(Number(value.toFixed(3)));
}

/** A model point in drawing coordinates (user unit = 1 m, y negated). */
export function point([x, y]: Point): string {
  return `${num(x)} ${num(-y)}`;
}

export function pathData(entry: ShapeEntry): string {
  const { shape } = entry;
  if (shape.kind === 'circle') return '';
  return `M${shape.vertices.map(point).join('L')}${shape.closed ? 'Z' : ''}`;
}

// ── Accessible names ─────────────────────────────────────────────────────────

/** The type icon of a garden object; beds, the boundary and a caption (it is its text) have none. */
export function shapeIconKind(entry: ShapeEntry): GardenObject['object_type'] | null {
  if (entry.kind !== 'gardenObject') return null;
  const type = (entry.source as GardenObject).object_type;
  return type === 'text_label' ? null : type;
}

/** The accessible name of a shape node (GP-NFR-020): the bed with size, plants and tasks, an object with its type. */
export function shapeAriaLabel(item: SceneShape, labels: RendererLabels): string {
  const { entry } = item;
  const size = labels.size(entry.geometry, entry.areaM2 || entry.bboxAreaM2);
  if (entry.kind === 'location') {
    const location = entry.source as PlanLocation;
    if (isAreaLocation(location) && labels.area) {
      return labels.area({ name: location.name, size, openTasks: location.open_task_count });
    }
    return labels.bed({
      name: location.name,
      size,
      plants: item.plantCount,
      openTasks: location.open_task_count,
    });
  }
  if (entry.kind === 'gardenObject') {
    const object = entry.source as GardenObject;
    // A caption is named by its text; the size of its box says nothing to a listener (GP-UX-071).
    if (object.object_type === 'text_label' && labels.caption) {
      return labels.caption({ text: object.label, typeLabel: labels.objectType(object.object_type) });
    }
    return labels.object({ label: object.label, typeLabel: labels.objectType(object.object_type), size });
  }
  return labels.boundary;
}

export function markerAriaLabel(entry: MarkerEntry, labels: RendererLabels, state?: PlantMarkerState): string {
  return entry.kind === 'plant'
    ? (state?.ariaLabel ?? labels.plant({ id: entry.displayId }))
    : labels.slot({ id: entry.displayId, plannedFrom: entry.plannedFrom ?? null });
}

export function clusterAriaLabel(cluster: SceneCluster, labels: RendererLabels): string {
  return cluster.attention !== null && labels.clusterSummary
    ? labels.clusterSummary({ count: cluster.count, attention: cluster.attention })
    : labels.cluster({ count: cluster.count });
}

/**
 * Enter or Space on a focused plan object activates it (GP-NFR-068). Enter acts on the press; Space acts on the
 * release, like a native button, because Space held down is also the editor's pan modifier (GP-FR-010): the press
 * only keeps the page from scrolling, see {@link activationKeyUp}.
 */
export function activationKeys(onActivateKey: ((key: string) => void) | undefined, key: string) {
  return (event: KeyboardEvent<SVGGElement>) => {
    if (!onActivateKey) return;
    if (event.key === 'Enter') {
      event.preventDefault();
      onActivateKey(key);
    } else if (event.key === ' ') {
      event.preventDefault();
    }
  };
}

/**
 * The release of Space activates a focused plan object - unless the editor already handled it (marked by
 * `preventDefault`): a Space that served as the pan modifier of a drag selects nothing (GP-FR-010).
 */
export function activationKeyUp(onActivateKey: ((key: string) => void) | undefined, key: string) {
  return (event: KeyboardEvent<SVGGElement>) => {
    if (onActivateKey && event.key === ' ' && !event.defaultPrevented) {
      event.preventDefault();
      onActivateKey(key);
    }
  };
}

// ── Task badge ───────────────────────────────────────────────────────────────

/** Radius of the task badge on a bed, in screen pixels. */
export const BADGE_RADIUS_PX = 11;
/** Font size of the count, in screen pixels. */
export const BADGE_FONT_PX = 12;
/** A bed narrower than this on screen shows no badge (the aria-label still carries the count). */
export const BADGE_MIN_BED_PX = 44;

/** Where a bed's task badge sits, in metres of the drawing (y already flipped), and what it says. */
export interface TaskBadgeBox {
  locationKey: string;
  text: string;
  overdue: boolean;
  /** Top-left corner and size, in metres of the drawing (y down). */
  left: number;
  top: number;
  width: number;
  height: number;
}

/**
 * The open-task badge of a bed (GP-FR-089), or `null` when the bed has no open task or is too narrow on screen. The
 * top-right corner of the box, except on a circle, where that corner lies outside the bed: there the badge sits on
 * the rim at 45 degrees. One digit is a circle; more grow into a pill so the number never spills out of its badge.
 */
export function taskBadgeOf(entry: ShapeEntry, pxPerM: number): TaskBadgeBox | null {
  if (entry.kind !== 'location') return null;
  if ((entry.bbox[2] - entry.bbox[0]) * pxPerM < BADGE_MIN_BED_PX) return null;
  const location = entry.source as PlanLocation;
  if (location.open_task_count <= 0) return null;
  const [x, y]: Point =
    entry.shape.kind === 'circle'
      ? [
          entry.shape.center[0] + entry.shape.radiusM * Math.SQRT1_2,
          -(entry.shape.center[1] + entry.shape.radiusM * Math.SQRT1_2),
        ]
      : [entry.bbox[2], -entry.bbox[3]];
  const text = location.open_task_count > 99 ? '99+' : String(location.open_task_count);
  const height = (2 * BADGE_RADIUS_PX) / pxPerM;
  const width = Math.max(height, (text.length * BADGE_FONT_PX * 0.62 + 10) / pxPerM);
  return {
    locationKey: entry.key,
    text,
    overdue: location.overdue_task_count > 0,
    left: x - width,
    top: y,
    width,
    height,
  };
}
