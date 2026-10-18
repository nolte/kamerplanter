import { fireEvent, render } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { smallPlan } from '@/test/gardenPlanFixtures';
import { SvgPlanRenderer } from './SvgPlanRenderer';
import {
  NO_SELECTION,
  bed,
  gardenObject,
  largePlacedPlan,
  normalizePlan,
  options,
  plantedBed,
  planResponse,
  viewportAt,
} from './rendererTestKit';
import type { RenderSelection, Viewport } from './types';

const theme = createTheme();
const wrap = (node: ReactNode) => <ThemeProvider theme={theme}>{node}</ThemeProvider>;

function mount(
  renderer: SvgPlanRenderer,
  model = smallPlan(),
  viewport: Viewport = viewportAt(0, 10, 100),
  selection: RenderSelection = NO_SELECTION,
  opts = options(),
) {
  const view = render(wrap(renderer.render(model, viewport, selection, opts)));
  const svg = view.container.querySelector('svg') as SVGSVGElement;
  return { ...view, svg };
}

/** Every node that stands for an object, a group of markers or a cluster. */
const DOM_OBJECTS = '[data-plan-key], [data-plan-markers], [data-plan-cluster]';

describe('SvgPlanRenderer - structure', () => {
  it('draws the small plan (snapshot)', () => {
    const { svg } = mount(
      new SvgPlanRenderer(),
      smallPlan({
        garden_objects: [gardenObject('go_1', 6, 6)],
      }),
      viewportAt(0, 10, 100),
      { selectedKeys: new Set(['loc_a']) },
    );
    // Without the generated Emotion class name: it hashes the theme and would churn the snapshot.
    expect(svg.innerHTML.replace(/></g, '>\n<')).toMatchSnapshot();
    expect(svg.getAttribute('viewBox')).toBe('0 -10 10 10');
    expect(svg.getAttribute('width')).toBe('1000');
  });

  it('draws the cluster view of a dense bed (snapshot)', () => {
    const { slots, plants } = plantedBed('loc_a', 1, 1, 6, 0.1);
    const { svg } = mount(
      new SvgPlanRenderer(),
      smallPlan({ slots, plants, locations: [bed('loc_a', 1, 1)], garden_objects: [] }),
      viewportAt(0, 10, 100), // 0.1 m = 10 px: exactly the marker threshold
    );
    expect(svg.querySelector('[data-plan-markers="loc_a"] path')).toBeInTheDocument();
    expect(svg.querySelector('[data-plan-cluster]')).toBeNull();
    const dense = mount(
      new SvgPlanRenderer(),
      smallPlan({ slots, plants, locations: [bed('loc_a', 1, 1)], garden_objects: [] }),
      viewportAt(0, 10, 99),
    );
    expect(dense.svg.querySelector('[data-plan-cluster="loc_a"]')?.textContent).toBe('6');
    expect(dense.svg.innerHTML.replace(/></g, '>\n<')).toMatchSnapshot();
  });

  it('labels the surface and gives every object a name and one tab stop (GP-NFR-020/068)', () => {
    const { svg } = mount(new SvgPlanRenderer());
    expect(svg).toHaveAttribute('role', 'group');
    expect(svg).toHaveAttribute('aria-roledescription', 'Plan');
    const objects = [...svg.querySelectorAll<SVGGElement>('g[role="button"]')];
    expect(objects.map((g) => g.getAttribute('data-plan-key'))).toEqual([
      '__boundary__',
      'loc_a',
      'loc_b',
    ]);
    for (const g of objects) {
      expect(g.getAttribute('aria-label')).toBeTruthy();
      expect(g).toHaveAttribute('aria-pressed', 'false');
    }
    const stops = objects.filter((g) => g.getAttribute('tabindex') === '0');
    expect(stops.map((g) => g.getAttribute('data-plan-key'))).toEqual(['loc_a']);
    expect(objects[1].getAttribute('aria-label')).toBe('Bed loc_a, bed, 2.4 m2, 1 plants, 0 tasks');
  });

  it('marks the selection with aria-pressed and moves the tab stop to it', () => {
    const { svg } = mount(new SvgPlanRenderer(), smallPlan(), viewportAt(0, 10, 100), {
      selectedKeys: new Set(['loc_b']),
    });
    const b = svg.querySelector('[data-plan-key="loc_b"]');
    expect(b).toHaveAttribute('aria-pressed', 'true');
    expect(b).toHaveAttribute('tabindex', '0');
    expect(svg.querySelector('[data-plan-key="loc_a"]')).toHaveAttribute('tabindex', '-1');
  });

  it('names each plant of the entered bed and keeps the rest decorative', () => {
    const { slots, plants } = plantedBed('loc_a', 1, 1, 3, 0.5);
    const model = smallPlan({ slots, plants, locations: [bed('loc_a', 1, 1)], garden_objects: [] });
    const { svg } = mount(new SvgPlanRenderer(), model, viewportAt(0, 10, 100), NO_SELECTION, {
      ...options(),
      enteredLocationKey: 'loc_a',
    });
    const buttons = [...svg.querySelectorAll('g[role="button"]')].map((g) =>
      g.getAttribute('aria-label'),
    );
    expect(buttons).toContain('Plant LOC_A-0');
    expect(svg.querySelector('g[data-plan-key="loc_a"]')).toHaveAttribute('tabindex', '-1');
    const plain = mount(new SvgPlanRenderer(), model);
    expect(plain.svg.querySelector('[data-plan-markers="loc_a"]')).toHaveAttribute(
      'aria-hidden',
      'true',
    );
    expect(plain.svg.querySelector('g[role="button"][data-plan-kind="plant"]')).toBeNull();
  });

  it('calls back on focus and on Enter or Space', () => {
    const onFocusKey = vi.fn();
    const onActivateKey = vi.fn();
    const { svg } = mount(
      new SvgPlanRenderer(),
      smallPlan(),
      viewportAt(0, 10, 100),
      NO_SELECTION,
      {
        ...options(),
        onFocusKey,
        onActivateKey,
      },
    );
    const a = svg.querySelector('[data-plan-key="loc_a"]') as SVGGElement;
    fireEvent.focus(a);
    expect(onFocusKey).toHaveBeenCalledWith('loc_a');
    fireEvent.keyDown(a, { key: 'Enter' });
    fireEvent.keyDown(a, { key: ' ' });
    fireEvent.keyDown(a, { key: 'a' });
    expect(onActivateKey.mock.calls).toEqual([['loc_a'], ['loc_a']]);
  });

  it('has no accessibility violations on the drawn objects', async () => {
    const { container } = mount(
      new SvgPlanRenderer(),
      smallPlan({ garden_objects: [gardenObject('go_1', 6, 6)] }),
      viewportAt(0, 10, 100),
      { selectedKeys: new Set(['loc_a']) },
    );
    // Contrast is skipped: jsdom has no layout, and the palette is a theme concern.
    await expectNoA11yViolations(container, { minImpact: 'minor', minElements: 10 });
  });
});

