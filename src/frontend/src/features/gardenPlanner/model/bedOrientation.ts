/**
 * The long axis of a bed as a compass direction (REQ-053 §9.3, GP-FR-017, #2894).
 *
 * The TypeScript port of `orientation_calculator.bed_axis` (backend); both run against the operation `bed_axis` of
 * `spec/e2e-testcases/fixtures/garden-plan-vectors.json` (`bedOrientation.vectors.test.ts`). Pure: no I/O, no React.
 *
 * GP-FR-017 derives the orientation of a placed bed "aus `rotation_deg` + `north_angle_deg`" - the successor of
 * REQ-002's `bed_orientation` (north-south, east-west, diagonal), an axis and not a facing. The long axis lies in
 * the bed's own frame, before `rotation_deg`: a rect along +y when `length_m > width_m`, along +x when
 * `width_m > length_m`; a polygon is read like the rectangle enclosing it there (bounding box of the stored points,
 * extents compared at 0.001 m); a circle, a square and a polygon with a square bounding box have none. Turned by
 * `rotation_deg` (counter-clockwise) and read against `north_angle_deg` (clockwise), the azimuth is folded into
 * [0, 180) and rounded to 0.1 deg; it is named by its end between north and southeast (`north` = north-south axis).
 *
 * The server stores the derived `Location.orientation` (an aspect wins, GP-FR-168); the editor shows the axis live
 * while a bed is drawn or turned, before it is saved.
 */
import type { Orientation } from '@/api/types';
import { roundLength } from './geometry';
import { orientationFromAzimuth } from './windowOrientation';
import type { Geometry } from './types';

const HALF_TURN_DEG = 180;

export interface BedAxis {
  /** Compass azimuth of the axis folded into [0, 180), in steps of 0.1. */
  azimuthDeg: number;
  /** `north`, `northeast`, `east` or `southeast`: the axis's end between north and southeast. */
  orientation: Orientation;
}

/** Fold into [0, 180) and round to 0.1 deg, ties away from zero (`_round_half_turn`, Python `ROUND_HALF_UP`). */
function roundHalfTurn(azimuthDeg: number): number {
  const folded = ((azimuthDeg % HALF_TURN_DEG) + HALF_TURN_DEG) % HALF_TURN_DEG;
  const rounded = Number(folded.toFixed(1)) + 0;
  return rounded >= HALF_TURN_DEG ? 0 : rounded;
}

/** The mathematical angle of the long side in the bed's own frame (0 = +x, 90 = +y); `null` = square. */
function longSide(width: number, length: number): number | null {
  const w = roundLength(width);
  const l = roundLength(length);
  if (w === l) return null;
  return w > l ? 0 : 90;
}

function ownFrameAngle(geometry: Geometry): number | null {
  if (geometry.kind === 'rect') return longSide(geometry.width_m, geometry.length_m);
  if (geometry.kind === 'polygon') {
    const xs = geometry.points.map((point) => point[0]);
    const ys = geometry.points.map((point) => point[1]);
    return longSide(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys));
  }
  return null;
}

/** The sector naming an axis: its end between north and southeast (the north-south axis is `north`). */
export function orientationFromAxis(axisDeg: number): Orientation {
  const sector = orientationFromAzimuth(roundHalfTurn(axisDeg));
  return sector === 'south' ? 'north' : sector;
}

/** The long axis of `geometry` on a plan whose north lies at `northAngleDeg`; `null` without a long axis. */
export function bedAxis(geometry: Geometry, northAngleDeg: number): BedAxis | null {
  const own = ownFrameAngle(geometry);
  if (own === null) return null;
  const rotation =
    geometry.kind === 'rect' || geometry.kind === 'polygon' ? geometry.rotation_deg : 0;
  // Mathematical angle (counter-clockwise from +x) -> compass azimuth relative to plan north (`rotationToAzimuthDeg`),
  // written out in the reference's order of operations so both ports fold the same binary value.
  const azimuthDeg = roundHalfTurn(90 - (own + rotation) - northAngleDeg);
  return { azimuthDeg, orientation: orientationFromAxis(azimuthDeg) };
}

/** The other end of an axis named by `orientation` (`north` -> `south`), for "Nord–Süd" style labels. */
export function oppositeOrientation(orientation: Orientation): Orientation {
  const opposite: Record<Orientation, Orientation> = {
    north: 'south',
    northeast: 'southwest',
    east: 'west',
    southeast: 'northwest',
    south: 'north',
    southwest: 'northeast',
    west: 'east',
    northwest: 'southeast',
  };
  return opposite[orientation];
}
