import { render } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import { smallPlan } from '@/test/gardenPlanFixtures';
import { SvgPlanRenderer } from './SvgPlanRenderer';
import { NO_SELECTION, bed, options, viewportAt } from './rendererTestKit';
import type { RenderOptions } from './types';

/** The zone layer and the "last watered" layer of the plan (REQ-053 WP 7.6 / 7.7). */
const theme = createTheme();
const wrap = (node: ReactNode) => <ThemeProvider theme={theme}>{node}</ThemeProvider>;

function mount(extra: Partial<RenderOptions>) {
  const model = smallPlan({
    locations: [bed('loc_a', 1, 1), bed('loc_b', 4, 1)],
    garden_objects: [],
    slots: [],
    plants: [],
  });
  const view = render(
    wrap(new SvgPlanRenderer().render(model, viewportAt(0, 10, 60), NO_SELECTION, options(extra))),
  );
  return view.container.querySelector('svg') as SVGSVGElement;
}

describe('zone layer', () => {
  it('draws nothing while the layer is off', () => {
    const svg = mount({});
    expect(svg.querySelector('[data-testid="garden-plan-zone-layer"]')).toBeNull();
  });

  it('draws outline and hatching over the beds of a zone, decorative only', () => {
    const svg = mount({
      zoneLayer: [
        { key: 'z1', color: '#2E7D32', variant: 0, locationKeys: ['loc_a'] },
        { key: 'z2', color: '#1565C0', variant: 1, locationKeys: ['loc_b', 'loc_gone'] },
      ],
    });
    const layer = svg.querySelector('[data-testid="garden-plan-zone-layer"]') as SVGGElement;
    expect(layer.getAttribute('aria-hidden')).toBe('true');
    expect(layer.getAttribute('pointer-events')).toBe('none');
    // A hatching pattern per zone, and a bed that is not in the plan is skipped.
    expect(layer.querySelectorAll('pattern')).toHaveLength(2);
    expect(layer.querySelectorAll('[data-zone-bed]')).toHaveLength(2);
    // Never colour alone: the second zone is hatched at another angle and dashed.
    const angles = [...layer.querySelectorAll('pattern')].map((p) => p.getAttribute('patternTransform'));
    expect(new Set(angles).size).toBe(2);
    expect(layer.querySelector('[data-zone-key="z2"] [stroke-dasharray]')).not.toBeNull();
  });
});

describe('last watered layer', () => {
  it('words the bed as "days since" with a pattern per class', () => {
    const svg = mount({
      wateredLayer: {
        byBed: {
          loc_a: { days: 1, wateredClass: 'd0_1' },
          loc_b: { days: 9, wateredClass: 'd8plus' },
        },
        label: (days) => `${days} days since`,
      },
    });
    const layer = svg.querySelector('[data-testid="garden-plan-watered-layer"]') as SVGGElement;
    expect(layer.getAttribute('aria-hidden')).toBe('true');
    expect(layer.querySelectorAll('pattern')).toHaveLength(4);
    expect(layer.querySelector('[data-watered-bed="loc_a"]')?.getAttribute('data-watered-class')).toBe('d0_1');
    const texts = [...layer.querySelectorAll('text')].map((node) => node.textContent);
    expect(texts).toEqual(['1 days since', '9 days since']);
    expect(layer.textContent ?? '').not.toMatch(/needs? water/i);
  });
});
