/**
 * The click machine of "Pflanze setzen" (REQ-053 GP-UX-071, #2913): one plant into exactly the free point slot
 * clicked - and for every other click a reason instead of a guess.
 */
import { describe, expect, it } from 'vitest';
import type { PlanModel } from '../../model/planModel';
import type { PlanSlot } from '../../model/types';
import { MARKER_MIN_SPACING_PX } from '../../renderer/lod';
import { plantDown, plantMove, plantUp, INITIAL_PLANT_STATE } from './plantMachine';
import { freePointSlots, plantTargetAt, slotState } from './plantTarget';
import { at, atPx, makeEnv, testPlan, VIEWPORT } from './toolTestKit';
import type { Effect } from './machineTypes';

const OPTIONS = { canZoom: true, maxPxPerM: 2000 };

/**
 * The test plan with a real area (`is_area`), a row slot in bed 2, a reserved and a free spot in "Solo" and a slot of
 * bed 1 occupied by its flag only.
 */
function plan(): PlanModel {
  const base = testPlan();
  const slots: Record<string, PlanSlot> = {
    ...base.slots,
    row: {
      key: 'row',
      slot_id: 'B2_R1',
      location_key: 'b2',
      plan_geometry: { kind: 'polyline', points: [[6.2, 4], [7.8, 4]], width_m: 0.1 },
    },
    reserved: {
      key: 'reserved',
      slot_id: 'SOLO_1',
      location_key: 'solo',
      planned_from: '2026-12-01',
      plan_geometry: { origin: [14.5, 2.5] },
    },
    soloFree: { key: 'soloFree', slot_id: 'SOLO_2', location_key: 'solo', plan_geometry: { origin: [15.5, 3.5] } },
    flagged: {
      key: 'flagged',
      slot_id: 'B1_3',
      location_key: 'b1',
      currently_occupied: true,
      plan_geometry: { origin: [3.5, 4.5] },
    },
  };
  return {
    ...base,
    locations: { ...base.locations, area: { ...base.locations.area, is_area: true } },
    slots,
  };
}

/** The effects of a click at a model point with the mouse (or the finger). */
function clickAt(model: PlanModel, point: [number, number], pointerType: 'mouse' | 'touch' = 'mouse', zoom = true) {
  const env = makeEnv(model);
  const sample = at(env, point, { pointerType });
  return plantUp(plantDown(sample), sample, env, { ...OPTIONS, canZoom: zoom }).effects;
}

const ofType = <T extends Effect['type']>(effects: Effect[], type: T) =>
  effects.filter((effect): effect is Extract<Effect, { type: T }> => effect.type === type);

