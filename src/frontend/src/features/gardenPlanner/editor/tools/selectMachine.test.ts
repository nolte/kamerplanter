import { describe, expect, it } from 'vitest';
import { normalizePlan } from '../../model/planModel';
import type { PolygonGeometry } from '../../model/types';
import type { SelectionRef } from '../../state/gardenPlanSlice';
import type { Effect, PointerSample, Step, ToolEnv } from './machineTypes';
import {
  dragPreview,
  INITIAL_SELECT_STATE,
  moveSnapMark,
  selectCancel,
  selectDown,
  selectMove,
  selectOverlay,
  selectUp,
  type SelectState,
} from './selectMachine';
import { at, atPx, makeEnv, testPlan } from './toolTestKit';
import { bed, planResponse } from '@/test/gardenPlanFixtures';

const ref = (key: string, entity: SelectionRef['entity'] = 'location'): SelectionRef => ({
  entity,
  key,
});

/** Press, optionally drag through `via`, release at the last point. Returns the final state and all effects. */
function gesture(
  env: ToolEnv,
  from: PointerSample,
  via: PointerSample[] = [],
  state: SelectState = INITIAL_SELECT_STATE,
) {
  const effects: Effect[] = [];
  const run = (step: Step<SelectState>) => {
    effects.push(...step.effects);
    return step.state;
  };
  let current = run(selectDown(state, from, env));
  for (const sample of via) current = run(selectMove(current, sample, env));
  const end = via[via.length - 1] ?? from;
  current = run(selectUp(current, end, env));
  return { state: current, effects };
}

const lastOf = <T>(items: T[]): T => items[items.length - 1];
const commits = (effects: Effect[]) => effects.filter((e) => e.type === 'commit');
const selections = (effects: Effect[]) =>
  effects.filter((e): e is Extract<Effect, { type: 'select' }> => e.type === 'select');

describe('click selection (GP-FR-020)', () => {
  it('selects the topmost object under the pointer and remembers the stack under it', () => {
    const env = makeEnv(testPlan());
    const { effects } = gesture(env, at(env, [4, 4]));
    const last = lastOf(selections(effects));
    expect(last.selection).toEqual([ref('b1')]);
    const stack = effects.find((e) => e.type === 'stack');
    expect(stack).toMatchObject({ stack: { keys: ['b1', 'area'], index: 0 } });
  });

  it('selects a plant marker before the bed it stands in (GP-UX-032)', () => {
    const env = makeEnv(testPlan());
    const { effects } = gesture(env, at(env, [3.5, 3.5]));
    expect(lastOf(selections(effects)).selection).toEqual([ref('p1', 'plant')]);
  });

  it('a click on empty ground clears the selection and the stack', () => {
    const env = makeEnv(testPlan(), { selection: [ref('b1')] });
    const { effects } = gesture(env, at(env, [18, 18]));
    expect(lastOf(selections(effects)).selection).toEqual([]);
    expect(effects).toContainEqual({ type: 'stack', stack: null });
  });

  it('Shift+click on empty ground keeps the selection', () => {
    const env = makeEnv(testPlan(), { selection: [ref('b1')] });
    const { effects } = gesture(env, at(env, [18, 18], { shift: true }));
    expect(selections(effects)).toEqual([]);
  });

  it('Shift+click adds an object and Shift+click again removes it', () => {
    const plan = testPlan();
    let env = makeEnv(plan, { selection: [ref('b1')] });
    const added = gesture(env, at(env, [15, 3], { shift: true }));
    expect(lastOf(selections(added.effects)).selection).toEqual([ref('b1'), ref('solo')]);

    env = makeEnv(plan, { selection: [ref('b1'), ref('solo')] });
    const removed = gesture(env, at(env, [15, 3], { shift: true }));
    expect(lastOf(selections(removed.effects)).selection).toEqual([ref('b1')]);
  });

  it('a click on one member of a multi-selection collapses it to that member', () => {
    const env = makeEnv(testPlan(), { selection: [ref('b1'), ref('solo')] });
    const { effects } = gesture(env, at(env, [15, 3]));
    expect(lastOf(selections(effects)).selection).toEqual([ref('solo')]);
  });

  it('a locked object can be selected (hit) like any other', () => {
    const env = makeEnv(testPlan());
    const { effects } = gesture(env, at(env, [15, 9]));
    expect(lastOf(selections(effects)).selection).toEqual([ref('lock')]);
  });
});

