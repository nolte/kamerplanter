import { describe, expect, it } from 'vitest';
import { isPhantomTouch, panIntoView, twoFingerStep } from './touchGestures';

describe('isPhantomTouch', () => {
  it('accepts the first fingertip', () => {
    expect(isPhantomTouch({ timeStamp: 100, width: 20, height: 20 }, null, 0)).toBe(false);
  });
  it('ignores a palm-sized contact patch', () => {
    expect(isPhantomTouch({ timeStamp: 100, width: 90, height: 20 }, null, 0)).toBe(true);
  });
  it('ignores a second touch within 50 ms of the first and accepts one a bit later', () => {
    expect(isPhantomTouch({ timeStamp: 130 }, 100, 1)).toBe(true);
    expect(isPhantomTouch({ timeStamp: 160 }, 100, 1)).toBe(false);
  });
  it('does not count a stale first-down time when no finger is down', () => {
    expect(isPhantomTouch({ timeStamp: 110 }, 100, 0)).toBe(false);
  });
});

describe('twoFingerStep', () => {
  it('pans with the midpoint and does not zoom for a parallel move', () => {
    const step = twoFingerStep(
      [
        [0, 0],
        [10, 0],
      ],
      [
        [5, 5],
        [15, 5],
      ],
    );
    expect(step.pan).toEqual([5, 5]);
    expect(step.zoom).toBe(1);
  });
  it('zooms with the spread of the fingers', () => {
    expect(
      twoFingerStep(
        [
          [0, 0],
          [10, 0],
        ],
        [
          [-5, 0],
          [15, 0],
        ],
      ).zoom,
    ).toBe(2);
    expect(
      twoFingerStep(
        [
          [0, 0],
          [10, 0],
        ],
        [
          [2, 0],
          [7, 0],
        ],
      ).zoom,
    ).toBe(0.5);
  });
  it('does not divide by zero for fingers on the same spot', () => {
    expect(
      twoFingerStep(
        [
          [3, 3],
          [3, 3],
        ],
        [
          [3, 3],
          [9, 3],
        ],
      ).zoom,
    ).toBe(1);
  });
});

describe('panIntoView', () => {
  it('leaves a visible object alone', () => {
    expect(panIntoView(100, 200, 400)).toBe(0);
  });
  it('lifts an object hidden by the sheet above it', () => {
    expect(panIntoView(300, 380, 360)).toBe(360 - 16 - 380);
  });
  it('pulls one that is above the top edge back down', () => {
    expect(panIntoView(-40, 20, 400)).toBe(16 + 40);
  });
  it('aligns the top edge for an object taller than the free area', () => {
    expect(panIntoView(100, 900, 400)).toBe(16 - 100);
  });
});
