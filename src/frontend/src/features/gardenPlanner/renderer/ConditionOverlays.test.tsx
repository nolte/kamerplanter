import { render } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import { smallPlan } from '@/test/gardenPlanFixtures';
import type { PlanLocation } from '../model/types';
import { CONDITION_SPECS, FROST_CONDITION, MOISTURE_CONDITION, SUN_CONDITION } from './ConditionOverlays';
import { SvgPlanRenderer } from './SvgPlanRenderer';
import { NO_SELECTION, bed, options, viewportAt } from './rendererTestKit';
import type { RenderOptions } from './types';

/** The sun, moisture and frost layers of the plan (REQ-053 GP-FR-169, GP-FR-047, #2487). */
const theme = createTheme();
const wrap = (node: ReactNode) => <ThemeProvider theme={theme}>{node}</ThemeProvider>;

/** One bed per sun window, drainage and frost risk value, plus one bed that knows nothing. */
function beds(): PlanLocation[] {
  const sun = SUN_CONDITION.values.map((value, i) =>
    bed(`sun_${value}`, i * 3, 0, { site_conditions: { sun_profile: { sun_window: value } } }),
  );
  const moisture = MOISTURE_CONDITION.values.map((value, i) =>
    bed(`moist_${value}`, i * 3, 4, { soil_profile: { drainage: value } }),
  );
  const frost = FROST_CONDITION.values.map((value, i) =>
    bed(`frost_${value}`, i * 3, 8, { site_conditions: { microclimate: { frost_risk: value } } }),
  );
  return [...sun, ...moisture, ...frost, bed('plain', 12, 8)];
}

function mount(extra: Partial<RenderOptions>, locations: PlanLocation[] = beds()) {
  const model = smallPlan({ locations, garden_objects: [], slots: [], plants: [] });
  const view = render(
    wrap(new SvgPlanRenderer().render(model, viewportAt(-1, 12, 60), NO_SELECTION, options(extra))),
  );
  return view.container.querySelector('svg') as SVGSVGElement;
}

const LAYERS = [
  { spec: SUN_CONDITION, option: 'sunLayer', prefix: 'sun_' },
  { spec: MOISTURE_CONDITION, option: 'moistureLayer', prefix: 'moist_' },
  { spec: FROST_CONDITION, option: 'frostLayer', prefix: 'frost_' },
] as const;

describe('site-condition layers', () => {
  it('draws none of the three layers while they are off', () => {
    const svg = mount({});
    for (const { spec } of LAYERS) {
      expect(svg.querySelector(`[data-testid="garden-plan-${spec.id}-layer"]`)).toBeNull();
    }
    expect(svg.querySelector('[data-condition-bed]')).toBeNull();
  });

  it.each(LAYERS)('$spec.id: one pattern and one glyph per value, decorative only', ({ spec, option, prefix }) => {
    const svg = mount({ [option]: true });
    const layer = svg.querySelector(`[data-testid="garden-plan-${spec.id}-layer"]`) as SVGGElement;
    expect(layer).not.toBeNull();
    expect(layer.getAttribute('aria-hidden')).toBe('true');
    expect(layer.getAttribute('pointer-events')).toBe('none');
    expect(layer.querySelectorAll('pattern')).toHaveLength(spec.values.length);

    const drawn = [...layer.querySelectorAll('[data-condition-bed]')];
    // Exactly the beds of this layer, each with its own value; the other layers' beds and the plain bed get nothing.
    expect(drawn.map((node) => node.getAttribute('data-condition-bed'))).toEqual(
      spec.values.map((value) => `${prefix}${value}`),
    );
    for (const node of drawn) {
      const value = node.getAttribute('data-condition-value') as string;
      expect(node.querySelector('[fill]')?.getAttribute('fill')).toBe(`url(#gp-${spec.id}-${value})`);
      expect(node.querySelector(`[data-condition-glyph="${value}"]`)).not.toBeNull();
    }
  });

  it.each(LAYERS)('$spec.id: the values stay apart without colour (as GP-ACC-052)', ({ spec, option }) => {
    const svg = mount({ [option]: true });
    const layer = svg.querySelector(`[data-testid="garden-plan-${spec.id}-layer"]`) as SVGGElement;
    // Every value has a pattern family and a glyph of its own: one ink per layer, so shape is the only cue.
    const families = [...layer.querySelectorAll('pattern')].map((p) => p.getAttribute('data-condition-pattern'));
    expect(new Set(families).size).toBe(spec.values.length);
    const tiles = [...layer.querySelectorAll('pattern')].map((p) => p.innerHTML);
    expect(new Set(tiles).size).toBe(spec.values.length);
    const glyphs = [...layer.querySelectorAll('[data-condition-glyph]')].map((g) =>
      [...g.querySelectorAll('path')].map((path) => `${path.getAttribute('d')}|${path.getAttribute('fill')}`).join(';'),
    );
    expect(glyphs).toHaveLength(spec.values.length);
    expect(new Set(glyphs).size).toBe(spec.values.length);
    // One ink for all values of the layer: no meaning rests on a colour difference.
    const strokes = new Set(
      [...layer.querySelectorAll('[data-condition-glyph] path')].map((path) => path.getAttribute('stroke')),
    );
    expect(strokes.size).toBe(1);
  });

  it('never draws a value that is unknown', () => {
    const svg = mount({ sunLayer: true, moistureLayer: true, frostLayer: true }, [
      bed('u', 0, 0, {
        site_conditions: { sun_profile: { sun_window: 'unknown' }, microclimate: { frost_risk: 'unknown' } },
        soil_profile: { drainage: 'unknown' },
      }),
    ]);
    expect(svg.querySelectorAll('[data-condition-bed]')).toHaveLength(0);
  });

  it('puts the glyphs of the three layers in different corners of a bed', () => {
    const svg = mount({ sunLayer: true, moistureLayer: true, frostLayer: true }, [
      bed('all', 0, 0, {
        site_conditions: { sun_profile: { sun_window: 'midday' }, microclimate: { frost_risk: 'high' } },
        soil_profile: { drainage: 'poor' },
      }),
    ]);
    const transforms = [...svg.querySelectorAll('[data-condition-glyph]')].map((g) => g.getAttribute('transform'));
    expect(transforms).toHaveLength(3);
    expect(new Set(transforms).size).toBe(3);
  });

  it('keeps one spec per layer id', () => {
    expect(CONDITION_SPECS.map((spec) => spec.id)).toEqual(['sun', 'moisture', 'frost']);
  });
});
