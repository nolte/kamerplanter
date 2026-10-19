import { describe, expect, it } from 'vitest';
import { familyColors, hueOf } from './familyColor';

const FAMILIES = [
  'Solanaceae',
  'Fabaceae',
  'Brassicaceae',
  'Apiaceae',
  'Amaranthaceae',
  'Cucurbitaceae',
  'Asteraceae',
  'Amaryllidaceae',
  'Poaceae',
  'Lamiaceae',
  'Rosaceae',
  'Polygonaceae',
];

describe('familyColors', () => {
  it('gives every family one colour, whatever the order it is asked in', () => {
    const forward = familyColors(FAMILIES);
    const backward = familyColors([...FAMILIES].reverse());
    expect(forward.size).toBe(FAMILIES.length);
    for (const family of FAMILIES) expect(backward.get(family)).toBe(forward.get(family));
  });

  it('counts a family named twice once', () => {
    expect(familyColors(['a', 'b', 'a', 'b']).size).toBe(2);
  });

  it('separates up to twelve families by at least 15 degrees of hue', () => {
    const hues = [...familyColors(FAMILIES).values()].map(hueOf);
    for (let a = 0; a < hues.length; a += 1) {
      for (let b = a + 1; b < hues.length; b += 1) {
        const gap = Math.abs(hues[a] - hues[b]);
        expect(Math.min(gap, 360 - gap), `${a} vs ${b}`).toBeGreaterThanOrEqual(15);
      }
    }
  });

  it('keeps the hue on the colour wheel and answers an empty set with nothing', () => {
    for (const color of familyColors(FAMILIES).values()) {
      expect(hueOf(color)).toBeGreaterThanOrEqual(0);
      expect(hueOf(color)).toBeLessThan(360);
    }
    expect(familyColors([]).size).toBe(0);
  });
});