describe('stack selection (GP-UX-033)', () => {
  it('a repeated click on the same spot picks the next object below, then wraps', () => {
    const plan = testPlan();
    const first = makeEnv(plan);
    const one = gesture(first, at(first, [4, 4]));
    const stack1 = one.effects.find((e) => e.type === 'stack') as Extract<
      Effect,
      { type: 'stack' }
    >;

    const second = makeEnv(plan, { selection: [ref('b1')], stack: stack1.stack });
    const two = gesture(second, at(second, [4, 4]));
    expect(lastOf(selections(two.effects)).selection).toEqual([ref('area')]);
    const stack2 = two.effects.find((e) => e.type === 'stack') as Extract<
      Effect,
      { type: 'stack' }
    >;
    expect(stack2.stack).toMatchObject({ index: 1 });

    const third = makeEnv(plan, { selection: [ref('area')], stack: stack2.stack });
    const three = gesture(third, at(third, [4, 4]));
    expect(lastOf(selections(three.effects)).selection).toEqual([ref('b1')]);
  });

  it('Alt+click picks the object below the selected one without a prior stack', () => {
    const env = makeEnv(testPlan(), { selection: [ref('b1')] });
    const { effects } = gesture(env, at(env, [4, 4], { alt: true }));
    expect(lastOf(selections(effects)).selection).toEqual([ref('area')]);
  });

  it('a click elsewhere starts a new stack at the top', () => {
    const env = makeEnv(testPlan(), {
      selection: [ref('area')],
      stack: { keys: ['b1', 'area'], index: 1, pointPx: [999, 999] },
    });
    const { effects } = gesture(env, at(env, [4, 4]));
    expect(lastOf(selections(effects)).selection).toEqual([ref('b1')]);
  });
});

describe('marquee (GP-FR-020, GP-UX-037)', () => {
  it('selects what lies completely inside and nothing locked', () => {
    const env = makeEnv(testPlan());
    const { effects } = gesture(env, at(env, [13, 1]), [at(env, [17, 5]), at(env, [17, 11])]);
    // Frame x 13..17, y 1..11: solo (14..16, 2..4) and the locked bed (14..16, 8..10).
    const last = lastOf(selections(effects));
    expect(last.selection).toEqual([ref('solo')]);
  });

  it('draws the frame while dragging', () => {
    const env = makeEnv(testPlan());
    const down = selectDown(INITIAL_SELECT_STATE, at(env, [13, 1]), env);
    const moved = selectMove(down.state, at(env, [17, 5]), env);
    expect(selectOverlay(moved.state).marquee).toMatchObject({ width: 80, height: 80 });
  });

  it('Shift keeps the earlier selection', () => {
    const env = makeEnv(testPlan(), { selection: [ref('b1')] });
    const { effects } = gesture(env, at(env, [13, 1], { shift: true }), [
      at(env, [17, 5], { shift: true }),
    ]);
    expect(lastOf(selections(effects)).selection).toEqual([ref('b1'), ref('solo')]);
  });

  it('a tiny drag on empty ground is a click, not a marquee', () => {
    const env = makeEnv(testPlan(), { selection: [ref('b1')] });
    const { effects } = gesture(env, atPx([380, 20]), [atPx([381, 21])]);
    expect(lastOf(selections(effects)).selection).toEqual([]);
  });
});

