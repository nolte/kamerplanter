/**
 * Own position on the plan (REQ-053 GP-UX-026): the projection of a device fix relative to `Site.gps_coordinates`
 * into plan metres, turned by `north_angle_deg` with the compass convention (GP-FR-015).
 */
import { describe, expect, it } from 'vitest';
import { northDirection } from './compass';
import {
  accuracyRadiusM,
  EARTH_RADIUS_M,
  eastNorthOffsetM,
  eastNorthToPlanOffset,
  FAR_FROM_PLAN_M,
  geoToPlanM,
  MIN_ACCURACY_M,
  placeOwnPosition,
  planAnchorM,
  type GeoPoint,
} from './ownPosition';
import type { BoundingBox, Point } from './types';

const SITE: GeoPoint = { latitude: 52.52, longitude: 13.405 };
const METRES_PER_DEG = (EARTH_RADIUS_M * Math.PI) / 180;

/** The device `northM` metres north and `eastM` metres east of the site. */
function offset(northM: number, eastM: number, site: GeoPoint = SITE): GeoPoint {
  const latitude = site.latitude + northM / METRES_PER_DEG;
  const meanLatitude = (((site.latitude + latitude) / 2) * Math.PI) / 180;
  return { latitude, longitude: site.longitude + eastM / (METRES_PER_DEG * Math.cos(meanLatitude)) };
}

function expectPoint(actual: Point, expected: Point, digits = 6) {
  expect(actual[0]).toBeCloseTo(expected[0], digits);
  expect(actual[1]).toBeCloseTo(expected[1], digits);
}

describe('eastNorthOffsetM', () => {
  it('reads known offsets back in metres', () => {
    const north = eastNorthOffsetM(SITE, offset(10, 0));
    expect(north.northM).toBeCloseTo(10, 6);
    expect(north.eastM).toBeCloseTo(0, 6);
    const east = eastNorthOffsetM(SITE, offset(0, 25));
    expect(east.eastM).toBeCloseTo(25, 6);
    expect(east.northM).toBeCloseTo(0, 6);
    const southWest = eastNorthOffsetM(SITE, offset(-40, -30));
    expect(southWest.northM).toBeCloseTo(-40, 6);
    expect(southWest.eastM).toBeCloseTo(-30, 6);
  });

  it('takes the short way across the antimeridian', () => {
    const site = { latitude: 0, longitude: 179.9999 };
    const { eastM } = eastNorthOffsetM(site, { latitude: 0, longitude: -179.9999 });
    expect(eastM).toBeGreaterThan(0);
    expect(eastM).toBeCloseTo(0.0002 * METRES_PER_DEG, 3);
  });
});

describe('eastNorthToPlanOffset (north angle, GP-FR-015)', () => {
  it('north angle 0: north is +y, east is +x', () => {
    expectPoint(eastNorthToPlanOffset(0, 10, 0), [0, 10]);
    expectPoint(eastNorthToPlanOffset(10, 0, 0), [10, 0]);
  });

  it('north angle 90: north is +x, east is -y (a quarter turn clockwise on screen)', () => {
    expectPoint(eastNorthToPlanOffset(0, 10, 90), [10, 0]);
    expectPoint(eastNorthToPlanOffset(10, 0, 90), [0, -10]);
  });

  it('north angle 30: north and east follow the compass, 30 degrees clockwise', () => {
    const sin = Math.sin(Math.PI / 6);
    const cos = Math.cos(Math.PI / 6);
    expectPoint(eastNorthToPlanOffset(0, 10, 30), [10 * sin, 10 * cos]);
    expectPoint(eastNorthToPlanOffset(10, 0, 30), [10 * cos, -10 * sin]);
  });

  it('north on the dot is north on the compass widget', () => {
    for (const angle of [0, 15, 90, 135.5, 270, 359.9]) {
      expectPoint(eastNorthToPlanOffset(0, 1, angle), northDirection(angle), 9);
    }
  });

  it('keeps distances (a rotation, no scaling)', () => {
    const [x, y] = eastNorthToPlanOffset(3, 4, 47);
    expect(Math.hypot(x, y)).toBeCloseTo(5, 9);
  });
});

describe('geoToPlanM', () => {
  const anchor: Point = [5, 5];

  it('places the site coordinate itself on the anchor', () => {
    expectPoint(geoToPlanM(SITE, SITE, anchor, 30), anchor);
  });

  it('known offsets land on the expected plan coordinates for north angle 0, 90 and 30', () => {
    const device = offset(10, 20);
    expectPoint(geoToPlanM(device, SITE, anchor, 0), [25, 15], 4);
    expectPoint(geoToPlanM(device, SITE, anchor, 90), [15, -15], 4);
    const sin = Math.sin(Math.PI / 6);
    const cos = Math.cos(Math.PI / 6);
    expectPoint(
      geoToPlanM(device, SITE, anchor, 30),
      [5 + 20 * cos + 10 * sin, 5 - 20 * sin + 10 * cos],
      4,
    );
  });
});

describe('placeOwnPosition', () => {
  const bounds: BoundingBox = [0, 0, 20, 10];

  it('anchors the site coordinate on the middle of the plan', () => {
    expectPoint(planAnchorM(bounds), [10, 5]);
    const placed = placeOwnPosition({ ...offset(2, -3), accuracyM: 8 }, SITE, bounds, 0);
    expect(placed.kind).toBe('on_plan');
    if (placed.kind !== 'on_plan') return;
    expectPoint(placed.pointM, [7, 7], 4);
    expect(placed.radiusM).toBe(8);
  });

  it('never draws the accuracy circle below 3 m', () => {
    expect(accuracyRadiusM(1)).toBe(MIN_ACCURACY_M);
    expect(accuracyRadiusM(null)).toBe(MIN_ACCURACY_M);
    expect(accuracyRadiusM(Number.NaN)).toBe(MIN_ACCURACY_M);
    expect(accuracyRadiusM(12.5)).toBe(12.5);
    const placed = placeOwnPosition({ ...SITE, accuracyM: 0.5 }, SITE, bounds, 0);
    expect(placed).toMatchObject({ kind: 'on_plan', radiusM: MIN_ACCURACY_M });
  });

  it('still draws a dot just outside the plan, but reports a device far away instead of drawing it', () => {
    // 100 m north of the anchor: 95 m beyond the plan's top edge - still drawn.
    expect(placeOwnPosition(offset(100, 0), SITE, bounds, 0).kind).toBe('on_plan');
    // 2 km east: far.
    const far = placeOwnPosition(offset(0, 2000), SITE, bounds, 0);
    expect(far.kind).toBe('far');
    if (far.kind === 'far') expect(far.distanceM).toBeGreaterThan(FAR_FROM_PLAN_M);
    // The limit itself: 500 m beyond the right edge (anchor x = 10, edge x = 20) is still on the plan.
    expect(placeOwnPosition(offset(0, 509), SITE, bounds, 0).kind).toBe('on_plan');
    expect(placeOwnPosition(offset(0, 511), SITE, bounds, 0).kind).toBe('far');
  });
});
