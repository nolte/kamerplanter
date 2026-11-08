import { act, fireEvent, render } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { smallPlan } from '@/test/gardenPlanFixtures';
import { KonvaPlanRenderer } from './KonvaPlanRenderer';
import { pathOf } from './konvaDraw';
import {
  contextOf,
  installRecordingCanvas,
  nextFrame,
  uninstallRecordingCanvas,
  type RecordingContext,
} from './konvaTestCanvas';
import { NO_SELECTION, bed, gardenObject, options, plantedBed, viewportAt } from './rendererTestKit';
import type { PlanModel } from './rendererTestKit';
import type { RenderOptions, RenderSelection, Viewport } from './types';

/**
 * The Konva renderer without a canvas (jsdom has none): `konvaTestCanvas` gives every canvas a recording context, so
 * these tests read the stage's draw calls (what is drawn where, on which layer) and the accessible overlay's DOM.
 */
const theme = createTheme();
const wrap = (node: ReactNode) => <ThemeProvider theme={theme}>{node}</ThemeProvider>;

beforeAll(installRecordingCanvas);
afterAll(uninstallRecordingCanvas);

async function mount(
  renderer: KonvaPlanRenderer,
  model: PlanModel = smallPlan(),
  viewport: Viewport = viewportAt(0, 10, 100),
  selection: RenderSelection = NO_SELECTION,
  opts: RenderOptions = options(),
) {
  const view = render(wrap(renderer.render(model, viewport, selection, opts)));
  await act(nextFrame);
  const svg = view.container.querySelector('svg') as SVGSVGElement;
  const canvases = [...view.container.querySelectorAll<HTMLCanvasElement>('[data-testid="garden-plan-konva"] canvas')];
  const layers = canvases.map(contextOf);
  return { ...view, svg, plan: layers[0], drag: layers[1], layers };
}

const texts = (layer: RecordingContext) => layer.ops('fillText').map((call) => call.args[0]);

describe('KonvaPlanRenderer - stage', () => {
  it('draws the plan on one layer and keeps a second, empty one for the drag', async () => {
    const { plan, drag, layers, container } = await mount(new KonvaPlanRenderer());
    expect(layers).toHaveLength(2);
    expect(container.querySelector('[data-renderer="konva"]')).not.toBeNull();
    // Both beds are named on the canvas; the drag layer holds nothing yet.
    expect(texts(plan)).toEqual(expect.arrayContaining(['Bed loc_a', 'Bed loc_b']));
    expect(texts(drag)).toEqual([]);
  });

  it('writes a name at its label anchor, in screen pixels', async () => {
    // Bed loc_a: 1.2 x 2 m at (1, 1); anchor (1.6, 2) -> (160, 800) px at 100 px/m from (0, 10).
    const { plan } = await mount(new KonvaPlanRenderer());
    const call = plan.ops('fillText').find((entry) => entry.args[0] === 'Bed loc_a');
    expect(call?.args[1]).toBeCloseTo(160, 6);
    expect(call?.args[2] as number).toBeCloseTo(800 + 12 / 3, 6);
    expect(call?.font).toMatch(/^12px /);
  });

  it('outlines the selection in the primary colour and a refused object in the error colour', async () => {
    const { plan } = await mount(
      new KonvaPlanRenderer(),
      smallPlan({ garden_objects: [] }),
      viewportAt(0, 10, 100),
      { selectedKeys: new Set(['loc_a']) },
      options({ invalidKeys: new Set(['loc_b']) }),
    );
    const strokes = plan.ops('stroke');
    expect(strokes.some((call) => call.strokeStyle === theme.palette.primary.main && call.lineWidth === 3)).toBe(true);
    expect(strokes.some((call) => call.strokeStyle === theme.palette.error.main && call.lineWidth === 4)).toBe(true);
  });

  it('draws a dense bed as one cluster with its count (GP-NFR-067)', async () => {
    const { slots, plants } = plantedBed('loc_a', 1, 1, 6, 0.1);
    const { plan, svg } = await mount(
      new KonvaPlanRenderer(),
      smallPlan({ slots, plants, locations: [bed('loc_a', 1, 1)], garden_objects: [] }),
      viewportAt(0, 10, 99),
    );
    expect(texts(plan)).toContain('6');
    expect(svg.querySelector('[data-plan-cluster="loc_a"]')).toHaveAttribute('aria-label', '6 plants');
  });

  it('draws the task badge on the canvas and keeps its click target in the overlay (GP-FR-089)', async () => {
    const model = smallPlan({
      locations: [bed('loc_a', 1, 1, { open_task_count: 120, overdue_task_count: 2 })],
      garden_objects: [],
    });
    const { plan, svg } = await mount(new KonvaPlanRenderer(), model);
    expect(texts(plan)).toContain('99+');
    const target = svg.querySelector('[data-plan-badge="loc_a"]');
    expect(target).toHaveAttribute('data-overdue', 'true');
    expect(target).toHaveAttribute('aria-hidden', 'true');
    expect(target?.querySelector('rect')).toHaveAttribute('pointer-events', 'all');
  });
});

