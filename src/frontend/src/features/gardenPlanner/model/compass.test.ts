import { describe, expect, it } from 'vitest';
import {
  azimuthFromScreenOffset,
  azimuthToRotationDeg,
  normalizeAzimuth,
  northDirection,
  rotationToAzimuthDeg,
} from './compass';

describe('north angle vs rotation_deg (GP-FR-015)', () => {
  it('0 degrees north lies along +y, 90 along +x (clockwise compass azimuth)', () => {
    const [x0, y0] = northDirection(0);
    expect(x0).toBeCloseTo(0, 9);
    expect(y0).toBeCloseTo(1, 9);
    const [x90, y90] = northDirection(90);
    expect(x90).toBeCloseTo(1, 9);
    expect(y90).toBeCloseTo(0, 9);
    const [x180, y180] = northDirection(180);
    expect(x180).toBeCloseTo(0, 9);
    expect(y180).toBeCloseTo(-1, 9);
  });
  it('converts between azimuth and the counter-clockwise rotation', () => {
    expect(azimuthToRotationDeg(0)).toBe(90);
    expect(azimuthToRotationDeg(90)).toBe(0);
    expect(azimuthToRotationDeg(180)).toBe(270);
    expect(rotationToAzimuthDeg(90)).toBe(0);
    expect(rotationToAzimuthDeg(0)).toBe(90);
    for (const value of [0, 15, 90, 123.5, 271, 359]) {
      expect(rotationToAzimuthDeg(azimuthToRotationDeg(value))).toBeCloseTo(value, 9);
    }
  });
  it('the two conventions differ: the same number means opposite turns', () => {
    // rotation_deg 30 turns counter-clockwise, north_angle_deg 30 clockwise
    expect(azimuthToRotationDeg(30)).not.toBe(30);
    expect(rotationToAzimuthDeg(30)).toBe(60);
  });
});

describe('azimuthFromScreenOffset', () => {
  it('reads the bearing of a pointer from straight up, clockwise', () => {
    expect(azimuthFromScreenOffset(0, -10)).toBe(0); // up
    expect(azimuthFromScreenOffset(10, 0)).toBe(90); // right
    expect(azimuthFromScreenOffset(0, 10)).toBe(180); // down
    expect(azimuthFromScreenOffset(-10, 0)).toBe(270); // left
    expect(azimuthFromScreenOffset(10, -10)).toBe(45);
  });
});

describe('normalizeAzimuth', () => {
  it('wraps into 0..359.9 with one decimal', () => {
    expect(normalizeAzimuth(360)).toBe(0);
    expect(normalizeAzimuth(-15)).toBe(345);
    expect(normalizeAzimuth(359.96)).toBe(0);
    expect(normalizeAzimuth(12.34)).toBe(12.3);
    expect(normalizeAzimuth(725)).toBe(5);
  });
});
