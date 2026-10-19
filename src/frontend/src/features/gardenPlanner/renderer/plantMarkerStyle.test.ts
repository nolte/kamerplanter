import { describe, expect, it } from 'vitest';
import { ATTENTION_PRIORITY, LIFECYCLES } from '../model/plantState';
import { BADGE_OUTLINE, BADGE_STYLES, RING_STYLES } from './plantMarkerStyle';

/**
 * GP-ACC-052: the five states (planned, sown, active, harvesting, failed) stay apart in greyscale and for
 * red-green weakness. The proof is structural - no two share a ring signature, no two badges share an outline
 * - plus the contrast of every badge against its white outline (WCAG 1.4.11, GP-UX-062).
 */

function luminance(hex: string): number {
  const channel = (offset: number) => {
    const value = parseInt(hex.slice(offset, offset + 2), 16) / 255;
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  }
  return 0.2126 * channel(1) + 0.7152 * channel(3) + 0.0722 * channel(5);
}

function contrast(a: string, b: string): number {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (light + 0.05) / (dark + 0.05);
}

describe('ring styles', () => {
  it('give every lifecycle its own ring signature, independent of colour', () => {
    const signature = (lifecycle: (typeof LIFECYCLES)[number]) => {
      const ring = RING_STYLES[lifecycle];
      return JSON.stringify([ring.dash, ring.double, ring.seeds, ring.cross, ring.discOpacity]);
    };
    const signatures = LIFECYCLES.map(signature);
    expect(new Set(signatures).size).toBe(LIFECYCLES.length);
  });

  it('draws a failed plant as a cross on an empty ring, never as a filled disc', () => {
    expect(RING_STYLES.failed.cross).toBe(true);
    expect(RING_STYLES.failed.discOpacity).toBe(0);
  });
});

describe('badge styles', () => {
  it('give every reason its own outline and shape', () => {
    const outlines = ATTENTION_PRIORITY.map((code) => BADGE_STYLES[code].outline);
    const shapes = ATTENTION_PRIORITY.map((code) => BADGE_STYLES[code].shape);
    expect(new Set(outlines).size).toBe(ATTENTION_PRIORITY.length);
    expect(new Set(shapes).size).toBe(ATTENTION_PRIORITY.length);
  });

  it.each(ATTENTION_PRIORITY.map((code) => [code] as const))(
    'keeps %s at least 3:1 against its white outline (light and dark plan)',
    (code) => {
      expect(contrast(BADGE_STYLES[code].fill, BADGE_OUTLINE)).toBeGreaterThanOrEqual(3);
    },
  );

  it('keeps the fills apart in greyscale where the shape does not decide (red/green weakness)', () => {
    // Luminance, not hue: the badge shape differs anyway, but no two fills may collapse to one grey.
    const greys = ATTENTION_PRIORITY.map((code) => Math.round(luminance(BADGE_STYLES[code].fill) * 100));
    expect(new Set(greys).size).toBeGreaterThanOrEqual(4);
  });
});