describe('moving (GP-FR-021, GP-FR-151, GP-FR-155)', () => {
  it('a drag commits ONE action with one update_geometry', () => {
    const env = makeEnv(testPlan());
    const { effects } = gesture(env, at(env, [4, 4]), [at(env, [4.5, 4.5]), at(env, [5, 5])]);
    const [commit] = commits(effects) as Extract<Effect, { type: 'commit' }>[];
    expect(commits(effects)).toHaveLength(1);
    expect(commit.label).toBe('move');
    expect(commit.ops).toEqual([
      {
        op: 'update_geometry',
        entity: 'location',
        key: 'b1',
        geometry: expect.objectContaining({ origin: [4, 4] }),
      },
    ]);
  });

  it('moving an area moves every child with it - one operation per child, one commit', () => {
    const env = makeEnv(testPlan());
    // (11, 11) is inside the area only.
    const { effects } = gesture(env, at(env, [11, 11]), [at(env, [12, 11]), at(env, [13, 11])]);
    const [commit] = commits(effects) as Extract<Effect, { type: 'commit' }>[];
    expect(commits(effects)).toHaveLength(1);
    const keys = commit.ops.map((op) => (op as { key: string }).key).sort();
    expect(keys).toEqual(['area', 'b1', 'b2', 't1']);
    const area = commit.ops.find((op) => (op as { key: string }).key === 'area') as {
      geometry: { origin: number[] };
    };
    expect(area.geometry.origin).toEqual([4, 2]);
    const child = commit.ops.find((op) => (op as { key: string }).key === 'b1') as {
      geometry: { origin: number[] };
    };
    expect(child.geometry.origin).toEqual([5, 3]);
  });

  it('moves a multi-selection together, a selected child not twice', () => {
    const env = makeEnv(testPlan(), { selection: [ref('solo'), ref('b1'), ref('area')] });
    const { effects } = gesture(env, at(env, [15, 3]), [at(env, [15, 4]), at(env, [15, 5])]);
    const [commit] = commits(effects) as Extract<Effect, { type: 'commit' }>[];
    const keys = commit.ops.map((op) => (op as { key: string }).key);
    expect(new Set(keys).size).toBe(keys.length);
    expect(keys.sort()).toEqual(['area', 'b1', 'b2', 'solo', 't1']);
  });

  it('previews the primary object through the renderer and every moved shape as a ghost', () => {
    const env = makeEnv(testPlan());
    const down = selectDown(INITIAL_SELECT_STATE, at(env, [11, 11]), env);
    const moved = selectMove(down.state, at(env, [12, 11]), env);
    expect(dragPreview(moved.state, env.pxPerM)).toEqual({ key: 'area', dxPx: 20, dyPx: -0 });
    const overlay = selectOverlay(moved.state);
    expect(overlay.shapes).toHaveLength(4);
    expect(overlay.shapes.every((shape) => !shape.invalid)).toBe(true);
  });

  it('feeds the new anchor through the snap seam and lets Alt bypass it (GP-ACC-006 seam)', () => {
    const snapPoint: ToolEnv['snapPoint'] = ([x, y], bypass) =>
      bypass ? [x, y] : [Math.round(x * 5) / 5, Math.round(y * 5) / 5];
    const env = makeEnv(testPlan(), { snapPoint });
    // b1 origin (3, 3); drag by 0.23 m to the right: snapped to the 0.2 grid, +0.2.
    const snapped = gesture(env, at(env, [4, 4]), [at(env, [4.23, 4])]);
    const geometry = (commits(snapped.effects)[0] as Extract<Effect, { type: 'commit' }>)
      .ops[0] as { geometry: { origin: number[] } };
    expect(geometry.geometry.origin[0]).toBeCloseTo(3.2, 3);
    const free = gesture(env, at(env, [4, 4], { alt: true }), [at(env, [4.23, 4], { alt: true })]);
    const freeGeometry = (commits(free.effects)[0] as Extract<Effect, { type: 'commit' }>)
      .ops[0] as { geometry: { origin: number[] } };
    expect(freeGeometry.geometry.origin[0]).toBeCloseTo(3.23, 3);
  });

  it('snaps by every corner of the moved object and reports where the snapped one lands (GP-FR-154)', () => {
    const calls: { sources: readonly number[][]; reference: number[] }[] = [];
    const snapMove: ToolEnv['snapMove'] = (sources, reference) => {
      calls.push({ sources, reference });
      // pretend the upper-right corner (5, 5) of b1 met a corner at (6.5, 5)
      return { delta: [1.5, 0], kind: 'corner', point: [6.5, 5] };
    };
    const env = makeEnv(testPlan(), { snapMove, selection: [{ entity: 'location', key: 'b1' }] });
    const down = selectDown(INITIAL_SELECT_STATE, at(env, [4, 4]), env);
    const moved = selectMove(down.state, at(env, [5.4, 4]), env);
    // b1 is 3..5 x 3..5 with its anchor at a corner: four sources, the anchor is the grid reference
    expect(calls[0].sources).toEqual([
      [3, 3],
      [5, 3],
      [5, 5],
      [3, 5],
    ]);
    expect(calls[0].reference).toEqual([3, 3]);
    expect(moveSnapMark(moved.state)).toEqual({ point: [6.5, 5], kind: 'corner' });
    const up = selectUp(moved.state, at(env, [5.4, 4]), env);
    const op = commits(up.effects)[0] as Extract<Effect, { type: 'commit' }>;
    expect((op.ops[0] as { geometry: { origin: number[] } }).geometry.origin).toEqual([4.5, 3]);
    expect(moveSnapMark(up.state)).toBeNull();
  });

  it('has no move marker when the move did not snap', () => {
    const env = makeEnv(testPlan(), { selection: [{ entity: 'location', key: 'b1' }] });
    const down = selectDown(INITIAL_SELECT_STATE, at(env, [4, 4]), env);
    expect(moveSnapMark(selectMove(down.state, at(env, [5.4, 4]), env).state)).toBeNull();
  });

  it('refuses to move a locked object: no commit, and it says why', () => {
    const env = makeEnv(testPlan());
    const { effects } = gesture(env, at(env, [15, 9]), [at(env, [15, 10]), at(env, [15, 11])]);
    expect(commits(effects)).toHaveLength(0);
    expect(effects.filter((e) => e.type === 'notice')).toEqual([
      { type: 'notice', code: 'object.locked' },
    ]);
  });

  it('refuses a move that would strand a bed outside its area (snap-back with a message, GP-UX-053)', () => {
    const env = makeEnv(testPlan());
    const down = selectDown(INITIAL_SELECT_STATE, at(env, [4, 4]), env);
    const moved = selectMove(down.state, at(env, [12, 4]), env);
    expect(selectOverlay(moved.state).shapes[0].invalid).toBe(true);
    const up = selectUp(moved.state, at(env, [12, 4]), env);
    expect(up.effects).toEqual([{ type: 'notice', code: 'geometry.outside_parent' }]);
  });

  it('a plant is selectable but never moved', () => {
    const env = makeEnv(testPlan());
    const { effects } = gesture(env, at(env, [3.5, 3.5]), [at(env, [4, 4]), at(env, [5, 5])]);
    expect(commits(effects)).toHaveLength(0);
  });

  it('presses below the drag threshold are clicks, not moves', () => {
    const env = makeEnv(testPlan());
    const { effects } = gesture(env, at(env, [4, 4]), [
      atPx([env.toScreen([4, 4])[0] + 2, env.toScreen([4, 4])[1]]),
    ]);
    expect(commits(effects)).toHaveLength(0);
  });

  it('Escape in the middle of a drag drops it: nothing is committed, and the release does nothing', () => {
    const env = makeEnv(testPlan());
    const down = selectDown(INITIAL_SELECT_STATE, at(env, [4, 4]), env);
    const moved = selectMove(down.state, at(env, [5, 5]), env);
    const cancelled = selectCancel(moved.state);
    expect(cancelled.gesture.kind).toBe('idle');
    expect(selectOverlay(cancelled)).toEqual({ shapes: [], marquee: null });
    expect(selectUp(cancelled, at(env, [5, 5]), env).effects).toEqual([]);
  });
});

