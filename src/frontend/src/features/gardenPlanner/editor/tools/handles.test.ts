import { describe, expect, it } from 'vitest';
import type { Geometry } from '../../model/types';
import { computeHandles, handleAt } from './handles';

const rect = (w: number, l: number, rotation = 0): Geometry => ({
  kind: 'rect',
  origin: [0, 0],
  width_m: w,
  length_m: l,
  rotation_deg: rotation,
});

describe('computeHandles density (GP-UX-048)', () => {
  it('gives a large rect eight handles and a rotate handle 32 px outside the edge', () => {
    const set = computeHandles(rect(10, 4), 100);
    expect(set.density).toBe('full');
    expect(set.handles.filter((h) => h.kind === 'corner')).toHaveLength(4);
    expect(set.handles.filter((h) => h.kind === 'edge')).toHaveLength(4);
    const rotate = set.handles.find((h) => h.id === 'rotate');
    expect(rotate?.pointM).toEqual([5, 4.32]);
  });

  it('keeps only the corners (and rotate) below 3 x 48 px', () => {
    const set = computeHandles(rect(1.2, 1.2), 100); // 120 px
    expect(set.density).toBe('corners');
    expect(set.handles.map((h) => h.kind).sort()).toEqual([
      'corner',
      'corner',
      'corner',
      'corner',
      'rotate',
    ]);
  });

  it('has no handles below 2 x 48 px', () => {
    expect(computeHandles(rect(0.5, 4), 100)).toEqual({ density: 'none', handles: [] });
  });

  it('puts the rotate handle on the outside of a rotated rect', () => {
    const set = computeHandles(rect(10, 4, 90), 100);
    const rotate = set.handles.find((h) => h.id === 'rotate')!;
    // Local up points to -x after 90 degrees.
    expect(rotate.pointM[0]).toBeCloseTo(-4.32, 3);
    expect(rotate.pointM[1]).toBeCloseTo(5, 3);
  });

  it('gives a circle its radius handle on the east side', () => {
    const set = computeHandles({ kind: 'circle', origin: [2, 2], radius_m: 1 }, 100);
    expect(set.handles).toEqual([{ id: 'radius', kind: 'radius', pointM: [3, 2] }]);
    expect(computeHandles({ kind: 'circle', origin: [2, 2], radius_m: 0.3 }, 100).handles).toEqual(
      [],
    );
  });

  it('gives a polygon a handle per vertex, a "+" per long edge and a rotate handle', () => {
    const set = computeHandles(
      {
        kind: 'polygon',
        points: [
          [0, 0],
          [4, 0],
          [4, 4],
          [0, 4],
        ],
        rotation_deg: 0,
      },
      100,
    );
    expect(set.handles.filter((h) => h.kind === 'vertex')).toHaveLength(4);
    expect(set.handles.filter((h) => h.kind === 'midpoint')).toHaveLength(4);
    expect(set.handles.some((h) => h.kind === 'rotate')).toBe(true);
  });

  it('skips the "+" on an edge too short to hold it, and has no rotate for a polyline', () => {
    const short = computeHandles(
      {
        kind: 'polygon',
        points: [
          [0, 0],
          [0.2, 0],
          [4, 4],
        ],
        rotation_deg: 0,
      },
      100,
    );
    expect(short.handles.filter((h) => h.kind === 'midpoint').map((h) => h.id)).toEqual([
      'm1',
      'm2',
    ]);
    const line = computeHandles(
      {
        kind: 'polyline',
        points: [
          [0, 0],
          [4, 0],
        ],
        width_m: 0.3,
      },
      100,
    );
    expect(line.handles.map((h) => h.kind).sort()).toEqual(['midpoint', 'vertex', 'vertex']);
  });
});

describe('handleAt', () => {
  const toScreen = ([x, y]: [number, number]): [number, number] => [x * 100, 400 - y * 100];
  const handles = computeHandles(rect(10, 4), 100).handles;

  it('picks the handle whose 48 px area holds the pointer', () => {
    expect(handleAt(handles, toScreen, [3, 399])?.id).toBe('sw');
    expect(handleAt(handles, toScreen, [500, 400])?.id).toBe('s');
  });

  it('returns null away from every handle', () => {
    expect(handleAt(handles, toScreen, [300, 200])).toBeNull();
  });

  it('prefers a vertex over a "+" at the same distance', () => {
    const vertex = {
      id: 'v0',
      kind: 'vertex' as const,
      pointM: [1, 1] as [number, number],
      index: 0,
    };
    const mid = {
      id: 'm0',
      kind: 'midpoint' as const,
      pointM: [1, 1] as [number, number],
      index: 0,
    };
    expect(handleAt([mid, vertex], toScreen, [100, 300])?.id).toBe('v0');
  });
});
