import { describe, expect, it } from 'vitest';
import { parseGeometry } from './geometry';
import type { Geometry } from './types';
import { bedAxis, oppositeOrientation, orientationFromAxis } from './bedOrientation';
import { loadVectors } from '@/test/gardenPlanVectors';

/**
 * The TypeScript port of the bed axis runs against the same vector file as the Python reference
 * (`tests/unit/domain/calculators/test_orientation_vectors.py`, REQ-053 GP-FR-017, §19.6). A test that copied the
 * cases inline would certify nothing.
 */
const VECTORS = loadVectors();
const AXIS_CASES = VECTORS.cases.filter((vector) => vector.operation === 'bed_axis');

interface AxisInput {
  geometry: unknown;
  north_angle_deg: number;
}

function parseOrThrow(raw: unknown, id: string): Geometry {
  const geometry = parseGeometry(raw);
  if (geometry === null) throw new Error(`vector geometry does not parse: ${id}`);
  return geometry;
}

describe('bed axis vectors (shared with the Python reference)', () => {
  it('the operation is documented and has cases', () => {
    expect(VECTORS.operations).toHaveProperty('bed_axis');
    expect(AXIS_CASES.length).toBeGreaterThanOrEqual(10);
  });

  it.each(AXIS_CASES.map((vector) => [vector.id, vector] as const))('%s', (_id, vector) => {
    const input = vector.input as unknown as AxisInput;
    const axis = bedAxis(parseOrThrow(input.geometry, vector.id), input.north_angle_deg);
    const actual =
      axis === null ? null : { azimuth_deg: axis.azimuthDeg, orientation: axis.orientation };
    expect(actual, vector.spec).toEqual(vector.expected);
  });
});

describe('bed axis rules (independent of the vector file)', () => {
  const longY: Geometry = {
    kind: 'rect',
    origin: [1, 1],
    width_m: 1,
    length_m: 4,
    rotation_deg: 0,
  };

  it('half a turn changes nothing: an axis has two ends', () => {
    for (const rotation of [0, 37, 90, 180, 271.5]) {
      const turned = bedAxis({ ...longY, rotation_deg: rotation }, 12);
      const opposite = bedAxis({ ...longY, rotation_deg: (rotation + 180) % 360 }, 12);
      expect(turned).toEqual(opposite);
    }
  });

  it('only the four ends between north and southeast name an axis', () => {
    const names = new Set<string>();
    for (let degree = 0; degree < 360; degree += 1) names.add(orientationFromAxis(degree));
    expect([...names].sort()).toEqual(['east', 'north', 'northeast', 'southeast']);
  });

  it('a circle has no axis', () => {
    expect(bedAxis({ kind: 'circle', origin: [5, 5], radius_m: 2 }, 0)).toBeNull();
  });

  it('names the other end of an axis', () => {
    expect(oppositeOrientation('north')).toBe('south');
    expect(oppositeOrientation('southeast')).toBe('northwest');
  });
});