describe('SvgPlanRenderer - drag by CSS transform (GP-NFR-011)', () => {
  it('moves the node in metres without touching the model or re-rendering it', () => {
    const renderer = new SvgPlanRenderer();
    const { svg, rerender } = mount(renderer);
    const node = svg.querySelector('[data-plan-key="loc_a"]') as SVGGElement;
    renderer.setDragOffset('loc_a', 50, -20); // 100 px/m
    expect(node.style.transform).toBe('translate(0.5px, -0.2px)');
    renderer.setDragOffset('loc_a', 100, 0);
    expect(node.style.transform).toBe('translate(1px, 0px)');
    // A render of the same model (selection change) keeps the preview on the same DOM node.
    rerender(
      wrap(
        renderer.render(
          smallPlan(),
          viewportAt(0, 10, 100),
          { selectedKeys: new Set(['loc_b']) },
          options(),
        ),
      ),
    );
    expect(svg.querySelector('[data-plan-key="loc_a"]')).toBe(node);
    renderer.setDragOffset(null);
    expect(node.style.transform).toBe('');
  });

  it('switches the preview to another object and ignores an unknown key', () => {
    const renderer = new SvgPlanRenderer();
    const { svg } = mount(renderer);
    renderer.setDragOffset('loc_a', 10, 10);
    renderer.setDragOffset('loc_b', 10, 10);
    expect((svg.querySelector('[data-plan-key="loc_a"]') as SVGGElement).style.transform).toBe('');
    expect((svg.querySelector('[data-plan-key="loc_b"]') as SVGGElement).style.transform).not.toBe(
      '',
    );
    expect(() => renderer.setDragOffset('nope', 1, 1)).not.toThrow();
  });

  it('is a no-op before anything is mounted', () => {
    expect(() => new SvgPlanRenderer().setDragOffset('a', 1, 1)).not.toThrow();
  });
});

describe('SvgPlanRenderer - hit test agrees with what is drawn', () => {
  it('finds the bed under a screen point of the mounted frame', () => {
    const renderer = new SvgPlanRenderer();
    mount(renderer);
    expect(renderer.hitTest(renderer.toScreen([1.6, 2]))).toBe('loc_a');
    expect(renderer.hitTest(renderer.toScreen([9, 9]))).toBeNull();
  });
});