describe('handles (GP-FR-022)', () => {
  // 60 px per metre: the area is 600 px wide, so it gets all eight handles.
  const zoomed = { originM: [0, 14] as [number, number], pxPerM: 60, widthPx: 900, heightPx: 900 };

  it('dragging the east handle resizes the rect in one commit', () => {
    const env = makeEnv(testPlan(), { selection: [ref('area')], viewport: zoomed });
    const { effects } = gesture(env, at(env, [12, 7]), [at(env, [13, 7]), at(env, [14, 7])]);
    const [commit] = commits(effects) as Extract<Effect, { type: 'commit' }>[];
    expect(commits(effects)).toHaveLength(1);
    expect(commit.label).toBe('resize');
    expect(commit.ops).toEqual([
      {
        op: 'update_geometry',
        entity: 'location',
        key: 'area',
        geometry: expect.objectContaining({ width_m: 12, length_m: 10 }),
      },
    ]);
  });

  it('refuses a resize that would leave children outside (red outline, snap-back)', () => {
    const env = makeEnv(testPlan(), { selection: [ref('area')], viewport: zoomed });
    const down = selectDown(INITIAL_SELECT_STATE, at(env, [12, 7]), env);
    const moved = selectMove(down.state, at(env, [6, 7]), env);
    expect(selectOverlay(moved.state).shapes[0].invalid).toBe(true);
    expect(selectUp(moved.state, at(env, [6, 7]), env).effects).toEqual([
      { type: 'notice', code: 'geometry.outside_parent' },
    ]);
  });

  it('Shift on a corner keeps the aspect ratio', () => {
    const env = makeEnv(testPlan(), { selection: [ref('area')], viewport: zoomed });
    const { effects } = gesture(env, at(env, [12, 12]), [
      at(env, [14, 13], { shift: true }),
      at(env, [15, 13], { shift: true }),
    ]);
    const [commit] = commits(effects) as Extract<Effect, { type: 'commit' }>[];
    const geometry = (commit.ops[0] as { geometry: { width_m: number; length_m: number } })
      .geometry;
    expect(geometry.width_m).toBe(geometry.length_m);
  });

  it('a locked object shows no handles, so the press selects and a drag is refused', () => {
    const env = makeEnv(testPlan(), { selection: [ref('lock')], viewport: zoomed });
    const { effects } = gesture(env, at(env, [16, 9]), [at(env, [17, 9]), at(env, [18, 9])]);
    expect(commits(effects)).toHaveLength(0);
  });

  it('the rotate handle turns the area with its children, snapping to 15 degrees', () => {
    const env = makeEnv(testPlan(), {
      selection: [ref('area')],
      viewport: zoomed,
      angleStepDeg: 15,
    });
    // The handle sits above the top edge at (7, 12 + 32/60); pivot is the centre (7, 7).
    const top: [number, number] = [7, 12 + 32 / 60];
    const target: [number, number] = [
      7 + 6.6 * Math.cos((107 * Math.PI) / 180),
      7 + 6.6 * Math.sin((107 * Math.PI) / 180),
    ];
    const { effects } = gesture(env, at(env, top), [at(env, [6, 13]), at(env, target)]);
    const [commit] = commits(effects) as Extract<Effect, { type: 'commit' }>[];
    expect(commit.label).toBe('rotate');
    const keys = commit.ops.map((op) => (op as { key: string }).key).sort();
    expect(keys).toEqual(['area', 'b1', 'b2', 't1']);
    const area = commit.ops.find((op) => (op as { key: string }).key === 'area') as {
      geometry: { rotation_deg: number };
    };
    expect(area.geometry.rotation_deg).toBe(15);
  });

  it('rotation steps 45/90 and free rotation with Alt', () => {
    const top: [number, number] = [7, 12 + 32 / 60];
    const swing = (deg: number): [number, number] => [
      7 + 6.6 * Math.cos(((90 + deg) * Math.PI) / 180),
      7 + 6.6 * Math.sin(((90 + deg) * Math.PI) / 180),
    ];
    const rotationOf = (step: number, deg: number, alt = false) => {
      const env = makeEnv(testPlan(), {
        selection: [ref('area')],
        viewport: zoomed,
        angleStepDeg: step,
      });
      const { effects } = gesture(env, at(env, top, { alt }), [
        at(env, swing(deg / 2), { alt }),
        at(env, swing(deg), { alt }),
      ]);
      const [commit] = commits(effects) as Extract<Effect, { type: 'commit' }>[];
      return commit
        ? (
            commit.ops.find((op) => (op as { key: string }).key === 'area') as {
              geometry: { rotation_deg: number };
            }
          ).geometry.rotation_deg
        : null;
    };
    // 90 degrees about the centre keeps the footprint, so the live validation lets it through.
    expect(rotationOf(90, 50)).toBe(90);
    expect(rotationOf(15, 20)).toBe(15);
    expect(rotationOf(15, 20, true)).toBeCloseTo(20, 0);
  });
});