describe('KonvaPlanRenderer - plant state channels (GP-UX-059/060)', () => {
  it('draws the initial, the lifecycle ring and the badge of a stated plant, and the state in its name', async () => {
    const { slots, plants } = plantedBed('loc_a', 1, 1, 2, 0.5);
    const model = smallPlan({ slots, plants, locations: [bed('loc_a', 1, 1)], garden_objects: [] });
    const plantStates = {
      loc_a_p0: { lifecycle: 'harvesting', badge: 'frost', initial: 'T', progress: 0.5, ariaLabel: 'Tomato, harvest' },
    } as const;
    const { plan, svg } = await mount(new KonvaPlanRenderer(), model, viewportAt(0, 10, 100), NO_SELECTION, {
      ...options(),
      enteredLocationKey: 'loc_a',
      plantStates,
    });
    // Plant 0 sits at (1.1, 1.5) -> (110, 850) px: the disc, the second ring of "harvesting" and the progress arc.
    const near = (value: unknown, target: number) => Math.abs((value as number) - target) < 1e-6;
    const arcsAtPlant = plan.ops('arc').filter((call) => near(call.args[0], 110) && near(call.args[1], 850));
    // (The recorder keeps every paint since the mount; one paint draws these three.)
    expect(arcsAtPlant.slice(0, 3).map((call) => call.args[2])).toEqual([8, 10.5, 13]);
    expect(texts(plan)).toContain('T');
    // The frost badge: its outline is filled in the badge colour.
    expect(plan.ops('fill').some((call) => call.fillStyle === '#01579B')).toBe(true);
    expect(svg.querySelector('[data-plan-key="loc_a_p0"]')).toHaveAttribute('aria-label', 'Tomato, harvest');
  });
});

describe('KonvaPlanRenderer - stroke state', () => {
  it('never draws a dashed slot ring with the round cap of a fence before it', async () => {
    const { slots } = plantedBed('loc_a', 1, 1, 3, 0.5);
    const model = smallPlan({
      slots,
      plants: [],
      locations: [bed('loc_a', 1, 1)],
      garden_objects: [
        gardenObject('fence', 0, 0, {
          object_type: 'fence',
          props: { object_type: 'fence' },
          geometry: { kind: 'polyline', points: [[1, 8], [6, 8]], width_m: 0.4 },
          bbox: [1, 7.8, 6, 8.2],
        }),
      ],
    });
    const { plan } = await mount(new KonvaPlanRenderer(), model);
    const capOfStrokes: string[] = [];
    const dashed = plan.ops('stroke').filter((call) => call.lineDash.join(' ') === '2 2');
    expect(dashed.length).toBeGreaterThan(0);
    for (const call of dashed) capOfStrokes.push(String(call.lineCap));
    expect(new Set(capOfStrokes)).toEqual(new Set(['butt']));
    expect(plan.ops('stroke').some((call) => call.lineCap === 'round')).toBe(true); // the fence itself
  });
});

