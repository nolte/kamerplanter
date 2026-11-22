import { normalizePlan, type PlanModel } from '@/features/gardenPlanner/model/planModel';
import type {
  GardenObject,
  GardenPlanResponse,
  PlanLocation,
  PlanPlant,
  PlanSlot,
} from '@/features/gardenPlanner/model/types';

/** Test fixtures for the garden plan feature (GP-ACC-033 "large" class and small hand-made plans). */

export function bed(
  key: string,
  x: number,
  y: number,
  overrides: Partial<PlanLocation> = {},
): PlanLocation {
  return {
    key,
    name: `Bed ${key}`,
    location_type_key: 'bed',
    depth: 0,
    geometry: { kind: 'rect', origin: [x, y], width_m: 1.2, length_m: 2, rotation_deg: 0 },
    area_m2: 2.4,
    bbox: [x, y, x + 1.2, y + 2],
    bed_status: 'active',
    sun_exposure: 'unknown',
    locked: false,
    z_order: 0,
    open_task_count: 0,
    overdue_task_count: 0,
    ...overrides,
  };
}

export function gardenObject(
  key: string,
  x: number,
  y: number,
  overrides: Partial<GardenObject> = {},
): GardenObject {
  return {
    key,
    site_key: 'site_1',
    object_type: 'tree',
    label: `Tree ${key}`,
    geometry: { kind: 'circle', origin: [x, y], radius_m: 1 },
    bbox: [x - 1, y - 1, x + 1, y + 1],
    props: { object_type: 'tree', crown_radius_m: 1 },
    off_site: false,
    locked: false,
    z_order: 0,
    ...overrides,
  };
}

export function planResponse(overrides: Partial<GardenPlanResponse> = {}): GardenPlanResponse {
  return {
    schema_version: '1',
    site_key: 'site_1',
    site_name: 'Vegetable garden',
    plan_revision: 42,
    plan: {
      boundary: { kind: 'rect', origin: [0, 0], width_m: 100, length_m: 100, rotation_deg: 0 },
      north_angle_deg: 15,
      default_grid_m: 0.1,
      adjacency_factor: 1.5,
      plan_revision: 42,
    },
    locations: [bed('loc_a', 1, 1), bed('loc_b', 4, 1)],
    garden_objects: [gardenObject('go_1', 20, 20)],
    slots: [
      {
        key: 'slot_1',
        slot_id: 'A_1',
        location_key: 'loc_a',
        plan_geometry: { origin: [1.3, 1.3] },
      },
    ],
    plants: [{ key: 'pl_1', instance_id: 'TOM-1', species_key: 'sp_tomato', slot_key: 'slot_1' }],
    zones: [],
    ...overrides,
  };
}

export function smallPlan(overrides: Partial<GardenPlanResponse> = {}): PlanModel {
  return normalizePlan(planResponse(overrides));
}

/** The "large" class of GP-ACC-033: 150 beds, 300 objects, 3 000 slots, 2 000 plants. */
export function largePlan(): PlanModel {
  const locations: PlanLocation[] = [];
  for (let i = 0; i < 150; i += 1)
    locations.push(bed(`loc_${i}`, (i % 15) * 3, Math.floor(i / 15) * 4));
  const objects: GardenObject[] = [];
  for (let i = 0; i < 300; i += 1)
    objects.push(gardenObject(`go_${i}`, (i % 30) * 3 + 0.5, 60 + Math.floor(i / 30) * 3));
  const slots: PlanSlot[] = [];
  for (let i = 0; i < 3000; i += 1) {
    const location = locations[i % 150];
    slots.push({
      key: `slot_${i}`,
      slot_id: `S${i}`,
      location_key: location.key,
      plan_geometry: { origin: [(i % 7) * 0.15 + 0.1, Math.floor(i / 150) * 0.1 + 0.1] },
    });
  }
  const plants: PlanPlant[] = [];
  for (let i = 0; i < 2000; i += 1) {
    plants.push({
      key: `pl_${i}`,
      instance_id: `P${i}`,
      species_key: `sp_${i % 40}`,
      slot_key: `slot_${i}`,
    });
  }
  return normalizePlan(planResponse({ locations, garden_objects: objects, slots, plants }));
}
