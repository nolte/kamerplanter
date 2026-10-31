import { describe, expect, it } from 'vitest';
import type { Geometry } from '../model/types';
import { fitLabel, labelAnchorOf, labelChars, resolveLabelCollisions, type LabelCandidate } from './labelLayout';

function candidate(key: string, x: number, y: number, weight: number, order: number, text = 'Beet'): LabelCandidate {
  return { key, text, x, y, withIcon: false, weight, order };
}

describe('resolveLabelCollisions (GP-UX-047)', () => {
  // 100 px/m, 12 px font: "Beet" is 4 x 7.2 = 28.8 px wide and 14.4 px high
  it('keeps both labels when they do not overlap', () => {
    const kept = resolveLabelCollisions([candidate('a', 1, 1, 2, 0), candidate('b', 2, 1, 1, 1)], 100, 12);
    expect([...kept].sort()).toEqual(['a', 'b']);
  });

  it('lets the larger object keep its name when two labels overlap, whatever the paint order', () => {
    const small = candidate('small', 1, 1, 1, 0);
    const large = candidate('large', 1.1, 1.05, 6, 1);
    expect([...resolveLabelCollisions([small, large], 100, 12)]).toEqual(['large']);
    expect([...resolveLabelCollisions([large, small], 100, 12)]).toEqual(['large']);
  });

  it('resolves equal sizes by paint order, so the same data gives the same picture (GP-FR-003)', () => {
    const first = candidate('first', 1, 1, 2, 0);
    const second = candidate('second', 1.1, 1, 2, 1);
    expect([...resolveLabelCollisions([second, first], 100, 12)]).toEqual(['first']);
  });

  it('takes the box of a name with its type icon as drawn: the name moves below the anchor', () => {
    // 20 px apart: two plain labels (14.4 px high) pass; with the icon the upper name drops 6.8 px onto the lower one
    const lower = candidate('lower', 1, 1, 1, 1);
    const upper = candidate('upper', 1, 1.2, 2, 0);
    expect(resolveLabelCollisions([lower, upper], 100, 12).size).toBe(2);
    expect([...resolveLabelCollisions([lower, { ...upper, withIcon: true }], 100, 12)]).toEqual(['upper']);
  });

  it('separates labels that only touch', () => {
    // exactly one label width (28.8 px) apart
    const kept = resolveLabelCollisions([candidate('a', 1, 1, 2, 0), candidate('b', 1.288, 1, 1, 1)], 100, 12);
    expect(kept.size).toBe(2);
  });
});

describe('fitLabel', () => {
  const lShape: Geometry = {
    kind: 'polygon',
    points: [
      [2, 2],
      [8, 2],
      [8, 3.2],
      [3.2, 3.2],
      [3.2, 6],
      [2, 6],
    ],
    rotation_deg: 0,
  };

  it('shortens a name to the room at the anchor, not to the bounding box', () => {
    // room 1.406 m at 50 px/m = 70 px -> 9 characters of 7.2 px; the 6 m box would hold 41
    const name = 'Staudenbeet am Gartenzaun';
    expect(labelChars(1.406 * 50, 12)).toBe(9);
    expect(fitLabel(name, lShape, 50, 12)).toBe('Staudenb…');
  });

  it('keeps a name that fits', () => {
    expect(fitLabel('Winkel', lShape, 50, 12)).toBe('Winkel');
  });

  it('caches the anchor per geometry object', () => {
    expect(labelAnchorOf(lShape)).toBe(labelAnchorOf(lShape));
  });
});
