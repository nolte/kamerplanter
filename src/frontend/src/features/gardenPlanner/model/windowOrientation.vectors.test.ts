import { describe, expect, it } from 'vitest';
import { parseGeometry } from './geometry';
import type { Geometry } from './types';
import {
  contribution,
  orientationFromAzimuth,
  roundAzimuth,
  suggestSunWindow,
  windowFacing,
  WINDOW_HINTS,
} from './windowOrientation';
import { loadVectors } from '@/test/gardenPlanVectors';

/**
 * The TypeScript port of the window orientation runs against the same vector file as the Python reference
 * (`tests/unit/domain/calculators/test_window_orientation_vectors.py`, REQ-053 GP-FR-181, §19.6). A test that copied
 * the cases inline would certify nothing.
 */
const VECTORS = loadVectors();
const FACING_CASES = VECTORS.cases.filter((vector) => vector.operation === 'window_facing');
const SUN_CASES = VECTORS.cases.filter((vector) => vector.operation === 'window_sun_window');

interface FacingInput {
  window: unknown;
  north_angle_deg: number;
  boundary: unknown;
}

interface SunInput {
  azimuths: number[];
  latitude: number | null;
}

function parseOrThrow(raw: unknown, id: string): Geometry {
  const geometry = parseGeometry(raw);
  if (geometry === null) throw new Error(`vector geometry does not parse: ${id}`);
  return geometry;
}

describe('window orientation vectors (shared with the Python reference)', () => {
  it('both operations are documented and have cases', () => {
    expect(VECTORS.operations).toHaveProperty('window_facing');
    expect(VECTORS.operations).toHaveProperty('window_sun_window');
    expect(FACING_CASES.length).toBeGreaterThan(0);
    expect(SUN_CASES.length).toBeGreaterThan(0);
  });

  it.each(FACING_CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const input = vector.input as unknown as FacingInput;
    const boundary = input.boundary === null ? null : parseOrThrow(input.boundary, vector.id);
    const facing = windowFacing(parseOrThrow(input.window, vector.id), input.north_angle_deg, boundary);
    const actual =
      facing === null
        ? null
        : { azimuth_deg: facing.azimuthDeg, orientation: facing.orientation, basis: facing.basis };
    expect(actual, vector.spec).toEqual(vector.expected);
  });

  it.each(SUN_CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const input = vector.input as unknown as SunInput;
    const result = suggestSunWindow(input.azimuths, input.latitude);
    expect({ sun_window: result.sunWindow, hints: result.hints }, vector.spec).toEqual(vector.expected);
  });

  it('every hint code of the port appears in the vectors', () => {
    const seen = new Set(SUN_CASES.flatMap((vector) => (vector.expected as { hints: string[] }).hints));
    expect([...seen].sort()).toEqual([...WINDOW_HINTS].sort());
  });
});

describe('window orientation rules (independent of the vector file)', () => {
  it('a single window is never all day', () => {
    for (let azimuth = 0; azimuth < 360; azimuth += 5) {
      expect(suggestSunWindow([azimuth], 48).sunWindow).not.toBe('all_day');
    }
  });

  it('the southern hemisphere mirrors north and south', () => {
    expect(contribution(0, -35)).toBe('midday');
    expect(contribution(180, -35)).toBeNull();
  });

  it('the sectors are half-open like orientation_from_aspect', () => {
    expect(orientationFromAzimuth(22.5)).toBe('northeast');
    expect(orientationFromAzimuth(337.5)).toBe('north');
    expect(orientationFromAzimuth(-45)).toBe('northwest');
    expect(() => orientationFromAzimuth(Number.NaN)).toThrow(RangeError);
  });

  it('the rounding wraps 360 to 0', () => {
    expect(roundAzimuth(359.96)).toBe(0);
    expect(roundAzimuth(-0.04)).toBe(0);
    expect(roundAzimuth(-45)).toBe(315);
  });

  it('a point has no direction', () => {
    expect(windowFacing({ kind: 'point', origin: [1, 1] }, 0)).toBeNull();
  });
});
