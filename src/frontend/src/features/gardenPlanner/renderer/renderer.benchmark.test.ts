import { describe, expect, it } from 'vitest';
import { hitTestAll } from './hitTest';
import {
  bed,
  largePlacedPlan,
  normalizePlan,
  NO_SELECTION,
  planResponse,
  viewportAt,
  type PlanModel,
} from './rendererTestKit';
import { buildScene } from './scene';
import type { PlanPlant, PlanSlot } from '../model/types';
import { ATTENTION_PRIORITY } from '../model/plantState';
import type { PlantMarkerState } from './types';
import { COMPANION_LINE_CAP, cullCompanionLines, type CompanionLine } from './companionLines';
import { drawDragged, drawScene, type DrawFrame, type PlanCanvasContext } from './konvaDraw';
import { planPalette } from './planDrawing';
import { TEST_LABELS } from './rendererTestKit';
import { createTheme } from '@mui/material/styles';

/**
 * GP-NFR-034 / GP-NFR-033 (benchmark half): a frame's scene and a hit test on the "large" plan
 * stay far inside the 16 ms frame budget. Wall-clock bounds run only in the benchmark lane, never in
 * the shared CI suite where a loaded runner makes them flaky:
 *
 *     GP_BENCHMARK=1 npx vitest run src/features/gardenPlanner/renderer/renderer.benchmark.test.ts
 *
 * The always-on half (counts, not time) is in `SvgPlanRenderer.test.tsx` (GP-ACC-033).
 *
 * The Konva cases (D-01, WP 9.7) time the renderer's own work per frame - painting the scene onto a 2D context and
 * repainting the drag layer - against a context whose calls cost nothing, so they measure the renderer and not a
 * rasteriser (jsdom has none). The browser's raster time is what the WP 9.6 E2E probe measures.
 */
const RUNS = 100;
const BUDGET_MS = 16;

function median(values: number[]): number {
  return [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)];
}

/**
 * 250 beds of 20 plants on a 0.3 m grid = 5 000 plants (GP-NFR-073), every one with a state, every bed at marker
 * LOD in one 2000 × 1200 px view at 36 px/m: the worst case of the plant-state layer (#2488), where no plant is
 * batched and every plant becomes a marker of its own.
 */
function statedPlan(): { model: PlanModel; states: Record<string, PlantMarkerState> } {
  const locations = [];
  const slots: PlanSlot[] = [];
  const plants: PlanPlant[] = [];
  const states: Record<string, PlantMarkerState> = {};
  for (let b = 0; b < 250; b += 1) {
    const key = `bed${b}`;
    const x = (b % 25) * 2;
    const y = Math.floor(b / 25) * 3;
    locations.push(bed(key, x, y));
    for (let k = 0; k < 20; k += 1) {
      const slotKey = `${key}_s${k}`;
      const plantKey = `${key}_p${k}`;
      slots.push({
        key: slotKey,
        slot_id: `${key}_${k}`,
        location_key: key,
        plan_geometry: { origin: [x + 0.15 + (k % 4) * 0.3, y + 0.2 + Math.floor(k / 4) * 0.35] },
      });
      plants.push({ key: plantKey, instance_id: plantKey, species_key: 'sp', slot_key: slotKey, phase_key: `ph${k % 4}` });
      states[plantKey] = {
        lifecycle: 'active',
        badge: k % 3 === 0 ? ATTENTION_PRIORITY[k % ATTENTION_PRIORITY.length] : null,
        initial: 'T',
        progress: 0.5,
        ariaLabel: 'Tomato',
      };
    }
  }
  const model = normalizePlan(planResponse({ locations, garden_objects: [], slots, plants }));
  return { model, states };
}

/** A 2D context whose every call is free: what remains is the renderer's own work. */
function freeContext(): PlanCanvasContext & { calls: number } {
  const context = { calls: 0 } as PlanCanvasContext & { calls: number };
  for (const name of ['save', 'restore', 'translate', 'scale', 'beginPath', 'closePath', 'moveTo', 'lineTo', 'arc',
    'fill', 'stroke', 'fillText', 'setLineDash'] as const) {
    (context as unknown as Record<string, () => void>)[name] = () => {
      context.calls += 1;
    };
  }
  return context;
}

const THEME = createTheme();

function konvaFrame(scene: ReturnType<typeof buildScene>, viewport: ReturnType<typeof viewportAt>): DrawFrame {
  return {
    scene,
    viewport,
    palette: planPalette(THEME),
    labels: TEST_LABELS,
    fontPx: 12,
    fontFamily: 'sans-serif',
    contrastText: () => '#fff',
    path: () => ({}) as Path2D,
  };
}

