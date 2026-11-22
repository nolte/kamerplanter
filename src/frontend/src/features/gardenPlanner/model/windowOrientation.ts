/**
 * Window orientation and the sun window it suggests for nearby locations (REQ-053 §9.8, GP-FR-181, WP 10.7).
 *
 * The TypeScript port of `app/domain/calculators/window_orientation.py`; both run against the operations
 * `window_facing` and `window_sun_window` of `spec/e2e-testcases/fixtures/garden-plan-vectors.json`
 * (`windowOrientation.vectors.test.ts`). Pure: no I/O, no React.
 *
 * Which way a window faces: the wall direction is the chord from the first to the last vertex of the window line;
 * the window faces along the normal that points outside, as a compass azimuth (0 = north, clockwise) relative to the
 * plan's `north_angle_deg`. The site outline tells the outside: two probes 0.5 m from the chord midpoint, one along
 * each normal - when exactly one lies inside, the other side is outside (`boundary`). Without an outline, or when
 * both or neither probe lies inside, the convention is that outside is LEFT of the drawing direction: walls traced
 * clockwise on screen keep the room on their right (`drawing_direction`).
 *
 * What it suggests (agrobiology review 2026-11-11): north gives no direct sun (diffuse light only), northeast/east/
 * southeast `morning`, south `midday`, southwest/west/northwest `afternoon`; south of the equator the azimuth is
 * mirrored first (a -> (180 - a) mod 360); without a latitude the northern hemisphere is assumed and said; between the
 * tropics nothing is suggested. Several windows: empty -> nothing, one value -> that value, all three -> `all_day`,
 * otherwise `mixed`. Only `sun_window` - no hours, no leaf shade, no `sun_exposure`, no PPFD/lux/DLI.
 */
import type { Orientation } from '@/api/types';
import { pointInPolygon, toShape } from './geometry';
import { rotationToAzimuthDeg } from './compass';
import type { Geometry, Point, SunWindow } from './types';

const FULL_TURN_DEG = 360;
const SECTOR_WIDTH_DEG = 45;
/** How far from the window both sides are probed against the outline, metres (`OUTSIDE_PROBE_M`). */
export const OUTSIDE_PROBE_M = 0.5;
/** `|latitude| <` this is tropical (`TROPIC_LATITUDE_DEG`). */
export const TROPIC_LATITUDE_DEG = 23.5;

export type FacingBasis = 'boundary' | 'drawing_direction';

/** Hint codes in their display order (`WindowHint`). */
export const WINDOW_HINTS = [
  'hemisphere_assumed',
  'tropics',
  'no_window',
  'diffuse_light_only',
  'shading_not_considered',
  'season',
  'window_distance',
  'glazing',
] as const;
export type WindowHint = (typeof WINDOW_HINTS)[number];

/** The caveats every suggestion carries. */
export const SUGGESTION_CAVEATS: readonly WindowHint[] = [
  'shading_not_considered',
  'season',
  'window_distance',
  'glazing',
];

/** The sun windows a suggestion can be: never `unknown` (no suggestion is `null`). */
export type SuggestedSunWindow = Exclude<SunWindow, 'unknown'>;

export interface WindowFacing {
  /** Compass azimuth of the outward normal, [0, 360) in steps of 0.1. */
  azimuthDeg: number;
  orientation: Orientation;
  basis: FacingBasis;
}

export interface SunWindowSuggestion {
  sunWindow: SuggestedSunWindow | null;
  hints: WindowHint[];
}

/** The sectors clockwise from north; index `i` is centred on `i * 45` degrees. */
const SECTORS: readonly Orientation[] = [
  'north',
  'northeast',
  'east',
  'southeast',
  'south',
  'southwest',
  'west',
  'northwest',
];

/** Northern-hemisphere table; `null` = no direct sun. */
const SUN_WINDOW_BY_ORIENTATION: Readonly<Record<Orientation, SuggestedSunWindow | null>> = {
  north: null,
  northeast: 'morning',
  east: 'morning',
  southeast: 'morning',
  south: 'midday',
  southwest: 'afternoon',
  west: 'afternoon',
  northwest: 'afternoon',
};

function wrap(angle: number): number {
  return ((angle % FULL_TURN_DEG) + FULL_TURN_DEG) % FULL_TURN_DEG;
}

/**
 * The compass sector of an azimuth - the port of `orientation_calculator.orientation_from_aspect`, the one sector
 * definition of the backend: eight sectors of 45 deg centred on their direction, a boundary belongs to the sector
 * that starts there clockwise (22.5 is northeast, 337.5 is north). Throws for a non-finite angle.
 */