describe('plantTargetAt / the click on a planting spot', () => {
  it('a free point slot: selects it and asks for the dialog of exactly that slot and bed', () => {
    const effects = clickAt(plan(), [4.5, 4.5]);
    expect(ofType(effects, 'plantSlot')).toEqual([{ type: 'plantSlot', bedKey: 'b1', slotKey: 's2' }]);
    expect(ofType(effects, 'select')).toEqual([{ type: 'select', selection: [{ entity: 'slot', key: 's2' }] }]);
    expect(ofType(effects, 'notice')).toEqual([]);
  });

  it('an occupied slot: no dialog - the plant is selected and the status says why', () => {
    const effects = clickAt(plan(), [3.5, 3.5]);
    expect(ofType(effects, 'plantSlot')).toEqual([]);
    expect(ofType(effects, 'select')[0].selection).toEqual([{ entity: 'plant', key: 'p1' }]);
    expect(ofType(effects, 'notice')).toEqual([{ type: 'notice', code: 'plant.occupied' }]);
  });

  it('a slot occupied by its flag alone counts as occupied, too (no plant known to the plan)', () => {
    const effects = clickAt(plan(), [3.5, 4.5]);
    expect(ofType(effects, 'plantSlot')).toEqual([]);
    expect(ofType(effects, 'select')[0].selection).toEqual([{ entity: 'slot', key: 'flagged' }]);
    expect(ofType(effects, 'notice')[0].code).toBe('plant.occupied');
  });

  it('a slot reserved by a planned run is not offered', () => {
    const effects = clickAt(plan(), [14.5, 2.5]);
    expect(ofType(effects, 'plantSlot')).toEqual([]);
    expect(ofType(effects, 'notice')[0].code).toBe('plant.reserved');
  });

  it('a row slot is sown in the bed: a status, no dialog', () => {
    const effects = clickAt(plan(), [7, 4]);
    expect(ofType(effects, 'plantSlot')).toEqual([]);
    expect(ofType(effects, 'notice')[0].code).toBe('plant.row_slot');
  });

  it('a bed without planting spots: the bed is selected (its panel leads on) and the status says where spots are made', () => {
    const base = plan();
    const model = { ...base, slots: Object.fromEntries(Object.entries(base.slots).filter(([, s]) => s.location_key !== 'b2')) };
    const effects = clickAt(model, [7, 4]);
    expect(ofType(effects, 'select')[0].selection).toEqual([{ entity: 'location', key: 'b2' }]);
    expect(ofType(effects, 'notice')[0].code).toBe('plant.no_slots');
    expect(ofType(effects, 'plantSlot')).toEqual([]);
  });

  it('a miss beside the spots of a bed says so', () => {
    expect(ofType(clickAt(plan(), [4.6, 3.3]), 'notice')[0].code).toBe('plant.missed');
  });

  it('an area, a garden object or empty ground is no bed', () => {
    expect(ofType(clickAt(plan(), [10, 6]), 'notice')[0].code).toBe('plant.no_bed'); // inside the area only
    expect(ofType(clickAt(plan(), [9, 9]), 'notice')[0].code).toBe('plant.no_bed'); // the tree
    expect(ofType(clickAt(plan(), [18, 18]), 'notice')[0].code).toBe('plant.no_bed'); // empty ground
  });

  it('markers hidden by the level of detail: zooms around the click to where they can be hit, and says so', () => {
    const model = plan();
    // 1 px per metre: bed 1's spots (1 m apart) are far below the 10 px marker spacing.
    const viewport = { ...VIEWPORT, pxPerM: 1, originM: [0, 400] as [number, number] };
    const env = makeEnv(model, { viewport });
    const sample = at(env, [4, 4]);
    const effects = plantUp(plantDown(sample), sample, env, OPTIONS).effects;
    const [zoom] = ofType(effects, 'zoom');
    expect(zoom.anchorPx).toEqual(sample.pointPx);
    // At the new zoom the spots are at least the marker spacing apart.
    expect(zoom.pxPerM * 1).toBeGreaterThanOrEqual(MARKER_MIN_SPACING_PX);
    expect(ofType(effects, 'notice')[0].code).toBe('plant.zoomed_in');
    expect(ofType(effects, 'plantSlot')).toEqual([]);
    // Without a zoom it only says to zoom in.
    const plain = plantUp(plantDown(sample), sample, env, { ...OPTIONS, canZoom: false }).effects;
    expect(ofType(plain, 'zoom')).toEqual([]);
    expect(ofType(plain, 'notice')[0].code).toBe('plant.zoom_in');
  });

  it('a finger finds the free spot within a fingertip, not only under its exact pixel', () => {
    const model = plan();
    const env = makeEnv(model);
    const spot = env.toScreen([15.5, 3.5]);
    const sample = atPx([spot[0] + 10, spot[1]], { pointerType: 'touch' });
    const effects = plantUp(plantDown(sample), sample, env, OPTIONS).effects;
    expect(ofType(effects, 'plantSlot')).toEqual([{ type: 'plantSlot', bedKey: 'solo', slotKey: 'soloFree' }]);
  });
});

describe('plantMove / a drag pans instead of clicking', () => {
  it('pans by the pointer step past the threshold and opens nothing on release', () => {
    const env = makeEnv(plan());
    const start = at(env, [4.5, 4.5]);
    const far = atPx([start.pointPx[0] + 30, start.pointPx[1] + 10]);
    const moved = plantMove(plantDown(start), far);
    expect(ofType(moved.effects, 'pan')).toEqual([{ type: 'pan', dxPx: 30, dyPx: 10 }]);
    const released = plantUp(moved.state, far, env, OPTIONS);
    expect(ofType(released.effects, 'plantSlot')).toEqual([]);
    expect(released.state).toEqual(INITIAL_PLANT_STATE);
  });

  it('a jitter below the threshold is still a click', () => {
    const env = makeEnv(plan());
    const start = at(env, [4.5, 4.5]);
    const jitter = atPx([start.pointPx[0] + 2, start.pointPx[1]]);
    const moved = plantMove(plantDown(start), jitter);
    expect(moved.effects).toEqual([]);
    expect(ofType(plantUp(moved.state, jitter, env, OPTIONS).effects, 'plantSlot')).toHaveLength(1);
  });
});

describe('slotState / freePointSlots', () => {
  it('lists only the free point slots of a bed, in slot order', () => {
    const model = plan();
    expect(freePointSlots(model, 'b1').map((slot) => slot.key)).toEqual(['s2']);
    expect(freePointSlots(model, 'solo').map((slot) => slot.key)).toEqual(['soloFree']);
    expect(freePointSlots(model, 'b2')).toEqual([]); // a row is no point slot
    expect(slotState(model, 's1')).toEqual({ state: 'occupied', plantKey: 'p1' });
    expect(slotState(model, 'reserved')).toEqual({ state: 'reserved' });
    expect(slotState(model, 'nope')).toEqual({ state: 'missing' });
  });

  it('plantTargetAt names the bed of a hit marker, whatever key the renderer reports for it', () => {
    const model = plan();
    expect(plantTargetAt(model, ['p1', 'b1', 'area'], [3.5, 3.5], 40, 0.1, 2000)).toEqual({
      kind: 'occupied',
      bedKey: 'b1',
      slotKey: 's1',
      plantKey: 'p1',
    });
  });
});
