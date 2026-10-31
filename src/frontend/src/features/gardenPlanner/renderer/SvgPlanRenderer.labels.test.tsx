import { render } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';
import type { PlanLocation, PlanPlant, PlanSlot } from '../model/types';
import { SvgPlanRenderer } from './SvgPlanRenderer';
import { NO_SELECTION, bed, normalizePlan, options, planResponse, viewportAt } from './rendererTestKit';
import type { RenderOptions, RenderSelection, Viewport } from './types';

/**
 * Names on the drawn plan (REQ-053 GP-UX-047, GP-NFR-067, #2490) - and the component half of TC-053-040 ("Zoom und
 * Beschriftung in der Übersicht"): the browser case is not automated; these assertions read the same DOM a user sees.
 */
const theme = createTheme();
const wrap = (node: ReactNode) => <ThemeProvider theme={theme}>{node}</ThemeProvider>;

function mount(
  model: ReturnType<typeof normalizePlan>,
  viewport: Viewport,
  selection: RenderSelection = NO_SELECTION,
  extra: Partial<RenderOptions> = {},
) {
  const view = render(wrap(new SvgPlanRenderer().render(model, viewport, selection, options(extra))));
  return view.container.querySelector('svg') as SVGSVGElement;
}

const label = (svg: SVGSVGElement, key: string) => svg.querySelector(`[data-testid="garden-plan-label-${key}"]`);

const L_SHAPE: PlanLocation = bed('l', 2, 2, {
  name: 'Winkelbeet',
  geometry: {
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
  },
  bbox: [2, 2, 8, 6],
  area_m2: 10.56,
});

describe('SvgPlanRenderer - label placement (GP-UX-047)', () => {
  it('draws the name of an L-shaped bed at its pole, inside the bed', () => {
    const svg = mount(normalizePlan(planResponse({ plan: null, locations: [L_SHAPE], garden_objects: [] })), viewportAt(0, 10, 100));
    const text = label(svg, 'l');
    expect(text).toHaveTextContent('Winkelbeet');
    expect(text).toHaveAttribute('x', '2.703');
    // y is flipped and the baseline sits a third of the 0.12 m font below the anchor
    expect(text).toHaveAttribute('y', '-2.663');
  });

  it('prints the dimensions centred above the top edge of the selection', () => {
    const svg = mount(
      normalizePlan(planResponse({ plan: null, locations: [L_SHAPE], garden_objects: [] })),
      viewportAt(0, 10, 100),
      { selectedKeys: new Set(['l']) },
    );
    const size = [...svg.querySelectorAll('[data-plan-key="l"] text')].find((node) => !node.hasAttribute('data-testid'));
    expect(size).toHaveAttribute('x', '5'); // the box's middle, not the pole and not the centroid
    expect(Number(size?.getAttribute('y'))).toBeLessThan(-6); // above y = 6, the top edge
  });

  it('leaves the dimensions to the editor overlay when asked', () => {
    const svg = mount(
      normalizePlan(planResponse({ plan: null, locations: [L_SHAPE], garden_objects: [] })),
      viewportAt(0, 10, 100),
      { selectedKeys: new Set(['l']) },
      { dimensionsOnOverlay: true },
    );
    expect(svg.querySelectorAll('[data-plan-key="l"] text')).toHaveLength(1); // the name only
  });
});

/**
 * TC-053-040 preconditions: a 28 x 20 m plan with 12 beds of 20 plants each, one of them very narrow. Beds of
 * 4 x 1.2 m in a 4 x 3 grid; bed 12 is 0.4 m wide.
 */
