/**
 * The user's own position on the plan in field mode (REQ-053 GP-UX-026). Pure: no browser API, no state.
 *
 * The site has one coordinate (`Site.gps_coordinates`, WGS84 `[lat, lon]`) and the plan its own metres. The site's
 * coordinate is read as the middle of the plan - the centre of the garden boundary's bounding box, else of
 * everything drawn - because nothing on the plan says which point the coordinate was taken at. The device's
 * offset from it is computed in a local east/north frame (equirectangular, ENU): at garden scale (a few hundred
 * metres) the error of that flat approximation stays in the centimetres, far below GPS accuracy. The east/north
 * offset is then turned into plan axes with `north_angle_deg` through {@link northDirection}, the same converter
 * the compass draws with, so "north" on the dot and on the compass can never disagree (GP-FR-015).
 *
 * The result is approximate on purpose and never leaves the device (SR-019): callers keep it in component state.
 */
import { northDirection } from './compass';
import type { BoundingBox, Point } from './types';

/** WGS84 coordinates in degrees. */
export interface GeoPoint {
  latitude: number;
  longitude: number;
}

/** Mean Earth radius (IUGG), metres. */
export const EARTH_RADIUS_M = 6_371_008.8;

/** The accuracy circle is never drawn smaller than this, whatever the device reports (GP-UX-026). */
export const MIN_ACCURACY_M = 3;

/** Beyond this distance from the plan the dot is not drawn; the user gets a hint instead. */
export const FAR_FROM_PLAN_M = 500;

const DEG_TO_RAD = Math.PI / 180;

/** East and north offset in metres of `point` from `origin` (local equirectangular frame). */
export function eastNorthOffsetM(origin: GeoPoint, point: GeoPoint): { eastM: number; northM: number } {
  const meanLatitude = ((origin.latitude + point.latitude) / 2) * DEG_TO_RAD;
  // Across the antimeridian the shorter way round counts.
  let deltaLongitude = point.longitude - origin.longitude;
  if (deltaLongitude > 180) deltaLongitude -= 360;
  else if (deltaLongitude < -180) deltaLongitude += 360;
  return {
    eastM: deltaLongitude * DEG_TO_RAD * Math.cos(meanLatitude) * EARTH_RADIUS_M,
    northM: (point.latitude - origin.latitude) * DEG_TO_RAD * EARTH_RADIUS_M,
  };
}

/**
 * An east/north offset expressed in plan axes (metres, y up) for the plan's `north_angle_deg` (compass azimuth,
 * clockwise; 0 = north is +y, 90 = north is +x). East lies a quarter turn clockwise from north.
 */
export function eastNorthToPlanOffset(eastM: number, northM: number, northAngleDeg: number): Point {
  const [nx, ny] = northDirection(northAngleDeg);
  // Clockwise quarter turn of (nx, ny) in a y-up frame.
  const ex = ny;
  const ey = -nx;
  return [eastM * ex + northM * nx, eastM * ey + northM * ny];
}

/** Where the site's coordinate sits on the plan: the middle of `bounds` (see the module comment). */
export function planAnchorM(bounds: BoundingBox): Point {
  return [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2];
}

/** The plan point of `device`, given the site's coordinate at `anchorM` and the plan's north angle. */
export function geoToPlanM(device: GeoPoint, site: GeoPoint, anchorM: Point, northAngleDeg: number): Point {
  const { eastM, northM } = eastNorthOffsetM(site, device);
  const [dx, dy] = eastNorthToPlanOffset(eastM, northM, northAngleDeg);
  return [anchorM[0] + dx, anchorM[1] + dy];
}

/** The radius of the accuracy circle: the device's accuracy, never below {@link MIN_ACCURACY_M}. */
export function accuracyRadiusM(deviceAccuracyM: number | null | undefined): number {
  return typeof deviceAccuracyM === 'number' && Number.isFinite(deviceAccuracyM)
    ? Math.max(MIN_ACCURACY_M, deviceAccuracyM)
    : MIN_ACCURACY_M;
}

/** Distance in metres from `point` to the box (0 inside it). */
export function distanceToBoxM([x, y]: Point, [x0, y0, x1, y1]: BoundingBox): number {
  return Math.hypot(Math.max(x0 - x, 0, x - x1), Math.max(y0 - y, 0, y - y1));
}

export type OwnPositionPlacement =
  | { kind: 'on_plan'; pointM: Point; radiusM: number }
  | { kind: 'far'; distanceM: number };

/**
 * Where to draw the dot, or that the device is too far from the plan to draw it (> {@link FAR_FROM_PLAN_M}
 * from `bounds`, the box of everything drawn) - a dot kilometres off-canvas would say nothing.
 */
export function placeOwnPosition(
  device: GeoPoint & { accuracyM?: number | null },
  site: GeoPoint,
  bounds: BoundingBox,
  northAngleDeg: number,
): OwnPositionPlacement {
  const pointM = geoToPlanM(device, site, planAnchorM(bounds), northAngleDeg);
  const distanceM = distanceToBoxM(pointM, bounds);
  if (!Number.isFinite(distanceM) || distanceM > FAR_FROM_PLAN_M) {
    return { kind: 'far', distanceM };
  }
  return { kind: 'on_plan', pointM, radiusM: accuracyRadiusM(device.accuracyM) };
}