describe('KonvaPlanRenderer - accessible overlay (GP-NFR-020/068, §9.7)', () => {
  it('labels the surface and gives every object a name and one tab stop, like the SVG renderer', async () => {
    const { svg } = await mount(new KonvaPlanRenderer());
    expect(svg).toHaveAttribute('data-testid', 'garden-plan-svg');
    expect(svg).toHaveAttribute('role', 'group');
    expect(svg).toHaveAttribute('aria-roledescription', 'Plan');
    const objects = [...svg.querySelectorAll<SVGGElement>('g[role="button"]')];
    expect(objects.map((g) => g.getAttribute('data-plan-key'))).toEqual(['__boundary__', 'loc_a', 'loc_b']);
    expect(objects.filter((g) => g.getAttribute('tabindex') === '0').map((g) => g.dataset.planKey)).toEqual(['loc_a']);
    expect(objects[1].getAttribute('aria-label')).toBe('Bed loc_a, bed, 2.4 m2, 1 plants, 0 tasks');
    // The overlay paints nothing: the canvas shows the plan.
    for (const shape of svg.querySelectorAll('.gp-shape')) {
      expect(shape).toHaveAttribute('fill', 'none');
      expect(shape).toHaveAttribute('stroke', 'none');
    }
  });

  it('makes an object a pointer target where the SVG renderer paints it, and reports what the canvas drew', async () => {
    const { slots, plants } = plantedBed('loc_a', 1, 1, 3, 0.5);
    const model = smallPlan({
      slots,
      plants,
      locations: [bed('loc_a', 1, 1)],
      garden_objects: [
        gardenObject('fence', 0, 0, {
          object_type: 'fence',
          props: { object_type: 'fence' },
          geometry: { kind: 'polyline', points: [[1, 8], [6, 8]], width_m: 0.4 },
          bbox: [1, 7.8, 6, 8.2],
        }),
      ],
    });
    const { svg } = await mount(new KonvaPlanRenderer(), model);
    const shapeOf = (key: string) => svg.querySelector(`[data-plan-key="${key}"] .gp-shape`);
    expect(shapeOf('loc_a')).toHaveAttribute('pointer-events', 'visibleFill');
    expect(shapeOf('__boundary__')).toHaveAttribute('pointer-events', 'visibleStroke');
    expect(shapeOf('fence')).toHaveAttribute('pointer-events', 'visibleStroke');
    expect(shapeOf('fence')).toHaveAttribute('stroke-width', '0.4');
    expect(svg).toHaveAttribute('data-renderer', 'konva');
    expect(svg).toHaveAttribute('data-plan-markers-batched', '3');
    expect(svg).toHaveAttribute('data-plan-markers-single', '0');
  });

  it('names each plant of the entered bed and keeps the rest on the canvas only', async () => {
    const { slots, plants } = plantedBed('loc_a', 1, 1, 3, 0.5);
    const model = smallPlan({ slots, plants, locations: [bed('loc_a', 1, 1)], garden_objects: [] });
    const entered = await mount(new KonvaPlanRenderer(), model, viewportAt(0, 10, 100), NO_SELECTION, {
      ...options(),
      enteredLocationKey: 'loc_a',
      describedPlantKey: 'loc_a_p1',
    });
    const plantsShown = [...entered.svg.querySelectorAll('g[role="button"][data-plan-kind="plant"]')];
    expect(plantsShown.map((g) => g.getAttribute('aria-label'))).toEqual([
      'Plant LOC_A-0',
      'Plant LOC_A-1',
      'Plant LOC_A-2',
    ]);
    expect(plantsShown[1]).toHaveAttribute('aria-describedby', 'gp-plant-info');
    entered.unmount();
    const plain = await mount(new KonvaPlanRenderer(), model);
    expect(plain.svg.querySelector('[data-plan-kind="plant"]')).toBeNull();
    // ... yet the three markers are drawn: one batch path with three discs.
    expect(plain.plan.ops('arc').length).toBeGreaterThanOrEqual(3);
  });

  it('calls back on focus and on Enter or Space', async () => {
    const onFocusKey = vi.fn();
    const onActivateKey = vi.fn();
    const { svg } = await mount(new KonvaPlanRenderer(), smallPlan(), viewportAt(0, 10, 100), NO_SELECTION, {
      ...options(),
      onFocusKey,
      onActivateKey,
    });
    const a = svg.querySelector('[data-plan-key="loc_a"]') as SVGGElement;
    fireEvent.focus(a);
    expect(onFocusKey).toHaveBeenCalledWith('loc_a');
    fireEvent.keyDown(a, { key: 'Enter' });
    fireEvent.keyDown(a, { key: ' ' });
    fireEvent.keyDown(a, { key: 'a' });
    expect(onActivateKey.mock.calls).toEqual([['loc_a'], ['loc_a']]);
  });

  it('keeps the canvas out of the accessibility tree and has no violations', async () => {
    const { container } = await mount(
      new KonvaPlanRenderer(),
      smallPlan({ garden_objects: [gardenObject('go_1', 6, 6)] }),
      viewportAt(0, 10, 100),
      { selectedKeys: new Set(['loc_a']) },
    );
    expect(container.querySelector('[data-testid="garden-plan-konva"]')).toHaveAttribute('aria-hidden', 'true');
    await expectNoA11yViolations(container, { minImpact: 'minor', minElements: 10 });
  });
});

