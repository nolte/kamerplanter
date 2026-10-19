/**
 * Derived, cached lookups the renderers share. Each cache is keyed by the identity of the model map
 * it was built from, so an edit that replaces one entry (structural sharing in `applyOperation`)
 * keeps the other indexes - and the entry objects the memoised SVG nodes compare by identity.
 */
import {
  anchor,
  boundingBox,
  rotationDeg,
  toShape,
  transformBedToPlan,
  transformPlanToBed,
  type Shape,
} from '../model/geometry';
import type { PlanModel } from '../model/planModel';
import type {
  BoundingBox,
  GardenObject,
  Geometry,
  PlanLocation,
  PlanPlant,
  PlanSettings,
  PlanSlot,
} from '../model/types';

/** Stand-in key of the garden boundary, which has no key of its own (GP-UX-032 lists it as a hit class). */
export const BOUNDARY_KEY = '__boundary__';

export type ShapeKind = 'location' | 'gardenObject' | 'boundary';

/**
 * Hit priority class (GP-UX-032), also the paint order reversed: 1 bed or garden object, 2 path,
 * 3 area (lawn), 4 boundary. Plant markers rank 0 and are not shape entries.
 */
export type ShapeLayer = 1 | 2 | 3 | 4;

export interface ShapeEntry {
  key: string;
  kind: ShapeKind;
  layer: ShapeLayer;
  geometry: Geometry;
  shape: Shape;
  bbox: BoundingBox;
  bboxAreaM2: number;
  zOrder: number;
  areaM2: number;
  /** The location or garden object; `null` for the boundary. */
  source: PlanLocation | GardenObject | null;
}

function entry(
  key: string,
  kind: ShapeKind,
  layer: ShapeLayer,
  geometry: Geometry,
  bbox: BoundingBox | null | undefined,
  zOrder: number,
  areaM2: number,
  source: PlanLocation | GardenObject | null,
): ShapeEntry {
  const box = bbox ?? boundingBox(geometry);
  return {
    key,
    kind,
    layer,
    geometry,
    shape: toShape(geometry),
    bbox: box,
    bboxAreaM2: (box[2] - box[0]) * (box[3] - box[1]),
    zOrder,
    areaM2,
    source,
  };
}

const locationCache = new WeakMap<object, ShapeEntry[]>();
const objectCache = new WeakMap<object, ShapeEntry[]>();
const boundaryCache = new WeakMap<object, ShapeEntry | null>();

function locationEntries(locations: Record<string, PlanLocation>): ShapeEntry[] {
  let cached = locationCache.get(locations);
  if (!cached) {
    cached = [];
    for (const location of Object.values(locations)) {
      if (!location.geometry) continue; // not placed on the plan
      cached.push(
        entry(
          location.key,
          'location',
          1,
          location.geometry,
          location.bbox,
          location.z_order,
          location.area_m2,
          location,
        ),
      );
    }
    locationCache.set(locations, cached);
  }
  return cached;
}

function objectLayer(object: GardenObject): ShapeLayer {
  if (object.object_type === 'path') return 2;
  if (object.object_type === 'lawn') return 3;
  return 1;
}

function objectEntries(objects: Record<string, GardenObject>): ShapeEntry[] {
  let cached = objectCache.get(objects);
  if (!cached) {
    cached = Object.values(objects).map((object) =>
      entry(
        object.key,
        'gardenObject',
        objectLayer(object),
        object.geometry,
        object.bbox,
        object.z_order,
        0,
        object,
      ),
    );
    objectCache.set(objects, cached);
  }
  return cached;
}

function boundaryEntry(settings: PlanSettings | null): ShapeEntry | null {
  if (!settings) return null;
  let cached = boundaryCache.get(settings);
  if (cached === undefined) {
    cached = settings.boundary
      ? entry(BOUNDARY_KEY, 'boundary', 4, settings.boundary, null, 0, 0, null)
      : null;
    boundaryCache.set(settings, cached);
  }
  return cached;
}

/** Every drawable location, garden object and the boundary of `model`, in no particular order. */
export function shapeEntries(model: PlanModel): ShapeEntry[] {
  const boundary = boundaryEntry(model.settings);
  const located = locationEntries(model.locations);
  const objects = objectEntries(model.gardenObjects);
  return boundary ? [boundary, ...located, ...objects] : [...located, ...objects];
}

// ── Plant and slot markers ───────────────────────────────────────────────────

export interface MarkerEntry {
  /** The plant key when the slot is occupied, else the slot key. */
  key: string;
  kind: 'plant' | 'slot';
  /** Instance id of the plant, or slot id of an empty position. */
  displayId: string;
  locationKey: string;
  x: number;
  y: number;
  /** Phase definition of the plant (`kind = 'plant'`); the renderer colours the marker by it (GP-FR-067). */
  phaseKey?: string | null;
}

export interface BedMarkers {
  locationKey: string;
  markers: MarkerEntry[];
  plantCount: number;
  /** Smallest distance between two markers in metres; `Infinity` for fewer than two. */
  minSpacingM: number;
  bbox: BoundingBox;
}

export type MarkerIndex = Map<string, BedMarkers>;

