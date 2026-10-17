/** Shared helpers of the editor tool tests: a tool environment over the headless renderer. */
import { HeadlessPlanRenderer } from '../../renderer/HeadlessPlanRenderer';
import { NO_SELECTION, options } from '../../renderer/rendererTestKit';
import { normalizePlan, type PlanModel } from '../../model/planModel';
import type { Geometry, PlanLocation, Point } from '../../model/types';
import { bed, gardenObject, planResponse } from '@/test/gardenPlanFixtures';
import type { SelectionRef, SelectionStack } from '../../state/gardenPlanSlice';
import type { Viewport } from '../../renderer';
import type { PointerSample, ToolEnv } from './machineTypes';

/** 20 px per metre, model (0, 20) at the top-left corner: x 0..20 m, y 0..20 m on a 400 px canvas. */
export const VIEWPORT: Viewport = { originM: [0, 20], pxPerM: 20, widthPx: 400, heightPx: 400 };

export interface EnvOptions {
  selection?: SelectionRef[];
  stack?: SelectionStack | null;
  angleStepDeg?: number;
  snapPoint?: ToolEnv['snapPoint'];
  viewport?: Viewport;
}

export function makeEnv(plan: PlanModel, opts: EnvOptions = {}): ToolEnv {
  const renderer = new HeadlessPlanRenderer();
  const viewport = opts.viewport ?? VIEWPORT;
  renderer.render(plan, viewport, NO_SELECTION, options());
  return {
    plan,
    selection: opts.selection ?? [],
    stack: opts.stack ?? null,
    pxPerM: viewport.pxPerM,
    hitTestAll: (p) => renderer.hitTestAll(p),
    toModel: (p) => renderer.toModel(p),
    toScreen: (p) => renderer.toScreen(p),
    snapPoint:
      opts.snapPoint ?? (([x, y]) => [Math.round(x * 1000) / 1000, Math.round(y * 1000) / 1000]),
    angleStepDeg: opts.angleStepDeg ?? 15,
  };
}

/** A mouse sample at a model point (so tests read in metres, not pixels). */
export function at(env: ToolEnv, pointM: Point, mods: Partial<PointerSample> = {}): PointerSample {
  return { pointPx: env.toScreen(pointM), pointerType: 'mouse', shift: false, alt: false, ...mods };
}

export function atPx(pointPx: Point, mods: Partial<PointerSample> = {}): PointerSample {
  return { pointPx, pointerType: 'mouse', shift: false, alt: false, ...mods };
}

function rectBed(
  key: string,
  x: number,
  y: number,
  w: number,
  l: number,
  extra: Partial<PlanLocation> = {},
) {
  const geometry: Geometry = {
    kind: 'rect',
    origin: [x, y],
    width_m: w,
    length_m: l,
    rotation_deg: 0,
  };
  return bed(key, x, y, { geometry, area_m2: w * l, bbox: [x, y, x + w, y + l], ...extra });
}

/**
 * area (2,2)-(12,12) holding bed b1 (3,3) 2x2 [2 slots, 1 plant, 3 open tasks], bed b2 (6,3) 2x2 and
 * the tree t1 at (9,9); alone: bed solo (14,2) 2x2 and the locked bed lock (14,8) 2x2. Boundary 20x20.
 */
export function testPlan() {
  return normalizePlan(
    planResponse({
      plan: {
        boundary: { kind: 'rect', origin: [0, 0], width_m: 20, length_m: 20, rotation_deg: 0 },
        north_angle_deg: 0,
        default_grid_m: 0.1,
        adjacency_factor: 1.5,
        plan_revision: 7,
      },
      locations: [
        rectBed('area', 2, 2, 10, 10, { name: 'Area', location_type_key: 'area', z_order: 0 }),
        rectBed('b1', 3, 3, 2, 2, {
          name: 'Bed 1',
          parent_location_key: 'area',
          depth: 1,
          open_task_count: 3,
          z_order: 1,
        }),
        rectBed('b2', 6, 3, 2, 2, {
          name: 'Bed 2',
          parent_location_key: 'area',
          depth: 1,
          z_order: 1,
        }),
        rectBed('solo', 14, 2, 2, 2, { name: 'Solo', z_order: 0 }),
        rectBed('lock', 14, 8, 2, 2, { name: 'Locked', locked: true }),
      ],
      garden_objects: [
        gardenObject('t1', 9, 9, {
          parent_location_key: 'area',
          geometry: { kind: 'circle', origin: [9, 9], radius_m: 0.5 },
          bbox: [8.5, 8.5, 9.5, 9.5],
          label: 'Tree',
        }),
      ],
      slots: [
        { key: 's1', slot_id: 'B1_1', location_key: 'b1', plan_geometry: { origin: [3.5, 3.5] } },
        { key: 's2', slot_id: 'B1_2', location_key: 'b1', plan_geometry: { origin: [4.5, 4.5] } },
      ],
      plants: [{ key: 'p1', instance_id: 'TOM-1', species_key: 'sp_tomato', slot_key: 's1' }],
    }),
  );
}
