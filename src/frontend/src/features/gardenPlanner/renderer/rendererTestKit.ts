import type { PlanModel } from '../model/planModel';
import { normalizePlan } from '../model/planModel';
import type { PlanPlant, PlanSlot } from '../model/types';
import { bed, gardenObject, largePlan, planResponse } from '@/test/gardenPlanFixtures';
import type { RenderOptions, RenderSelection, RendererLabels, Viewport } from './types';

/** Plain-text labels for tests that do not care about i18n wording. */
export const TEST_LABELS: RendererLabels = {
  canvas: 'Plan',
  canvasRole: 'Plan',
  boundary: 'Boundary',
  bed: ({ name, size, plants, openTasks }) =>
    `${name}, bed, ${size}, ${plants} plants, ${openTasks} tasks`,
  object: ({ label, typeLabel, size }) => `${label}, ${typeLabel}, ${size}`,
  plant: ({ id }) => `Plant ${id}`,
  slot: ({ id }) => `Slot ${id}`,
  cluster: ({ count }) => `${count} plants`,
  objectType: (type) => type,
  size: (_geometry, area) => `${area} m2`,
};

export const NO_SELECTION: RenderSelection = { selectedKeys: new Set() };

export function options(overrides: Partial<RenderOptions> = {}): RenderOptions {
  return { labels: TEST_LABELS, ...overrides };
}

/** Top-left at (`x`, `y`) metres. */
export function viewportAt(
  x: number,
  y: number,
  pxPerM: number,
  widthPx = 1000,
  heightPx = 1000,
): Viewport {
  return { originM: [x, y], pxPerM, widthPx, heightPx };
}

/** A bed with `count` plants in a row `spacingM` apart, each in its own slot. */
export function plantedBed(
  key: string,
  x: number,
  y: number,
  count: number,
  spacingM: number,
): { slots: PlanSlot[]; plants: PlanPlant[] } {
  const slots: PlanSlot[] = [];
  const plants: PlanPlant[] = [];
  for (let i = 0; i < count; i += 1) {
    slots.push({
      key: `${key}_s${i}`,
      slot_id: `${key.toUpperCase()}_${i}`,
      location_key: key,
      plan_geometry: { origin: [x + 0.1 + i * spacingM, y + 0.5] },
    });
    plants.push({
      key: `${key}_p${i}`,
      instance_id: `${key.toUpperCase()}-${i}`,
      species_key: 'sp_tomato',
      slot_key: `${key}_s${i}`,
    });
  }
  return { slots, plants };
}

export { bed, gardenObject, normalizePlan, planResponse };
export type { PlanModel };

/**
 * The "large" class (150 beds, 300 objects, 3 000 slots, 2 000 plants) with every slot placed
 * inside its own bed on a 0.3 m grid, the way a real plan looks: 20 positions per bed, 13 planted.
 * (`largePlan()` scatters its slots near the origin, which is fine for operation benchmarks and
 * useless for anything that draws.)
 */
export function largePlacedPlan(): PlanModel {
  const base = largePlan();
  const slots: PlanSlot[] = [];
  const plants: PlanPlant[] = [];
  for (const location of Object.values(base.locations)) {
    const [x, y] = (location.geometry as { origin: [number, number] }).origin;
    for (let k = 0; k < 20; k += 1) {
      const key = `${location.key}_s${k}`;
      slots.push({
        key,
        slot_id: `${location.key}_${k}`,
        location_key: location.key,
        plan_geometry: { origin: [x + 0.15 + (k % 4) * 0.3, y + 0.2 + Math.floor(k / 4) * 0.35] },
      });
      if (k < 13) {
        plants.push({
          key: `${location.key}_p${k}`,
          instance_id: `${location.key}-${k}`,
          species_key: `sp_${k}`,
          slot_key: key,
        });
      }
    }
  }
  return normalizePlan(
    planResponse({
      locations: Object.values(base.locations),
      garden_objects: Object.values(base.gardenObjects),
      slots,
      plants,
    }),
  );
}
