/**
 * Where the handles of a selected object sit and which one a pointer grabs (REQ-053 GP-FR-022/023,
 * GP-UX-048). Pure geometry: the editor computes handles in model space and projects them with
 * `PlanRenderer.toScreen`. A rect has eight handles and a rotate handle, a circle a radius handle,
 * a polygon or polyline one handle per vertex plus a "+" handle in the middle of each edge.
 */
import { rotatePoint } from '../../model/geometry';
import type { Geometry, Point } from '../../model/types';
import { effectiveVertices, RECT_HANDLE_IDS, rectHandleLocal } from './geometryEdit';

export type HandleKind = 'corner' | 'edge' | 'radius' | 'rotate' | 'vertex' | 'midpoint';

export interface Handle {
  /** `nw`..`w` for a rect, `radius`, `rotate`, `v<i>` and `m<i>` (the edge after vertex i). */
  id: string;
  kind: HandleKind;
  pointM: Point;
  /** The vertex index, or the index of the vertex before a midpoint. */
  index?: number;
}

/** Visible handle size and the hit area around it (GP-UX-048: 12-16 px visible, 48 px target). */
export const HANDLE_VISIBLE_PX = 14;
export const HANDLE_TARGET_PX = 48;
/** The rotate handle sits at least this far outside the edge (GP-UX-048). */
export const ROTATE_OFFSET_PX = 32;
/** An edge shorter than this on screen gets no "+" handle: it would sit on the vertex handles. */
const MIN_MIDPOINT_EDGE_PX = HANDLE_TARGET_PX;

/** How many handles the object's on-screen size leaves room for (GP-UX-048). */
export type HandleDensity = 'full' | 'corners' | 'none';

export interface HandleSet {
  density: HandleDensity;
  handles: Handle[];
}

function densityOf(sizePx: number): HandleDensity {
  if (sizePx < 2 * HANDLE_TARGET_PX) return 'none';
  if (sizePx < 3 * HANDLE_TARGET_PX) return 'corners';
  return 'full';
}

export function computeHandles(geometry: Geometry, pxPerM: number): HandleSet {
  const offsetM = ROTATE_OFFSET_PX / pxPerM;
  if (geometry.kind === 'rect') {
    const density = densityOf(Math.min(geometry.width_m, geometry.length_m) * pxPerM);
    if (density === 'none') return { density, handles: [] };
    const toPlan = (local: Point): Point =>
      rotatePoint(
        [geometry.origin[0] + local[0], geometry.origin[1] + local[1]],
        geometry.rotation_deg,
        geometry.origin,
      );
    const handles: Handle[] = RECT_HANDLE_IDS.filter(
      (id) => density === 'full' || id.length === 2,
    ).map((id) => ({
      id,
      kind: id.length === 2 ? 'corner' : 'edge',
      pointM: toPlan(rectHandleLocal(id, geometry.width_m, geometry.length_m)),
    }));
    handles.push({
      id: 'rotate',
      kind: 'rotate',
      pointM: toPlan([geometry.width_m / 2, geometry.length_m + offsetM]),
    });
    return { density, handles };
  }
  if (geometry.kind === 'circle') {
    const density = densityOf(geometry.radius_m * 2 * pxPerM);
    if (density === 'none') return { density, handles: [] };
    return {
      density,
      handles: [
        {
          id: 'radius',
          kind: 'radius',
          pointM: [geometry.origin[0] + geometry.radius_m, geometry.origin[1]],
        },
      ],
    };
  }
  if (geometry.kind === 'polygon' || geometry.kind === 'polyline') {
    const vertices = effectiveVertices(geometry);
    const handles: Handle[] = vertices.map((pointM, index) => ({
      id: `v${index}`,
      kind: 'vertex',
      pointM,
      index,
    }));
    const edges = geometry.kind === 'polygon' ? vertices.length : vertices.length - 1;
    for (let index = 0; index < edges; index += 1) {
      const from = vertices[index];
      const to = vertices[(index + 1) % vertices.length];
      if (Math.hypot(to[0] - from[0], to[1] - from[1]) * pxPerM < MIN_MIDPOINT_EDGE_PX) continue;
      handles.push({
        id: `m${index}`,
        kind: 'midpoint',
        pointM: [(from[0] + to[0]) / 2, (from[1] + to[1]) / 2],
        index,
      });
    }
    if (geometry.kind === 'polygon') {
      const top = Math.max(...vertices.map((vertex) => vertex[1]));
      const xs = vertices.map((vertex) => vertex[0]);
      handles.push({
        id: 'rotate',
        kind: 'rotate',
        pointM: [(Math.min(...xs) + Math.max(...xs)) / 2, top + offsetM],
      });
    }
    return { density: 'full', handles };
  }
  return { density: 'none', handles: [] };
}

/** When two handles are equally near, the one that is harder to hit by accident wins. */
const KIND_PRIORITY: Record<HandleKind, number> = {
  rotate: 0,
  vertex: 1,
  corner: 2,
  radius: 3,
  edge: 4,
  midpoint: 5,
};

/** The handle whose hit area contains `pointPx`; the nearest one when areas overlap. */
export function handleAt(
  handles: readonly Handle[],
  toScreen: (pointM: Point) => Point,
  pointPx: Point,
  radiusPx = HANDLE_TARGET_PX / 2,
): Handle | null {
  let best: { handle: Handle; distance: number } | null = null;
  for (const handle of handles) {
    const [x, y] = toScreen(handle.pointM);
    const distance = Math.hypot(x - pointPx[0], y - pointPx[1]);
    if (distance > radiusPx) continue;
    if (
      best === null ||
      distance < best.distance - 1 ||
      (Math.abs(distance - best.distance) <= 1 &&
        KIND_PRIORITY[handle.kind] < KIND_PRIORITY[best.handle.kind])
    ) {
      best = { handle, distance };
    }
  }
  return best?.handle ?? null;
}
