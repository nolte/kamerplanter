/**
 * The two angle conventions of the plan, kept apart on purpose (REQ-053 GP-FR-015):
 *
 * - `rotation_deg` is mathematical: counter-clockwise from +x.
 * - `north_angle_deg` is a compass azimuth: clockwise, 0 = north lies along +y (up on screen),
 *   90 = north lies along +x (right on screen).
 *
 * Never use one where the other belongs; convert with the named functions below.
 */
const FULL_TURN = 360;

/** Wrap into [0, 360) without the storage rounding. */
function wrap(angle: number): number {
  return ((angle % FULL_TURN) + FULL_TURN) % FULL_TURN;
}

/** Compass azimuth (clockwise from +y) -> mathematical angle (counter-clockwise from +x). */
export function azimuthToRotationDeg(azimuthDeg: number): number {
  return wrap(90 - azimuthDeg);
}

/** Mathematical angle (counter-clockwise from +x) -> compass azimuth (clockwise from +y). */
export function rotationToAzimuthDeg(rotationDeg: number): number {
  return wrap(90 - rotationDeg);
}

/** The unit vector in plan coordinates (y up) along which geographic north lies. */
export function northDirection(northAngleDeg: number): [number, number] {
  const radians = (azimuthToRotationDeg(northAngleDeg) * Math.PI) / 180;
  return [Math.cos(radians), Math.sin(radians)];
}

/**
 * The azimuth a pointer offset describes: `dx` to the right, `dy` downwards on screen (the
 * pixel convention), measured from straight up, clockwise. Rounded and wrapped to [0, 360).
 */
export function azimuthFromScreenOffset(dx: number, dy: number): number {
  return normalizeAzimuth((Math.atan2(dx, -dy) * 180) / Math.PI);
}

/** The value stored in `north_angle_deg`: [0, 360) in steps of 0.1 (GP-FR-015: 0-359,9). */
export function normalizeAzimuth(azimuthDeg: number): number {
  const rounded = Math.round(wrap(azimuthDeg) * 10) / 10;
  return rounded >= FULL_TURN ? 0 : rounded;
}