describe.runIf(process.env.GP_BENCHMARK === '1')('Konva renderer frame cost on a large plan (D-01, WP 9.7)', () => {
  it('paints a frame of the "large" plan onto the canvas within one frame (median)', () => {
    const model = largePlacedPlan();
    const view = (i: number) => viewportAt((i * 0.7) % 60, 30 + (i % 50), 36, 1000, 1000);
    const context = freeContext();
    const frames = Array.from({ length: RUNS }, (_, i) => konvaFrame(buildScene(model, view(i), NO_SELECTION, {}), view(i)));
    drawScene(context, frames[0]);
    expect(context.calls).toBeGreaterThan(1000); // the case draws a real plan, not an empty view
    const times = frames.map((frame) => {
      const start = performance.now();
      drawScene(context, frame);
      return performance.now() - start;
    });
    expect(median(times)).toBeLessThanOrEqual(BUDGET_MS);
  });

  it('paints 5 000 stated plants of the plant-state layer within one frame (median, #2488)', () => {
    const { model: stated, states } = statedPlan();
    const view = viewportAt(-1, 31, 36, 2000, 1200);
    const scene = buildScene(stated, view, NO_SELECTION, { plantStateLayer: { states, attentionOnly: false } });
    expect(scene.markers).toHaveLength(5000);
    const frame = konvaFrame(scene, view);
    const context = freeContext();
    const times = Array.from({ length: RUNS }, () => {
      const start = performance.now();
      drawScene(context, frame);
      return performance.now() - start;
    });
    expect(median(times)).toBeLessThanOrEqual(BUDGET_MS);
  });

  it('repaints only the dragged bed per pointer move (median far below one frame, GP-NFR-033)', () => {
    const model = largePlacedPlan();
    const view = viewportAt(10, 50, 36, 1000, 1000);
    const scene = buildScene(model, view, NO_SELECTION, {});
    const key = scene.shapes.find((item) => item.entry.kind === 'location')?.entry.key as string;
    const frame = konvaFrame(scene, view);
    const whole = freeContext();
    drawScene(whole, frame);
    const dragged = freeContext();
    drawDragged(dragged, frame, { key, dxPx: 1, dyPx: 1 });
    // A pointer move costs one node's calls, a small share of the plan's.
    expect(dragged.calls).toBeGreaterThan(0);
    expect(dragged.calls * 50).toBeLessThan(whole.calls);
    const times = Array.from({ length: RUNS }, (_, i) => {
      const start = performance.now();
      drawDragged(dragged, frame, { key, dxPx: i % 30, dyPx: 0 });
      return performance.now() - start;
    });
    expect(median(times)).toBeLessThanOrEqual(BUDGET_MS / 8);
  });
});

describe.runIf(process.env.GP_BENCHMARK === '1')('renderer frame cost on a large plan', () => {
  const model = largePlacedPlan();
  const view = (i: number) => viewportAt((i * 0.7) % 60, 30 + (i % 50), 36, 1000, 1000);

  it('builds a scene within one frame (median)', () => {
    buildScene(model, view(0), NO_SELECTION, {}); // warm the model caches, as a mounted editor has
    const times = Array.from({ length: RUNS }, (_, i) => {
      const start = performance.now();
      buildScene(model, view(i), NO_SELECTION, {});
      return performance.now() - start;
    });
    expect(median(times)).toBeLessThanOrEqual(BUDGET_MS);
  });

  it('builds a scene with 5 000 stated plants of the plant-state layer within one frame (median, #2488)', () => {
    const { model: stated, states } = statedPlan();
    const view = viewportAt(-1, 31, 36, 2000, 1200);
    const options = { plantStateLayer: { states, attentionOnly: false } };
    const first = buildScene(stated, view, NO_SELECTION, options);
    // the case is what it claims: every plant drawn on its own, with its state
    expect(first.markers).toHaveLength(5000);
    expect(first.markers.every((marker) => marker.layerState !== undefined)).toBe(true);
    const filtered = { plantStateLayer: { states, attentionOnly: true } };
    const times = Array.from({ length: RUNS }, (_, i) => {
      const start = performance.now();
      buildScene(stated, view, NO_SELECTION, i % 2 === 0 ? options : filtered);
      return performance.now() - start;
    });
    expect(median(times)).toBeLessThanOrEqual(BUDGET_MS);
  });

  it('culls 5 000 companion lines to the 500-line cap within one frame (median, GP-FR-134)', () => {
    // 250 beds of 20 neighbouring pairs, the size of the plant-state worst case, all of them in one big view
    const lines: CompanionLine[] = [];
    const statuses = ['compatible', 'incompatible', 'unknown'] as const;
    for (let b = 0; b < 250; b += 1) {
      const x = (b % 25) * 2;
      const y = Math.floor(b / 25) * 3;
      for (let k = 0; k < 20; k += 1) {
        const a: [number, number] = [x + 0.15 + (k % 4) * 0.3, y + 0.2 + Math.floor(k / 4) * 0.35];
        lines.push({ id: `bed${b}:${k}`, a, b: [a[0] + 0.3, a[1]], status: statuses[(b + k) % 3] });
      }
    }
    const view = viewportAt(-1, 31, 36, 2000, 1200);
    expect(cullCompanionLines(lines, view).candidates).toBe(5000);
    const times = Array.from({ length: RUNS }, (_, i) => {
      const start = performance.now();
      const culled = cullCompanionLines(lines, viewportAt(-1 + (i % 10) * 0.1, 31, 36, 2000, 1200));
      const elapsed = performance.now() - start;
      expect(culled.lines.length).toBeLessThanOrEqual(COMPANION_LINE_CAP);
      return elapsed;
    });
    expect(median(times)).toBeLessThanOrEqual(BUDGET_MS);
  });

  it('answers a hit test within one frame (median)', () => {
    hitTestAll(model, view(0), [500, 500]);
    const times = Array.from({ length: RUNS }, (_, i) => {
      const start = performance.now();
      hitTestAll(model, view(i), [500, 500]);
      return performance.now() - start;
    });
    expect(median(times)).toBeLessThanOrEqual(BUDGET_MS);
  });
});
