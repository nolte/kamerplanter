import { describe, expect, it } from 'vitest';
import type { Point } from '../model/types';
import { DIMENSION_GAP_PX, labelAnchor, labelAnchorBelow, placeDimensionLabel } from './dimensions';
import { HANDLE_VISIBLE_PX } from './tools/handles';

/** The text's box as `placeDimensionLabel` sees it: 12 px font, 0.62 em glyphs, a quarter em below the baseline. */
function textBox([x, baseline]: Point, text: string): [number, number, number, number] {
  const half = (text.length * 12 * 0.62) / 2;
  return [x - half, baseline - 12, x + half, baseline + 3];
}

function clearOf(box: [number, number, number, number], handles: readonly Point[]): boolean {
  const half = HANDLE_VISIBLE_PX / 2;
  return handles.every(([x, y]) => box[2] <= x - half || box[0] >= x + half || box[3] <= y - half || box[1] >= y + half);
}

const TEXT = '2.00 m × 1.00 m · 2.00 m²';

describe('placeDimensionLabel (GP-UX-047: outside above the edge, clear of handles)', () => {
  it('stands just above the top edge when no handle is near', () => {
    const at = placeDimensionLabel({
      topPx: [300, 200],
      bottomPx: [300, 280],
      text: TEXT,
      fontPx: 12,
      handlesPx: [],
      handleSizePx: HANDLE_VISIBLE_PX,
      heightPx: 600,
    });
    expect(at).toEqual([300, 200 - DIMENSION_GAP_PX]);
  });

  it('moves past the edge handle and the rotate handle of a selected rect', () => {
    // A 300 x 200 px rect: corners, edge midpoints and the rotate handle 32 px above the top edge.
    const handles: Point[] = [
      [150, 200],
      [300, 200],
      [450, 200],
      [450, 300],
      [450, 400],
      [300, 400],
      [150, 400],
      [150, 300],
      [300, 168],
    ];
    const at = placeDimensionLabel({
      topPx: [300, 200],
      bottomPx: [300, 400],
      text: TEXT,
      fontPx: 12,
      handlesPx: handles,
      handleSizePx: HANDLE_VISIBLE_PX,
      heightPx: 600,
    });
    const box = textBox(at, TEXT);
    expect(clearOf(box, handles)).toBe(true);
    expect(box[3]).toBeLessThanOrEqual(168 - HANDLE_VISIBLE_PX / 2); // above the rotate handle, outside the shape
    expect(at[0]).toBe(300);
  });

  it('goes below the shape when there is no room above it on the canvas', () => {
    const handles: Point[] = [[300, 10]];
    const at = placeDimensionLabel({
      topPx: [300, 10],
      bottomPx: [300, 120],
      text: TEXT,
      fontPx: 12,
      handlesPx: handles,
      handleSizePx: HANDLE_VISIBLE_PX,
      heightPx: 600,
    });
    expect(at[1] - 12).toBeGreaterThanOrEqual(120); // below the bottom edge
    expect(clearOf(textBox(at, TEXT), handles)).toBe(true);
  });

  it('stays on the canvas when the shape is taller than it', () => {
    const at = placeDimensionLabel({
      topPx: [300, -50],
      bottomPx: [300, 900],
      text: TEXT,
      fontPx: 12,
      handlesPx: [],
      handleSizePx: HANDLE_VISIBLE_PX,
      heightPx: 600,
    });
    expect(at[1] - 12).toBeGreaterThanOrEqual(0);
    expect(at[1]).toBeLessThanOrEqual(600);
  });
});

describe('labelAnchor / labelAnchorBelow', () => {
  it('names the middle of the top and the bottom edge of a shape', () => {
    const shape = {
      kind: 'vertices' as const,
      closed: true,
      vertices: [
        [1, 1],
        [3, 1],
        [3, 2],
        [1, 2],
      ] as Point[],
    };
    expect(labelAnchor(shape)).toEqual([2, 2]);
    expect(labelAnchorBelow(shape)).toEqual([2, 1]);
  });

  it('takes the top and the bottom of a circle', () => {
    const circle = { kind: 'circle' as const, center: [5, 5] as Point, radiusM: 1 };
    expect(labelAnchor(circle)).toEqual([5, 6]);
    expect(labelAnchorBelow(circle)).toEqual([5, 4]);
  });
});
