/**
 * The area target of the draw machine (REQ-053 GP-UX-071, §9.5, #2913): the tool "Bereich" draws an area location as a
 * rect or a polygon. Pinned here: the create operation (type, name, geometry, inferred parent), the parent rule - a bed
 * drawn inside the area afterwards gets the area as its parent, an area never lies in a bed - and the notice when an
 * area is drawn around what is there already (no re-parenting). Also: the bed default ignores areas.
 */
import { describe, expect, it } from 'vitest';
import { applyOperation } from '../../model/applyOperation';
import type { PlanModel } from '../../model/planModel';
import type { Point } from '../../model/types';
import {
  commonBedTypeKey,
  drawDown,
  drawFinish,
  drawMove,
  drawUp,
  INITIAL_DRAW_STATE,
  NOTICE_AREA_ENCLOSES_EXISTING,
  type DrawOptions,
  type DrawState,
} from './drawMachine';
import type { Effect, Step } from './machineTypes';
import { at, makeEnv, testPlan } from './toolTestKit';

const areaOptions = (shape: DrawOptions['shape'] = 'rect'): DrawOptions => ({
  target: 'area',
  shape,
  newBedName: (n) => `Bed ${n}`,
  newAreaName: (n) => `Area ${n}`,
  areaTypeKey: 'terrace',
});
const bedOptions: DrawOptions = { target: 'bed', shape: 'rect', newBedName: (n) => `Bed ${n}` };

/**
 * The tool test plan with its `area` location marked an area, as the server reads it: area (2,2)-(12,12) holding the
 * beds b1 (3,3) and b2 (6,3) and the tree t1; alone: the beds solo (14,2) and lock (14,8). Boundary 20 x 20.
 */
function areaPlan(): PlanModel {
  const plan = testPlan();
  return {
    ...plan,
    areaTypeKeys: ['area', 'garden', 'terrace'],
    locations: { ...plan.locations, area: { ...plan.locations.area, is_area: true } },
  };
}

const commitOf = (effects: Effect[]) =>
  effects.find((e): e is Extract<Effect, { type: 'commit' }> => e.type === 'commit');

function dragRect(plan: PlanModel, opts: DrawOptions, from: Point, to: Point): Step<DrawState> {
  const env = makeEnv(plan);
  const down = drawDown(INITIAL_DRAW_STATE, at(env, from), env, opts);
  return drawUp(drawMove(down.state, at(env, to), env, true).state, at(env, to), env, opts);
}

describe('the area tool draws an area location', () => {
  it('creates one create_location with the chosen area type, the next area name and no parent outside every area', () => {
    const step = dragRect(areaPlan(), areaOptions(), [13, 13], [19, 18]);
    const created = commitOf(step.effects)!;
    expect(created.ops).toHaveLength(1);
    expect(created.ops[0]).toMatchObject({
      op: 'create_location',
      data: {
        // One area exists: this is the second. Beds are numbered on their own.
        name: 'Area 2',
        location_type_key: 'terrace',
        geometry: { kind: 'rect', origin: [13, 13], width_m: 6, length_m: 5, rotation_deg: 0 },
      },
    });
    expect('parent_location_key' in (created.ops[0] as { data: object }).data).toBe(false);
    expect(step.effects).toContainEqual({ type: 'tool', tool: 'select' });
    expect(step.effects.some((e) => e.type === 'notice')).toBe(false);
  });

  it('draws a polygon area point by point', () => {
    const plan = areaPlan();
    const env = makeEnv(plan);
    const opts = areaOptions('polygon');
    let state: DrawState = INITIAL_DRAW_STATE;
    for (const point of [
      [13, 13],
      [19, 13],
      [16, 18],
    ] as Point[]) {
      state = drawDown(state, at(env, point), env, opts).state;
      state = drawUp(state, at(env, point), env, opts).state;
    }
    const finished = drawFinish(state, env, opts);
    expect(commitOf(finished.effects)!.ops[0]).toMatchObject({
      op: 'create_location',
      data: { location_type_key: 'terrace', geometry: { kind: 'polygon' } },
    });
  });

  it('takes the area around it as its parent, never a bed: an area drawn inside a bed hangs below the area', () => {
    // (3.2, 3.2)-(4.8, 4.8) lies inside bed b1 and inside the area around b1. A bed would win for a bed (smaller);
    // for an area only an area qualifies.
    const step = dragRect(areaPlan(), areaOptions(), [3.2, 3.2], [4.8, 4.8]);
    expect(commitOf(step.effects)!.ops[0]).toMatchObject({ data: { parent_location_key: 'area' } });
    const asBed = dragRect(areaPlan(), bedOptions, [3.2, 3.2], [4.8, 4.8]);
    expect(commitOf(asBed.effects)!.ops[0]).toMatchObject({ data: { parent_location_key: 'b1' } });
  });

  it('becomes the parent of a bed drawn inside it afterwards', () => {
    const drawn = commitOf(dragRect(areaPlan(), areaOptions(), [13, 13], [19, 18]).effects)!;
    const op = drawn.ops[0];
    const withArea = applyOperation(areaPlan(), op).plan;
    const areaKey = (op as { temp_key: string }).temp_key;
    // Drawn as an area before the save: its type is an area type of the plan.
    expect(withArea.locations[areaKey].is_area).toBe(true);

    const bed = commitOf(dragRect(withArea, bedOptions, [14, 14], [16, 15]).effects)!;
    expect(bed.ops[0]).toMatchObject({
      op: 'create_location',
      data: { parent_location_key: areaKey, location_type_key: 'bed', name: 'Bed 5' },
    });
  });

  it('drawn around a bed that is there already: created, the bed keeps its parent, and a notice says so', () => {
    // (13, 1)-(17, 5) encloses the bed "solo" (14,2) 2 x 2, which hangs below nothing.
    const step = dragRect(areaPlan(), areaOptions(), [13, 1], [17, 5]);
    const created = commitOf(step.effects)!;
    expect(created.ops).toHaveLength(1);
    expect(created.ops[0]).toMatchObject({ op: 'create_location', data: { location_type_key: 'terrace' } });
    expect(step.effects).toContainEqual({ type: 'notice', code: NOTICE_AREA_ENCLOSES_EXISTING });
    // No re-parent: the one operation is the area's own.
    const after = applyOperation(areaPlan(), created.ops[0]).plan;
    expect(after.locations.solo.parent_location_key ?? null).toBeNull();
  });
});

describe('the bed default ignores areas', () => {
  it('keeps the bed type most beds have even when areas outnumber them', () => {
    const plan = areaPlan();
    const area = plan.locations.area;
    const locations = {
      solo: { ...plan.locations.solo, location_type_key: 'raised_bed' },
      g1: { ...area, key: 'g1', location_type_key: 'garden' },
      g2: { ...area, key: 'g2', location_type_key: 'garden' },
      g3: { ...area, key: 'g3', location_type_key: 'garden' },
    };
    expect(commonBedTypeKey({ ...plan, locations })).toBe('raised_bed');
  });
});