describe('polygon points (GP-FR-023)', () => {
  const bigPolygon: PolygonGeometry = {
    kind: 'polygon',
    points: [
      [2, 2],
      [12, 2],
      [12, 12],
      [2, 12],
    ],
    rotation_deg: 0,
  };
  const polyPlan = () =>
    normalizePlan(
      planResponse({
        locations: [
          bed('poly', 2, 2, { geometry: bigPolygon, area_m2: 100, bbox: [2, 2, 12, 12] }),
        ],
        garden_objects: [],
        slots: [],
        plants: [],
      }),
    );
  const zoomed = { originM: [0, 14] as [number, number], pxPerM: 60, widthPx: 900, heightPx: 900 };

  it('dragging a vertex edits that point in one commit', () => {
    const env = makeEnv(polyPlan(), { selection: [ref('poly')], viewport: zoomed });
    const { effects, state } = gesture(env, at(env, [12, 12]), [
      at(env, [13, 13]),
      at(env, [14, 14]),
    ]);
    const [commit] = commits(effects) as Extract<Effect, { type: 'commit' }>[];
    expect(commit.label).toBe('editPoint');
    expect((commit.ops[0] as { geometry: PolygonGeometry }).geometry.points[2]).toEqual([14, 14]);
    expect(state.vertex).toEqual({ key: 'poly', index: 2 });
  });

  it('clicking a vertex picks it without changing the plan', () => {
    const env = makeEnv(polyPlan(), { selection: [ref('poly')], viewport: zoomed });
    const { effects, state } = gesture(env, at(env, [12, 2]));
    expect(commits(effects)).toHaveLength(0);
    expect(state.vertex).toEqual({ key: 'poly', index: 1 });
  });

  it('a click on the "+" of an edge inserts a point there; dragging it places the point', () => {
    const env = makeEnv(polyPlan(), { selection: [ref('poly')], viewport: zoomed });
    const click = gesture(env, at(env, [7, 2]));
    const [inserted] = commits(click.effects) as Extract<Effect, { type: 'commit' }>[];
    expect((inserted.ops[0] as { geometry: PolygonGeometry }).geometry.points).toEqual([
      [2, 2],
      [7, 2],
      [12, 2],
      [12, 12],
      [2, 12],
    ]);
    expect(click.state.vertex).toEqual({ key: 'poly', index: 1 });

    const drag = gesture(env, at(env, [7, 2]), [at(env, [7, 1]), at(env, [7, 0.5])]);
    const [dragged] = commits(drag.effects) as Extract<Effect, { type: 'commit' }>[];
    expect((dragged.ops[0] as { geometry: PolygonGeometry }).geometry.points[1]).toEqual([7, 0.5]);
  });

  it('refuses a point that makes the polygon cross itself (V-02)', () => {
    const env = makeEnv(polyPlan(), { selection: [ref('poly')], viewport: zoomed });
    const { effects } = gesture(env, at(env, [12, 12]), [at(env, [0.5, 5]), at(env, [-1, 5])]);
    expect(commits(effects)).toHaveLength(0);
    expect(effects.some((e) => e.type === 'notice')).toBe(true);
  });
});