function minSpacing(markers: readonly MarkerEntry[]): number {
  if (markers.length < 2) return Infinity;
  const sorted = [...markers].sort((a, b) => a.x - b.x);
  let best = Infinity;
  for (let i = 0; i < sorted.length; i += 1) {
    for (let j = i + 1; j < sorted.length; j += 1) {
      const dx = sorted[j].x - sorted[i].x;
      if (dx >= best) break;
      const d = Math.hypot(dx, sorted[j].y - sorted[i].y);
      if (d < best) best = d;
    }
  }
  return best;
}

function buildMarkerIndex(
  slots: Record<string, PlanSlot>,
  plants: Record<string, PlanPlant>,
): MarkerIndex {
  const plantBySlot = new Map<string, PlanPlant>();
  for (const plant of Object.values(plants)) {
    if (plant.slot_key) plantBySlot.set(plant.slot_key, plant);
  }
  const perBed = new Map<string, MarkerEntry[]>();
  for (const slot of Object.values(slots)) {
    const origin = slot.plan_geometry?.origin;
    // Only point slots are markers; row and zone slots (polyline/polygon) have their own drawing.
    if (!origin || slot.plan_geometry?.kind) continue;
    const plant = plantBySlot.get(slot.key);
    const marker: MarkerEntry = {
      key: plant ? plant.key : slot.key,
      kind: plant ? 'plant' : 'slot',
      displayId: plant ? plant.instance_id : slot.slot_id,
      locationKey: slot.location_key,
      x: origin[0],
      y: origin[1],
      phaseKey: plant?.phase_key ?? null,
    };
    const list = perBed.get(slot.location_key);
    if (list) list.push(marker);
    else perBed.set(slot.location_key, [marker]);
  }
  const index: MarkerIndex = new Map();
  for (const [locationKey, markers] of perBed) {
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    let plantCount = 0;
    for (const marker of markers) {
      minX = Math.min(minX, marker.x);
      minY = Math.min(minY, marker.y);
      maxX = Math.max(maxX, marker.x);
      maxY = Math.max(maxY, marker.y);
      if (marker.kind === 'plant') plantCount += 1;
    }
    index.set(locationKey, {
      locationKey,
      markers,
      plantCount,
      minSpacingM: minSpacing(markers),
      bbox: [minX, minY, maxX, maxY],
    });
  }
  return index;
}

/** Same pivot and rotation = same bed frame: a resize or a change of other fields moves no slot. */
function sameFrame(a: Geometry, b: Geometry): boolean {
  if (a === b) return true;
  const [ax, ay] = anchor(a);
  const [bx, by] = anchor(b);
  return ax === bx && ay === by && rotationDeg(a) === rotationDeg(b);
}

function rebase(markers: BedMarkers, from: Geometry, to: Geometry): BedMarkers {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  const moved = markers.markers.map((marker) => {
    const [x, y] = transformBedToPlan(transformPlanToBed([marker.x, marker.y], from), to);
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
    return { ...marker, x, y };
  });
  // A rigid motion keeps every distance, so the spacing and the plant count carry over.
  return { ...markers, markers: moved, bbox: [minX, minY, maxX, maxY] };
}

/**
 * Slot positions are bed-local; the server delivers them in the plan frame of the bed as loaded
 * (`model.slotFrames`). A move or rotation of the bed replaces only its `locations` entry, so the
 * plan position is derived here: the marker is taken back into the bed frame it was delivered in and
 * out again through the bed's current geometry. Only beds whose frame differs are recomputed; the
 * other `BedMarkers` objects are reused as they are.
 */
function deriveMarkerIndex(base: MarkerIndex, model: PlanModel): MarkerIndex {
  const frames = model.slotFrames;
  if (!frames) return base;
  let derived: MarkerIndex | null = null;
  for (const [locationKey, bed] of base) {
    const from = frames[locationKey];
    const to = model.locations[locationKey]?.geometry;
    if (!from || !to || sameFrame(from, to)) continue;
    derived ??= new Map(base);
    derived.set(locationKey, rebase(bed, from, to));
  }
  return derived ?? base;
}

const markerCache = new WeakMap<object, WeakMap<object, MarkerIndex>>();
const derivedCache = new WeakMap<object, WeakMap<object, MarkerIndex>>();

/** Markers grouped by bed, with the per-bed plant count and marker spacing the LOD rule needs. */
export function markerIndex(model: PlanModel): MarkerIndex {
  let byPlants = markerCache.get(model.slots);
  if (!byPlants) {
    byPlants = new WeakMap();
    markerCache.set(model.slots, byPlants);
  }
  let base = byPlants.get(model.plants);
  if (!base) {
    base = buildMarkerIndex(model.slots, model.plants);
    byPlants.set(model.plants, base);
  }
  let byLocations = derivedCache.get(base);
  if (!byLocations) {
    byLocations = new WeakMap();
    derivedCache.set(base, byLocations);
  }
  let index = byLocations.get(model.locations);
  if (!index) {
    index = deriveMarkerIndex(base, model);
    byLocations.set(model.locations, index);
  }
  return index;
}
