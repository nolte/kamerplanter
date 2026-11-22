import { act, render } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { loadVectors } from '@/test/gardenPlanVectors';
import { boundingBox, parseGeometry } from '../model/geometry';
import type { Geometry, Point } from '../model/types';
import { HeadlessPlanRenderer } from './HeadlessPlanRenderer';
import { KonvaPlanRenderer } from './KonvaPlanRenderer';
import { contextOf, installRecordingCanvas, nextFrame, uninstallRecordingCanvas } from './konvaTestCanvas';
import {
  NO_SELECTION,
  bed,
  gardenObject,
  normalizePlan,
  options,
  plantedBed,
  planResponse,
  viewportAt,
  type PlanModel,
} from './rendererTestKit';
import { SvgPlanRenderer } from './SvgPlanRenderer';
import type { PlanRenderer, Viewport } from './types';

/**
 * The renderer contract (REQ-053 D-01, GP-NFR-009): Headless, SVG and Konva answer the same hit test for the same
 * frame and draw an object's name where the shared vectors put it. The geometries are the `label_anchor` cases of
 * `garden-plan-vectors.json` - the file the Python reference (`test_label_anchor_vectors.py`) and the TypeScript port
 * already run against - each placed as a garden object of its own. Hit testing is model-based in every renderer
 * (`BasePlanRenderer`); this suite pins that none of them answers differently from what it draws.
 */
const VECTORS = loadVectors();
const CASES = VECTORS.cases.filter((vector) => vector.operation === 'label_anchor');
const KEY = 'vector';
const theme = createTheme();

type Kind = 'headless' | 'svg' | 'konva';
const KINDS: Kind[] = ['headless', 'svg', 'konva'];

function create(kind: Kind): PlanRenderer {
  if (kind === 'headless') return new HeadlessPlanRenderer();
  if (kind === 'svg') return new SvgPlanRenderer();
  return new KonvaPlanRenderer();
}

/** The model point at which each renderer writes the name, in metres; `null` = no name drawn. */
async function drawnLabel(kind: Kind, renderer: PlanRenderer, model: PlanModel, viewport: Viewport): Promise<Point | null> {
  const node = renderer.render(model, viewport, NO_SELECTION, options());
  if (kind === 'headless') {
    const label = (renderer as HeadlessPlanRenderer).lastScene?.shapes.find((item) => item.entry.key === KEY)?.label;
    return label ? [label.x, label.y] : null;
  }
  const view = render(<ThemeProvider theme={theme}>{node}</ThemeProvider>);
  try {
    if (kind === 'svg') {
      const text = view.container.querySelector(`[data-testid="garden-plan-label-${KEY}"]`);
      return text ? [Number(text.getAttribute('x')), Number.NaN] : null;
    }
    await act(nextFrame);
    const canvas = view.container.querySelector<HTMLCanvasElement>('[data-testid="garden-plan-konva"] canvas');
    const call = canvas ? contextOf(canvas).ops('fillText')[0] : undefined;
    return call ? renderer.toModel([call.args[1] as number, call.args[2] as number]) : null;
  } finally {
    view.unmount();
  }
}

function vectorPlan(geometry: Geometry): PlanModel {
  return normalizePlan(
    planResponse({
      plan: null,
      locations: [],
      garden_objects: [
        gardenObject(KEY, 0, 0, {
          object_type: 'other',
          label: 'V',
          props: { object_type: 'other' },
          geometry,
          bbox: boundingBox(geometry),
        }),
      ],
      slots: [],
      plants: [],
    }),
  );
}

/** A 1000 px view around the object's box at a zoom that shows its name (>= 60 px wide). */
function fit(geometry: Geometry): Viewport {
  const [x0, y0, x1, y1] = boundingBox(geometry);
  const pxPerM = Math.min(200, 800 / Math.max(x1 - x0, y1 - y0, 0.01));
  const margin = 100 / pxPerM;
  return viewportAt(x0 - margin, y1 + margin, pxPerM, 1000, 1000);
}

beforeAll(installRecordingCanvas);
afterAll(uninstallRecordingCanvas);

describe('renderer contract against the label_anchor vectors (Headless, SVG, Konva)', () => {
  it('runs on vectors of every geometry kind', () => {
    const kinds = new Set(CASES.map((vector) => (vector.input.geometry as Geometry).kind));
    expect(kinds).toEqual(new Set(['rect', 'circle', 'polygon', 'polyline', 'point']));
  });

  it.each(CASES.map((vector) => [vector.id, vector] as const))('%s', async (_id, vector) => {
    const geometry = parseGeometry(vector.input.geometry);
    if (geometry === null) throw new Error(`vector geometry does not parse: ${vector.id}`);
    const expected = (vector.expected as { point: Point }).point;
    const tolerance = vector.tolerance ?? VECTORS.default_tolerance;
    const model = vectorPlan(geometry);
    const viewport = fit(geometry);
    const [x0, , x1, y1] = boundingBox(geometry);

    for (const kind of KINDS) {
      const renderer = create(kind);
      const label = await drawnLabel(kind, renderer, model, viewport);
      // The anchor is on the object: every renderer finds it there, and nothing beside its box.
      expect(renderer.hitTest(renderer.toScreen(expected)), `${kind}: hit at the anchor`).toBe(KEY);
      expect(renderer.hitTest(renderer.toScreen([x1 + 60 / viewport.pxPerM, y1 + 60 / viewport.pxPerM])), kind).toBeNull();
      expect(renderer.hitTestAll(renderer.toScreen(expected)), kind).toEqual([KEY]);
      if ((x1 - x0) * viewport.pxPerM < 60) {
        expect(label, `${kind}: no name below 60 px`).toBeNull();
        continue;
      }
      expect(label, `${kind}: a name is drawn`).not.toBeNull();
      const slack = Math.max(tolerance, 0.5 / viewport.pxPerM); // half a pixel of output rounding
      expect(Math.abs((label as Point)[0] - expected[0]), `${kind}: x of the name`).toBeLessThanOrEqual(slack);
    }
  });
});

describe('renderer contract on a mixed plan: one hit-test answer per screen point', () => {
  const { slots, plants } = plantedBed('bed', 1, 1, 3, 0.4);
  const model = normalizePlan(
    planResponse({
      locations: [bed('bed', 1, 1), bed('raised', 1.5, 1.5, { z_order: 2 })],
      garden_objects: [gardenObject('tree', 5, 5)],
      slots,
      plants,
    }),
  );
  const viewport = viewportAt(0, 10, 100);

  it('Headless, SVG and Konva return the same stack on a 25 px grid', async () => {
    const answers: Record<Kind, string[][]> = { headless: [], svg: [], konva: [] };
    for (const kind of KINDS) {
      const renderer = create(kind);
      const node = renderer.render(model, viewport, NO_SELECTION, options());
      const view = kind === 'headless' ? null : render(<ThemeProvider theme={theme}>{node}</ThemeProvider>);
      for (let x = 0; x <= 1000; x += 25) {
        for (let y = 0; y <= 1000; y += 25) answers[kind].push(renderer.hitTestAll([x, y]));
      }
      view?.unmount();
    }
    expect(answers.headless.filter((stack) => stack.length > 0).length).toBeGreaterThan(50);
    expect(answers.svg).toEqual(answers.headless);
    expect(answers.konva).toEqual(answers.headless);
  });
});
