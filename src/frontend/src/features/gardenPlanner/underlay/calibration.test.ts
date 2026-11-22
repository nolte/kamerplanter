import { describe, expect, it } from 'vitest';
import type { PlanUnderlay } from '../model/types';
import {
  clampOpacity,
  metresPerPixel,
  pixelDistance,
  pixelsPerMetre,
  toImagePoint,
  underlayTransform,
} from './calibration';

/** REQ-053 GP-FR-033, WP 7.15: the two-point calibration (TC-053-044 step 2: 400 px apart, 4.0 m = 100 px/m). */
const CAL = { p1_px: [100, 200] as [number, number], p2_px: [500, 200] as [number, number], distance_m: 4 };

describe('two-point calibration', () => {
  it('turns two points 400 px apart and 4.0 m into 100 px per metre', () => {
    expect(pixelDistance(CAL.p1_px, CAL.p2_px)).toBe(400);
    expect(pixelsPerMetre(CAL)).toBe(100);
    expect(metresPerPixel(CAL)).toBeCloseTo(0.01, 10);
  });

  it('measures a diagonal by Pythagoras, not by one axis', () => {
    expect(pixelsPerMetre({ p1_px: [0, 0], p2_px: [300, 400], distance_m: 5 })).toBe(100);
  });

  it.each([
    ['two identical points', { ...CAL, p2_px: CAL.p1_px }],
    ['points less than a pixel apart', { ...CAL, p2_px: [100.4, 200.4] as [number, number] }],
    ['a zero distance', { ...CAL, distance_m: 0 }],
    ['a negative distance', { ...CAL, distance_m: -1 }],
    ['a distance beyond the limit', { ...CAL, distance_m: 2001 }],
    ['NaN', { ...CAL, distance_m: Number.NaN }],
    ['Infinity', { ...CAL, p2_px: [Number.POSITIVE_INFINITY, 0] as [number, number] }],
  ])('gives no scale for %s', (_name, calibration) => {
    expect(pixelsPerMetre(calibration)).toBeNull();
    expect(metresPerPixel(calibration)).toBeNull();
  });
});

describe('underlay transform', () => {
  const underlay = (patch: Partial<PlanUnderlay>): PlanUnderlay => ({
    attachment_key: 'att_1',
    calibration: CAL,
    origin: [2, 5],
    rotation_deg: 0,
    opacity: 0.5,
    ...patch,
  });

  it('places the picture at the plan origin, flipped into the SVG frame, at the calibrated scale', () => {
    expect(underlayTransform(underlay({}))).toBe('translate(2 -5) rotate(0) scale(0.01)');
  });

  it('turns counter-clockwise in the plan, which is a negative SVG rotation', () => {
    expect(underlayTransform(underlay({ rotation_deg: 30 }))).toBe('translate(2 -5) rotate(-30) scale(0.01)');
  });

  it('draws nothing for a calibration that gives no scale', () => {
    expect(underlayTransform(underlay({ calibration: { ...CAL, distance_m: 0 } }))).toBeNull();
  });
});

describe('pointer to picture pixel', () => {
  const box = { left: 10, top: 20, width: 400, height: 200 };
  const natural = { width: 800, height: 400 };

  it('scales a click inside the displayed picture to the picture pixel', () => {
    expect(toImagePoint([110, 70], box, natural)).toEqual([200, 100]);
  });

  it('ignores a click outside the picture', () => {
    expect(toImagePoint([5, 70], box, natural)).toBeNull();
    expect(toImagePoint([110, 400], box, natural)).toBeNull();
  });

  it('ignores a picture that has no size yet', () => {
    expect(toImagePoint([1, 1], { ...box, width: 0 }, natural)).toBeNull();
  });
});

describe('opacity', () => {
  it('stays within the faintest value the server accepts and fully opaque', () => {
    expect(clampOpacity(0)).toBe(0.05);
    expect(clampOpacity(2)).toBe(1);
    expect(clampOpacity(0.4)).toBe(0.4);
    expect(clampOpacity(Number.NaN)).toBe(0.5);
  });
});
