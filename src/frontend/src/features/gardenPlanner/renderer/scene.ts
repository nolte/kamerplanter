/**
 * The renderer-independent part of a frame: which objects are in, in which order and at which
 * level of detail. `SvgPlanRenderer` turns a {@link Scene} into DOM, `HeadlessPlanRenderer` hands
 * it to tests, so culling, LOD and ordering are asserted once, without a DOM.
 */
import { ICON_MIN_PX, LABEL_MIN_PX, markersVisible } from './lod';
import { markerIndex, shapeEntries, type MarkerEntry, type ShapeEntry } from './planIndex';
import { ATTENTION_PRIORITY, type AttentionCode } from '../model/plantState';
import type { PlanModel } from '../model/planModel';
import type { RenderOptions, RenderSelection, Viewport } from './types';
import { cullBoundsM, intersects } from './viewport';

export interface SceneShape {
  entry: ShapeEntry;
  selected: boolean;
  /** A refused save named this object (GP-UX-017). */
  invalid: boolean;
  /** Roving tabindex 0 (GP-NFR-068); every other object is -1. */
  tabStop: boolean;
  showLabel: boolean;
  /** Garden objects only. */
  showIcon: boolean;
  /** Dimensions are printed for the selection only (GP-NFR-067). */
  showDimensions: boolean;
  plantCount: number;
}

/** An individually drawn marker: every marker of the entered bed, and a selected one anywhere. */
export interface SceneMarker {
  entry: MarkerEntry;
  selected: boolean;
  /** Only the plants of the entered bed are focus targets. */
  interactive: boolean;
  tabStop: boolean;
}

/**
 * The remaining markers of a bed, drawn as ONE path: they are decorative (the bed's label carries
 * the count), so a bed of 20 plants costs one DOM node instead of 20 - which is what keeps the
 * "large" class inside the DOM budget (GP-ACC-033). Hit testing reads the model, not these nodes.
 */
export interface SceneMarkerBatch {
  locationKey: string;
  markers: MarkerEntry[];
}

/** One summary per bed whose markers would be closer than 10 px (GP-NFR-067). */
export interface SceneCluster {
  locationKey: string;
  count: number;
  /** The centre of the bed, in metres. */
  x: number;
  y: number;
  /** Plants of the bed that need attention, when their states are known (GP-FR-190); else `null`. */
  attention: number | null;
  /** The highest-priority reason among them (GP-UX-060). */
  topBadge: AttentionCode | null;
}

export interface Scene {
  /** Paint order = DOM order: boundary, areas, paths, then beds and objects in reading order. */
  shapes: SceneShape[];
  markers: SceneMarker[];
  markerBatches: SceneMarkerBatch[];
  clusters: SceneCluster[];
  tabStopKey: string | null;
}

/** Row (north first) then column by the bounding box (GP-NFR-020), after layer and z-order. */
export function compareDomOrder(a: ShapeEntry, b: ShapeEntry): number {
  return (
    b.layer - a.layer ||
    a.zOrder - b.zOrder ||
    b.bbox[3] - a.bbox[3] ||
    a.bbox[0] - b.bbox[0] ||
    (a.key < b.key ? -1 : a.key > b.key ? 1 : 0)
  );
}

function screenSize(entry: ShapeEntry, pxPerM: number): [number, number] {
  return [(entry.bbox[2] - entry.bbox[0]) * pxPerM, (entry.bbox[3] - entry.bbox[1]) * pxPerM];
}

/** Plants that need attention among the markers (`null` when no plant of the bed has a known state) and the top reason. */
function attentionOf(
  markers: readonly MarkerEntry[],
  states: RenderOptions['plantStates'],
): Pick<SceneCluster, 'attention' | 'topBadge'> {
  if (!states) return { attention: null, topBadge: null };
  let known = 0;
  let attention = 0;
  let top: AttentionCode | null = null;
  for (const marker of markers) {
    if (marker.kind !== 'plant') continue;
    const state = states[marker.key];
    if (!state) continue;
    known += 1;
    if (state.badge === null) continue;
    attention += 1;
    if (top === null || ATTENTION_PRIORITY.indexOf(state.badge) < ATTENTION_PRIORITY.indexOf(top)) top = state.badge;
  }
  return { attention: known > 0 ? attention : null, topBadge: top };
}

