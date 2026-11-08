import { describe, expect, it } from 'vitest';
import { zoomAround, type ZoomView } from '../model/units';
import { commitOf, cssTransform, layerTransform } from './wheelZoom';

const START: ZoomView = { originM: [2, 30], pxPerM: 40 };

describe('coalesced wheel zoom (GP-NFR-034)', () => {
  it('commits a burst around changing pointers as the one zoom the route reproduces', () => {
    let pending = START;
    for (const [factor, anchor] of [
      [1.2, [100, 200]],
      [1.2, [300, 50]],
      [0.9, [420, 380]],
    ] as const) {
      pending = zoomAround(pending, pending.pxPerM * factor, [anchor[0], anchor[1]], 1);
    }
    const step = commitOf(START, pending);
    expect(step?.kind).toBe('zoom');
    if (step?.kind !== 'zoom') return;
    const committed = zoomAround(START, step.pxPerM, step.anchorPx, 1);
    expect(committed.pxPerM).toBeCloseTo(pending.pxPerM, 9);
    expect(committed.originM[0]).toBeCloseTo(pending.originM[0], 9);
    expect(committed.originM[1]).toBeCloseTo(pending.originM[1], 9);
  });

  it('maps each drawn point to where the pending view draws it', () => {
    const pending = zoomAround(START, 60, [250, 150], 1);
    const t = layerTransform(START, pending);
    const model: [number, number] = [7, 25];
    const before: [number, number] = [(model[0] - START.originM[0]) * 40, (START.originM[1] - model[1]) * 40];
    const after: [number, number] = [(model[0] - pending.originM[0]) * 60, (pending.originM[1] - model[1]) * 60];
    expect(before[0] * t.scale + t.txPx).toBeCloseTo(after[0], 9);
    expect(before[1] * t.scale + t.tyPx).toBeCloseTo(after[1], 9);
    expect(cssTransform(t)).toMatch(/^translate\(.+px, .+px\) scale\(1\.5\)$/);
  });

  it('commits a burst that came back to its scale as the pan that remains, and nothing for no change', () => {
    const there = zoomAround(START, 80, [100, 100], 1);
    const back = zoomAround(there, 40, [300, 300], 1);
    expect(commitOf(START, back)?.kind).toBe('pan');
    expect(commitOf(START, START)).toBeNull();
  });
});