function overviewPlan() {
  const locations: PlanLocation[] = [];
  const slots: PlanSlot[] = [];
  const plants: PlanPlant[] = [];
  for (let index = 0; index < 12; index += 1) {
    const key = `bed${index + 1}`;
    const narrow = index === 11;
    const x = 1 + (index % 4) * 6.5;
    const y = 2 + Math.floor(index / 4) * 6;
    const width = narrow ? 0.4 : 4;
    const length = narrow ? 4 : 1.2;
    locations.push(
      bed(key, x, y, {
        name: narrow ? 'Schmales Kräuterband' : `Beet ${index + 1}`,
        geometry: { kind: 'rect', origin: [x, y], width_m: width, length_m: length, rotation_deg: 0 },
        bbox: [x, y, x + width, y + length],
        area_m2: width * length,
      }),
    );
    for (let p = 0; p < 20; p += 1) {
      const slotKey = `${key}_s${p}`;
      const px = narrow ? x + 0.2 : x + 0.1 + (p % 10) * 0.4;
      const py = narrow ? y + 0.1 + p * 0.2 : y + 0.3 + Math.floor(p / 10) * 0.6;
      slots.push({ key: slotKey, slot_id: `${key}_${p}`, location_key: key, plan_geometry: { origin: [px, py] } });
      plants.push({ key: `${key}_p${p}`, instance_id: `${key}-${p}`, species_key: 'sp', slot_key: slotKey });
    }
  }
  return normalizePlan(
    planResponse({
      plan: {
        boundary: { kind: 'rect', origin: [0, 0], width_m: 28, length_m: 20, rotation_deg: 0 },
        north_angle_deg: 0,
        default_grid_m: 0.1,
        adjacency_factor: 1.5,
        plan_revision: 1,
      },
      locations,
      garden_objects: [],
      slots,
      plants,
    }),
  );
}

describe('TC-053-040 - zoom and names in the overview (GP-NFR-067, GP-UX-047)', () => {
  const model = overviewPlan();
  // "An Fläche anpassen": 28 m on 840 px = 30 px/m; zoomed in: 100 px/m (100 %)
  const fitted = viewportAt(0, 20, 30, 840, 600);
  const zoomed = viewportAt(0, 20, 100, 2800, 2000);

  it('names every bed from 60 px of width in the overview, the narrow one not', () => {
    const svg = mount(model, fitted);
    for (let index = 1; index <= 11; index += 1) {
      expect(label(svg, `bed${index}`)).toHaveTextContent(`Beet ${index}`); // 4 m = 120 px
    }
    expect(label(svg, 'bed12')).toBeNull(); // 0.4 m = 12 px
  });

  it('shows the plants as a cluster with their count before there is room for them', () => {
    const svg = mount(model, fitted);
    // 0.4 m spacing at 30 px/m = 12 px: markers; the narrow bed's 0.2 m = 6 px: a cluster
    expect(svg.querySelector('[data-plan-cluster="bed12"]')).toHaveAttribute('aria-label', '20 plants');
    expect(svg.querySelector('[data-plan-markers="bed1"]')).not.toBeNull();
  });

  it('keeps the font size constant on screen while zooming in (12 px)', () => {
    const fontPx = (svg: SVGSVGElement, viewport: Viewport) =>
      Number(label(svg, 'bed1')?.getAttribute('font-size')) * viewport.pxPerM;
    expect(fontPx(mount(model, fitted), fitted)).toBeCloseTo(12, 2);
    expect(fontPx(mount(model, zoomed), zoomed)).toBeCloseTo(12, 2);
  });

  it('names the narrow bed once it is wide enough, shortened to its width', () => {
    // 0.4 m at 200 px/m = 80 px: 11 characters of 7.2 px
    const view = viewportAt(18, 16, 200, 1000, 1000);
    const svg = mount(model, view);
    expect(label(svg, 'bed12')).toHaveTextContent('Schmales K…');
  });

  it('prints dimensions only for the selected bed', () => {
    const svg = mount(model, fitted, { selectedKeys: new Set(['bed12']) });
    const sized = [...svg.querySelectorAll('[data-plan-key] text')].filter(
      (node) => !node.hasAttribute('data-testid') && node.closest('[data-plan-key]')?.getAttribute('data-plan-kind') === 'location',
    );
    expect(sized.map((node) => node.closest('[data-plan-key]')?.getAttribute('data-plan-key'))).toEqual(['bed12']);
  });
});
