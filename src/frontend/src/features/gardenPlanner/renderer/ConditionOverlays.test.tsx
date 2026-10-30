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

  it('lines the glyphs of the three layers up along the bottom edge, one place per layer', () => {
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

type Box = [left: number, top: number, right: number, bottom: number];

/** The glyph's round backdrop (r 7.5 around 6 in a 12-unit box), read from its transform. */
function glyphBox(glyph: Element): Box {
  const match = /translate\(([-\d.]+) ([-\d.]+)\) scale\(([-\d.]+)\)/.exec(glyph.getAttribute('transform') ?? '');
  if (!match) throw new Error('glyph without transform');
  const [x, y, scale] = match.slice(1).map(Number);
  return [x - 1.5 * scale, y - 1.5 * scale, x + 13.5 * scale, y + 13.5 * scale];
}

function badgeBox(svg: SVGSVGElement): Box {
  const rect = svg.querySelector('[data-plan-badge] rect') as SVGRectElement;
  const [x, y, w, h] = ['x', 'y', 'width', 'height'].map((name) => Number(rect.getAttribute(name)));
  return [x, y, x + w, y + h];
}

/** Generous on purpose: a digit is at most 0.7 em wide, the halo adds its stroke, ascent 1 em, descent 0.25 em. */
function zoneNumberBox(svg: SVGSVGElement): Box {
  const text = svg.querySelector('[data-zone-number]') as SVGTextElement;
  const [x, y, size, halo] = ['x', 'y', 'font-size', 'stroke-width'].map((name) => Number(text.getAttribute(name)));
  const width = (text.textContent ?? '').length * size * 0.7;
  return [x - halo, y - size - halo, x + width + halo, y + size * 0.25 + halo];
}

const intersects = (a: Box, b: Box): boolean => a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3];

const ALL_THREE: Partial<PlanLocation> = {
  site_conditions: { sun_profile: { sun_window: 'midday' }, microclimate: { frost_risk: 'high' } },
  soil_profile: { drainage: 'poor' },
};

describe('glyph placement (badge, zone number, three layers on one bed)', () => {
  const layersOn = (bedKey: string): Partial<RenderOptions> => ({
    sunLayer: true,
    moistureLayer: true,
    frostLayer: true,
    zoneLayer: [{ key: 'z1', color: '#2E7D32', variant: 11, locationKeys: [bedKey] }],
  });

  it('keeps every glyph clear of the task badge, the zone number and the other glyphs', () => {
    // The widest badge ("99+") and a two-digit zone number on a 1.2 m x 2 m bed at 60 px/m (72 x 120 px).
    const svg = mount(layersOn('busy'), [bed('busy', 0, 0, { ...ALL_THREE, open_task_count: 120, overdue_task_count: 1 })]);
    const glyphs = [...svg.querySelectorAll('[data-condition-glyph]')].map(glyphBox);
    expect(glyphs).toHaveLength(3);
    const badge = badgeBox(svg);
    const zone = zoneNumberBox(svg);
    expect(svg.querySelector('[data-zone-number]')?.textContent).toBe('12');
    for (const glyph of glyphs) {
      expect(intersects(glyph, badge)).toBe(false);
      expect(intersects(glyph, zone)).toBe(false);
    }
    for (let i = 0; i < glyphs.length; i += 1) {
      for (let j = i + 1; j < glyphs.length; j += 1) expect(intersects(glyphs[i], glyphs[j])).toBe(false);
    }
    // The measuring stick: the badge's own box does hit the place the sun glyph used to take (top-right).
    // (The bed's top-right corner is (1.2, -2) in drawing coordinates; the glyph sat 4 px inside it, 14 px wide.)
    const formerSun: Box = [1.2 - 18 / 60, -2 + 4 / 60, 1.2 - 4 / 60, -2 + 18 / 60];
    expect(intersects(formerSun, badge)).toBe(true);
  });

  it('leaves the glyphs out where the bed is too short for them below the badge band; the pattern stays', () => {
    // 2 m wide, 0.6 m deep at 60 px/m: 36 px, less than the 24 px band plus a glyph row.
    const short = bed('short', 0, 0, {
      ...ALL_THREE,
      geometry: { kind: 'rect', origin: [0, 0], width_m: 2, length_m: 0.6, rotation_deg: 0 },
      bbox: [0, 0, 2, 0.6],
    });
    const svg = mount({ sunLayer: true, moistureLayer: true, frostLayer: true }, [short]);
    expect(svg.querySelectorAll('[data-condition-bed]')).toHaveLength(3);
    expect(svg.querySelector('[data-condition-glyph]')).toBeNull();
  });

  it('puts the glyphs of a circular bed inside the circle and clear of the badge on its rim', () => {
    // Radius 1 m at 60 px/m: the bounding-box corners lie 25 px outside the rim.
    const circle = bed('round', 1, 1, {
      ...ALL_THREE,
      open_task_count: 120,
      overdue_task_count: 0,
      geometry: { kind: 'circle', origin: [3, 3], radius_m: 1 },
      bbox: [2, 2, 4, 4],
    });
    const svg = mount(layersOn('round'), [circle]);
    const glyphs = [...svg.querySelectorAll('[data-condition-glyph]')].map(glyphBox);
    expect(glyphs).toHaveLength(3);
    const badge = badgeBox(svg);
    for (const [left, top, right, bottom] of glyphs) {
      for (const [x, y] of [
        [left, top],
        [right, top],
        [left, bottom],
        [right, bottom],
      ]) {
        expect(Math.hypot(x - 3, y + 3)).toBeLessThanOrEqual(1);
      }
      expect(intersects([left, top, right, bottom], badge)).toBe(false);
    }
  });

  it('leaves the glyphs out of a circle too small to hold the row inside its rim', () => {
    // Radius 0.5 m at 60 px/m = 30 px: wide enough for a label (60 px), too small for three glyphs.
    const small = bed('small', 0, 0, {
      ...ALL_THREE,
      geometry: { kind: 'circle', origin: [0.5, 0.5], radius_m: 0.5 },
      bbox: [0, 0, 1, 1],
    });
    const svg = mount({ sunLayer: true, moistureLayer: true, frostLayer: true }, [small]);
    expect(svg.querySelectorAll('[data-condition-bed]')).toHaveLength(3);
    expect(svg.querySelector('[data-condition-glyph]')).toBeNull();
  });
});

/**
 * A pattern tile's geometry without its colour: paint becomes "ink" (or stays "none"), line width and dot radius
 * go (a fatter dot is still a dot), and every length is divided by the tile, so a layer's tile size does not make
 * two equal pictures look different.
 */
function tileGeometry(pattern: Element): string {
  const tile = Number(pattern.getAttribute('width'));
  const body = pattern.innerHTML
    .replace(/ (stroke|fill)="(?!none")[^"]*"/g, ' $1="ink"')
    .replace(/ (stroke-width|fill-opacity|stroke-opacity|opacity|r)="[^"]*"/g, '')
    .replace(/(?<![a-z])-?\d+(?:\.\d+)?/g, (n) => String(Number((Number(n) / tile).toFixed(2))));
  return `${pattern.getAttribute('patternTransform') ?? ''}|${body}`;
}

describe('patterns across the whole plan (WCAG 1.4.1)', () => {
  it('gives every tile of every layer - zones, last watered, sun, moisture, frost - a geometry of its own', () => {
    const svg = mount({
      sunLayer: true,
      moistureLayer: true,
      frostLayer: true,
      zoneLayer: [0, 1, 2, 3].map((variant) => ({
        key: `z${variant}`,
        color: '#2E7D32',
        variant,
        locationKeys: ['plain'],
      })),
      wateredLayer: { byBed: { plain: { days: 1, wateredClass: 'd0_1' } }, label: (days) => `${days}` },
    });
    const patterns = [...svg.querySelectorAll('pattern')];
    // 4 zone hatchings, 4 watered classes, 5 sun windows, 3 drainage and 3 frost values.
    expect(patterns).toHaveLength(19);
    const families = patterns.map((pattern) => pattern.getAttribute('data-pattern-family'));
    expect(families.every(Boolean)).toBe(true);
    expect(new Set(families).size).toBe(patterns.length);
    const geometries = patterns.map(tileGeometry);
    const seen = new Map<string, string>();
    for (const [i, geometry] of geometries.entries()) {
      const id = patterns[i].getAttribute('id') ?? '';
      expect(seen.get(geometry), `${id} draws the same tile as ${seen.get(geometry)}`).toBeUndefined();
      seen.set(geometry, id);
    }
  });

  it('the measuring stick: the former sun "rising" and watered "diagonal" tiles count as one geometry', () => {
    const tile = (width: number, body: string) => {
      const node = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
      node.setAttribute('width', String(width));
      node.innerHTML = body;
      return node;
    };
    // Same stroke, different colour, line width and tile size: the same picture.
    const rising = tile(10, '<path d="M0 10L10 0" stroke="#e65100" stroke-width="1.4" fill="none"></path>');
    const diagonal = tile(8, '<path d="M0 8L8 0" stroke="#01579b" stroke-width="1.6" fill="none"></path>');
    expect(tileGeometry(rising)).toBe(tileGeometry(diagonal));
    // And the former moisture "drops" and watered "dots" (a centred dot, radius aside).
    const drops = tile(10, '<circle cx="5" cy="5" r="1.4" fill="#01579b"></circle>');
    const dots = tile(10, '<circle cx="5" cy="5" r="2.24" fill="#01579b"></circle>');
    expect(tileGeometry(drops)).toBe(tileGeometry(dots));
  });
});