describe('KonvaPlanRenderer - drag on its own layer (GP-NFR-011, GP-NFR-033)', () => {
  it('moves the dragged bed to the drag layer and repaints only that layer while it moves', async () => {
    const renderer = new KonvaPlanRenderer();
    const { plan, drag, svg } = await mount(renderer);
    plan.reset();
    drag.reset();

    await act(async () => {
      renderer.setDragOffset('loc_a', 50, -20);
      await nextFrame();
    });
    // The plan layer repainted once without the bed, the drag layer drew it shifted by the offset.
    expect(texts(plan)).not.toContain('Bed loc_a');
    expect(texts(plan)).toContain('Bed loc_b');
    const moved = drag.ops('fillText').find((call) => call.args[0] === 'Bed loc_a');
    expect(moved).toBeDefined();
    expect(drag.ops('translate').map((call) => call.args)).toContainEqual([50, -20]);
    // The overlay node follows like the SVG renderer's node: focus ring and badge target stay on the bed.
    const overlayNode = svg.querySelector<SVGGElement>('g[data-plan-key="loc_a"]');
    expect(overlayNode?.style.transform).toBe('translate(0.5px, -0.2px)');

    plan.reset();
    drag.reset();
    await act(async () => {
      renderer.setDragOffset('loc_a', 80, 0);
      await nextFrame();
    });
    expect(plan.calls).toEqual([]); // a move repaints one node, never the plan
    expect(drag.ops('translate').map((call) => call.args)).toContainEqual([80, 0]);

    await act(async () => {
      renderer.setDragOffset(null);
      await nextFrame();
    });
    expect(renderer.dragPreview).toBeNull();
    expect(texts(plan)).toContain('Bed loc_a');
    expect(overlayNode?.style.transform).toBe('');
  });

  it('ignores an unknown key and is a no-op before anything is mounted', async () => {
    expect(() => new KonvaPlanRenderer().setDragOffset('a', 1, 1)).not.toThrow();
    const renderer = new KonvaPlanRenderer();
    await mount(renderer);
    renderer.setDragOffset('nope', 1, 1);
    expect(renderer.dragPreview).toBeNull();
  });
});

describe('konvaDraw - path cache', () => {
  it('parses each icon or glyph path once per factory and reuses it', () => {
    const factory = vi.fn((d: string) => ({ d }) as unknown as Path2D);
    const frame = { path: factory } as unknown as Parameters<typeof pathOf>[0];
    const first = pathOf(frame, 'M0 0L1 1');
    expect(pathOf(frame, 'M0 0L1 1')).toBe(first);
    expect(pathOf(frame, 'M0 0L2 2')).not.toBe(first);
    expect(factory).toHaveBeenCalledTimes(2);
  });
});