export function orientationFromAzimuth(azimuthDeg: number): Orientation {
  if (!Number.isFinite(azimuthDeg)) throw new RangeError(`azimuth must be a finite angle, got ${azimuthDeg}`);
  const normalised = wrap(azimuthDeg);
  const index = Math.floor((normalised + SECTOR_WIDTH_DEG / 2) / SECTOR_WIDTH_DEG) % SECTORS.length;
  return SECTORS[index];
}

/** Wrap into [0, 360) and round to 0.1 deg, ties away from zero (`round_azimuth`, Python `ROUND_HALF_UP`). */
export function roundAzimuth(azimuthDeg: number): number {
  const rounded = Number(wrap(azimuthDeg).toFixed(1));
  return rounded >= FULL_TURN_DEG ? 0 : rounded;
}

function inside(point: Point, boundary: Geometry): boolean {
  const shape = toShape(boundary);
  if (shape.kind === 'circle') {
    return Math.hypot(point[0] - shape.center[0], point[1] - shape.center[1]) < shape.radiusM;
  }
  if (!shape.closed) return false;
  return pointInPolygon(point, shape.vertices);
}

/** The direction `window` faces, or `null` when it is no line or its chord has no length. */
export function windowFacing(
  window: Geometry,
  northAngleDeg: number,
  boundary: Geometry | null = null,
): WindowFacing | null {
  if (window.kind !== 'polyline') return null;
  const [x1, y1] = window.points[0];
  const [x2, y2] = window.points[window.points.length - 1];
  const dx = x2 - x1;
  const dy = y2 - y1;
  const length = Math.hypot(dx, dy);
  if (length === 0) return null;
  // The two normals in the plan frame (y up): left of the drawing direction and right of it.
  const left: Point = [-dy / length, dx / length];
  const right: Point = [dy / length, -dx / length];
  let outward = left;
  let basis: FacingBasis = 'drawing_direction';
  if (boundary !== null) {
    const mid: Point = [(x1 + x2) / 2, (y1 + y2) / 2];
    const leftInside = inside([mid[0] + left[0] * OUTSIDE_PROBE_M, mid[1] + left[1] * OUTSIDE_PROBE_M], boundary);
    const rightInside = inside([mid[0] + right[0] * OUTSIDE_PROBE_M, mid[1] + right[1] * OUTSIDE_PROBE_M], boundary);
    if (leftInside !== rightInside) {
      outward = leftInside ? right : left;
      basis = 'boundary';
    }
  }
  // Mathematical angle of the normal (counter-clockwise from +x) -> compass azimuth relative to plan north.
  const thetaDeg = (Math.atan2(outward[1], outward[0]) * 180) / Math.PI;
  const azimuthDeg = roundAzimuth(rotationToAzimuthDeg(thetaDeg) - northAngleDeg);
  return { azimuthDeg, orientation: orientationFromAzimuth(azimuthDeg), basis };
}

/** What one window facing `azimuthDeg` contributes outside the tropics; `null` = diffuse light only. */
export function contribution(azimuthDeg: number, latitude: number | null): SuggestedSunWindow | null {
  const mapped = latitude !== null && latitude < 0 ? wrap(180 - azimuthDeg) : azimuthDeg;
  return SUN_WINDOW_BY_ORIENTATION[orientationFromAzimuth(mapped)];
}

/** Whether `latitude` lies between the tropics; an unknown latitude is not (the north is assumed). */
export function isTropical(latitude: number | null): boolean {
  return latitude !== null && Math.abs(latitude) < TROPIC_LATITUDE_DEG;
}

/** The sun window the windows facing `azimuths` suggest at `latitude` (`Site.gps_coordinates[0]`). */
export function suggestSunWindow(azimuths: readonly number[], latitude: number | null): SunWindowSuggestion {
  const hints: WindowHint[] = [];
  if (latitude === null) hints.push('hemisphere_assumed');
  if (isTropical(latitude)) return { sunWindow: null, hints: [...hints, 'tropics'] };
  if (azimuths.length === 0) return { sunWindow: null, hints: [...hints, 'no_window'] };
  const contributions = azimuths.map((azimuth) => contribution(azimuth, latitude));
  if (contributions.includes(null)) hints.push('diffuse_light_only');
  const values = new Set(contributions.filter((value): value is SuggestedSunWindow => value !== null));
  if (values.size === 0) return { sunWindow: null, hints };
  let sunWindow: SuggestedSunWindow;
  if (values.size === 1) [sunWindow] = values;
  else if (values.has('morning') && values.has('midday') && values.has('afternoon')) sunWindow = 'all_day';
  else sunWindow = 'mixed';
  return { sunWindow, hints: [...hints, ...SUGGESTION_CAVEATS] };
}