describe('GP-ACC-033 - DOM budget on the "large" plan (150 beds, 300 objects, 3 000 slots, 2 000 plants)', () => {
  const model = largePlacedPlan();
  // Extent of the large fixture: x 0..88.5, y 0..88 -> 10 % of that area is a 27.9 m square.
  const SIDE_M = Math.sqrt(0.1 * 88.5 * 88);
  const PX_PER_M = 1000 / SIDE_M; // the square fills a 1000 px screen: 35.8 px/m, markers on (0.3 m = 10.7 px)

  function count(viewport: Viewport): { dom: number; unmount: () => void } {
    const { svg, unmount } = mount(new SvgPlanRenderer(), model, viewport);
    return { dom: svg.querySelectorAll(DOM_OBJECTS).length, unmount };
  }

  it('would exceed 400 without culling - the bound below is not vacuous', () => {
    const everything = count(viewportAt(0, 90, 11, 1000, 1000)); // 90 m on 1000 px: all in view, markers on
    expect(everything.dom).toBeGreaterThan(400);
    everything.unmount();
  });

  it.each([
    ['south-west corner', 0, 28],
    ['bed field', 12, 36],
    ['object field', 30, 88],
    ['centre', 30, 58],
  ])('stays at or below 400 DOM objects with a 10 %% viewport (%s)', (_name, x, yTop) => {
    const { dom, unmount } = count(viewportAt(x, yTop, PX_PER_M, 1000, 1000));
    expect(PX_PER_M).toBeGreaterThan(33); // markers are drawn: the LOD rule does not hide the cost
    expect(dom).toBeLessThanOrEqual(400);
    expect(dom).toBeGreaterThan(0);
    unmount();
  });

  it('keeps the same bound while panning across the whole plan', () => {
    const renderer = new SvgPlanRenderer();
    let worst = 0;
    for (let x = 0; x <= 70; x += 14) {
      for (let y = 28; y <= 90; y += 14) {
        const view = render(
          wrap(renderer.render(model, viewportAt(x, y, PX_PER_M), NO_SELECTION, options())),
        );
        worst = Math.max(worst, view.container.querySelectorAll(DOM_OBJECTS).length);
        view.unmount();
      }
    }
    console.info(`GP-ACC-033 worst DOM objects while panning: ${worst}`);
    expect(worst).toBeLessThanOrEqual(400);
  });

  it('draws the plants of the entered bed one by one and nothing else individually', () => {
    const renderer = new SvgPlanRenderer();
    const { svg } = mount(renderer, model, viewportAt(0, 12, 100), NO_SELECTION, {
      ...options(),
      enteredLocationKey: 'loc_0',
    });
    expect(svg.querySelectorAll('g[data-plan-kind="plant"]')).toHaveLength(13);
    expect(svg.querySelectorAll('g[data-plan-kind="slot"]')).toHaveLength(7);
  });
});

describe('SvgPlanRenderer - boundary stays in the plan', () => {
  it('draws the garden boundary as a dashed, named object', () => {
    const model = normalizePlan(planResponse());
    const { svg } = mount(new SvgPlanRenderer(), model, viewportAt(0, 100, 5, 500, 500));
    const boundary = svg.querySelector('[data-plan-kind="boundary"]');
    expect(boundary).toHaveAttribute('aria-label', 'Boundary');
    expect(boundary?.querySelector('path')).toHaveAttribute('stroke-dasharray', '10 6');
  });
});

describe('SvgPlanRenderer - task badge (GP-FR-089)', () => {
  const planWith = (counts: { open: number; overdue: number }, width = 1.2) =>
    smallPlan({
      locations: [
        bed('loc_a', 1, 1, {
          open_task_count: counts.open,
          overdue_task_count: counts.overdue,
          geometry: { kind: 'rect', origin: [1, 1], width_m: width, length_m: 2, rotation_deg: 0 },
          bbox: [1, 1, 1 + width, 3],
        }),
      ],
      garden_objects: [],
    });

  it('draws the count of open tasks at the corner of the bed, decorative for assistive technology', () => {
    const { svg } = mount(new SvgPlanRenderer(), planWith({ open: 3, overdue: 0 }));
    const badge = svg.querySelector('[data-plan-badge="loc_a"]');
    expect(badge).not.toBeNull();
    expect(badge?.textContent).toBe('3');
    expect(badge?.getAttribute('data-overdue')).toBe('false');
    expect(badge?.getAttribute('aria-hidden')).toBe('true');
    // The bed's accessible name already carries the count.
    expect(svg.querySelector('[data-plan-key="loc_a"]')?.getAttribute('aria-label')).toContain('3 tasks');
  });

  it('marks a bed with overdue tasks and caps the number at 99+', () => {
    const { svg } = mount(new SvgPlanRenderer(), planWith({ open: 120, overdue: 2 }));
    const badge = svg.querySelector('[data-plan-badge="loc_a"]');
    expect(badge?.getAttribute('data-overdue')).toBe('true');
    expect(badge?.textContent).toBe('99+');
  });

  it('draws no badge for a bed without open tasks, or one too narrow on screen', () => {
    expect(mount(new SvgPlanRenderer(), planWith({ open: 0, overdue: 0 })).svg.querySelector('[data-plan-badge]')).toBeNull();
    // 1.2 m at 30 px/m = 36 px, below the 44 px a badge needs.
    expect(
      mount(new SvgPlanRenderer(), planWith({ open: 2, overdue: 0 }), viewportAt(0, 10, 30)).svg.querySelector('[data-plan-badge]'),
    ).toBeNull();
  });
});