export function buildScene(
  model: PlanModel,
  viewport: Viewport,
  selection: RenderSelection,
  options: Pick<RenderOptions, 'enteredLocationKey' | 'plantStates' | 'invalidKeys'>,
): Scene {
  const cull = cullBoundsM(viewport);
  const { pxPerM } = viewport;
  const selected = selection.selectedKeys;
  const markers = markerIndex(model);
  const entered = options.enteredLocationKey ?? null;

  // A focus target stays rendered outside the viewport (GP-NFR-069): culling never removes it.
  const kept = shapeEntries(model).filter(
    (entry) =>
      entry.key === selection.focusKey || selected.has(entry.key) || intersects(entry.bbox, cull),
  );
  kept.sort(compareDomOrder);

  const sceneMarkers: SceneMarker[] = [];
  const markerBatches: SceneMarkerBatch[] = [];
  const clusters: SceneCluster[] = [];
  for (const entry of kept) {
    if (entry.kind !== 'location') continue;
    const bed = markers.get(entry.key);
    if (!bed) continue;
    if (markersVisible(bed.minSpacingM, pxPerM)) {
      const isEntered = entry.key === entered;
      const rest: MarkerEntry[] = [];
      for (const marker of bed.markers) {
        const isSelected = selected.has(marker.key);
        if (isEntered || isSelected) {
          sceneMarkers.push({
            entry: marker,
            selected: isSelected,
            interactive: isEntered,
            tabStop: false,
          });
        } else {
          rest.push(marker);
        }
      }
      if (rest.length > 0) markerBatches.push({ locationKey: entry.key, markers: rest });
    } else if (bed.plantCount > 0) {
      clusters.push({
        locationKey: bed.locationKey,
        count: bed.plantCount,
        x: (entry.bbox[0] + entry.bbox[2]) / 2,
        y: (entry.bbox[1] + entry.bbox[3]) / 2,
        ...attentionOf(bed.markers, options.plantStates),
      });
    }
  }

  const shapes: SceneShape[] = kept.map((entry) => {
    const [widthPx, heightPx] = screenSize(entry, pxPerM);
    const isObject = entry.kind === 'gardenObject';
    return {
      entry,
      selected: selected.has(entry.key),
      invalid: options.invalidKeys?.has(entry.key) ?? false,
      tabStop: false,
      showLabel: entry.kind !== 'boundary' && widthPx >= LABEL_MIN_PX,
      showIcon: isObject && Math.max(widthPx, heightPx) >= ICON_MIN_PX,
      showDimensions: entry.kind !== 'boundary' && selected.has(entry.key),
      plantCount: markers.get(entry.key)?.plantCount ?? 0,
    };
  });

  // Roving tabindex: one tab stop on the current level. Inside an entered bed that is a plant,
  // else an object; the stop is the focus key, else the first selected, else the first in DOM order.
  const interactiveMarkers = sceneMarkers.filter((marker) => marker.interactive);
  const level: { key: string; selected: boolean; boundary: boolean }[] =
    interactiveMarkers.length > 0
      ? interactiveMarkers.map((m) => ({ key: m.entry.key, selected: m.selected, boundary: false }))
      : shapes.map((s) => ({
          key: s.entry.key,
          selected: s.selected,
          boundary: s.entry.kind === 'boundary',
        }));
  // The boundary encloses everything and is painted first; it is the default stop only when alone.
  const tabStopKey =
    level.find((item) => item.key === selection.focusKey)?.key ??
    level.find((item) => item.selected)?.key ??
    level.find((item) => !item.boundary)?.key ??
    level[0]?.key ??
    null;
  for (const shape of shapes) {
    shape.tabStop = interactiveMarkers.length === 0 && shape.entry.key === tabStopKey;
  }
  for (const marker of interactiveMarkers) marker.tabStop = marker.entry.key === tabStopKey;

  return { shapes, markers: sceneMarkers, markerBatches, clusters, tabStopKey };
}
