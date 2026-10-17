import { describe, expect, it } from 'vitest';
import type { Effect, Step } from './machineTypes';
import {
  drawDown,
  drawFinish,
  drawMove,
  drawOverlay,
  drawUndoPoint,
  drawUp,
  INITIAL_DRAW_STATE,
  pointCount,
  type DrawOptions,
  type DrawState,
} from './drawMachine';
import { at, atPx, makeEnv, testPlan } from './toolTestKit';
import { panDown, panMove, panUp } from './panMachine';

const bedOptions = (shape: DrawOptions['shape']): DrawOptions => ({
  target: 'bed',
  shape,
  newBedName: (n) => `Bed ${n}`,
});
const objectOptions = (shape: DrawOptions['shape']): DrawOptions => ({
  ...bedOptions(shape),
  target: 'garden_object',
});

const commit = (effects: Effect[]) =>
  effects.find((e): e is Extract<Effect, { type: 'commit' }> => e.type === 'commit');

describe('rect and circle are dragged out', () => {
  it('draws a rectangle from corner to corner as one create_location', () => {
    const env = makeEnv(testPlan());
    const opts = bedOptions('rect');
    const down = drawDown(INITIAL_DRAW_STATE, at(env, [16, 14]), env, opts);
    const moved = drawMove(down.state, at(env, [18.5, 16]), env, true);
    const up = drawUp(moved.state, at(env, [18.5, 16]), env, opts);
    const created = commit(up.effects)!;
    expect(created.label).toBe('draw');
    expect(created.ops).toHaveLength(1);
    expect(created.ops[0]).toMatchObject({
      op: 'create_location',
      data: {
        name: 'Bed 6',
        geometry: { kind: 'rect', origin: [16, 14], width_m: 2.5, length_m: 2, rotation_deg: 0 },
      },
    });
    // The new object is selected and the editor returns to the select tool.
    expect(up.effects.find((e) => e.type === 'select')).toMatchObject({
      selection: [{ entity: 'location' }],
    });
    expect(up.effects).toContainEqual({ type: 'tool', tool: 'select' });
    expect(up.state).toEqual(INITIAL_DRAW_STATE);
  });

  it('draws in any drag direction and a square with Shift', () => {
    const env = makeEnv(testPlan());
    const opts = bedOptions('rect');
    const down = drawDown(INITIAL_DRAW_STATE, at(env, [18, 16], { shift: true }), env, opts);
    const up = drawUp(
      drawMove(down.state, at(env, [16, 15], { shift: true }), env, true).state,
      at(env, [16, 15], { shift: true }),
      env,
      opts,
    );
    expect(commit(up.effects)!.ops[0]).toMatchObject({
      data: { geometry: { origin: [16, 14], width_m: 2, length_m: 2 } },
    });
  });

  it('draws a circle from its centre', () => {
    const env = makeEnv(testPlan());
    const opts = objectOptions('circle');
    const down = drawDown(INITIAL_DRAW_STATE, at(env, [17, 15]), env, opts);
    const up = drawUp(
      drawMove(down.state, at(env, [18, 15]), env, true).state,
      at(env, [18, 15]),
      env,
      opts,
    );
    expect(commit(up.effects)!.ops[0]).toMatchObject({
      op: 'create_garden_object',
      data: { object_type: 'other', geometry: { kind: 'circle', origin: [17, 15], radius_m: 1 } },
    });
  });

  it('takes the smallest area holding the shape as its parent and the most common bed type', () => {
    const env = makeEnv(testPlan());
    const opts = bedOptions('rect');
    const down = drawDown(INITIAL_DRAW_STATE, at(env, [9, 5]), env, opts);
    const up = drawUp(
      drawMove(down.state, at(env, [10.5, 6.5]), env, true).state,
      at(env, [10.5, 6.5]),
      env,
      opts,
    );
    expect(commit(up.effects)!.ops[0]).toMatchObject({
      data: { parent_location_key: 'area', location_type_key: 'bed' },
    });
  });

  it('a click without a drag draws nothing', () => {
    const env = makeEnv(testPlan());
    const opts = bedOptions('rect');
    const down = drawDown(INITIAL_DRAW_STATE, at(env, [17, 15]), env, opts);
    const up = drawUp(
      down.state,
      atPx([env.toScreen([17, 15])[0] + 1, env.toScreen([17, 15])[1]]),
      env,
      opts,
    );
    expect(up.effects).toEqual([]);
    expect(up.state).toEqual(INITIAL_DRAW_STATE);
  });

  it('refuses a shape outside the garden boundary with a notice and creates nothing (live validation)', () => {
    const env = makeEnv(testPlan());
    const opts = bedOptions('rect');
    const down = drawDown(INITIAL_DRAW_STATE, at(env, [19, 14]), env, opts);
    const moved = drawMove(down.state, at(env, [22, 16]), env, true);
    expect(drawOverlay(moved.state, env, opts).shapes[0].invalid).toBe(true);
    const up = drawUp(moved.state, at(env, [22, 16]), env, opts);
    expect(commit(up.effects)).toBeUndefined();
    expect(up.effects).toEqual([{ type: 'notice', code: 'geometry.outside_parent' }]);
  });
});

describe('polygon and polyline are built point by point', () => {
  function click(
    state: DrawState,
    env: ReturnType<typeof makeEnv>,
    opts: DrawOptions,
    point: [number, number],
  ) {
    const down = drawDown(state, at(env, point), env, opts);
    return drawUp(down.state, at(env, point), env, opts);
  }

  it('collects points, follows the pointer with a rubber band and closes on the first point', () => {
    const env = makeEnv(testPlan());
    const opts = bedOptions('polygon');
    let step: Step<DrawState> = click(INITIAL_DRAW_STATE, env, opts, [16, 14]);
    step = click(step.state, env, opts, [19, 14]);
    step = click(step.state, env, opts, [19, 17]);
    expect(pointCount(step.state)).toBe(3);
    const hover = drawMove(step.state, at(env, [16, 17]), env, false);
    expect(drawOverlay(hover.state, env, opts).shapes[0]).toMatchObject({ draft: true });
    // A click on the first point finishes the polygon.
    const closed = click(hover.state, env, opts, [16, 14]);
    const created = commit(closed.effects)!;
    expect(created.ops[0]).toMatchObject({
      op: 'create_location',
      data: {
        geometry: {
          kind: 'polygon',
          points: [
            [16, 14],
            [19, 14],
            [19, 17],
          ],
        },
      },
    });
    expect(closed.state).toEqual(INITIAL_DRAW_STATE);
  });

  it('Enter (finish) with too few points reports it and keeps the points', () => {
    const env = makeEnv(testPlan());
    const opts = bedOptions('polygon');
    const first = click(INITIAL_DRAW_STATE, env, opts, [16, 14]);
    const second = click(first.state, env, opts, [19, 14]);
    const finished = drawFinish(second.state, env, opts);
    expect(finished.effects).toEqual([{ type: 'notice', code: 'draw.too_few_points' }]);
    expect(pointCount(finished.state)).toBe(2);
  });

  it('keeps the points of a self-intersecting polygon and says why', () => {
    const env = makeEnv(testPlan());
    const opts = bedOptions('polygon');
    let state: DrawState = INITIAL_DRAW_STATE;
    for (const point of [
      [16, 14],
      [19, 17],
      [19, 14],
      [16, 17],
    ] as [number, number][]) {
      state = click(state, env, opts, point).state;
    }
    const finished = drawFinish(state, env, opts);
    expect(finished.effects).toEqual([{ type: 'notice', code: 'geometry.self_intersecting' }]);
    expect(pointCount(finished.state)).toBe(4);
    // Backspace takes the last point back, after which the rest can be finished.
    expect(pointCount(drawUndoPoint(finished.state))).toBe(3);
  });

  it('a polyline ends with a click on its last point and becomes a garden object with a stroke width', () => {
    const env = makeEnv(testPlan());
    const opts = objectOptions('polyline');
    let state = click(INITIAL_DRAW_STATE, env, opts, [16, 14]).state;
    state = click(state, env, opts, [19, 14]).state;
    const done = click(state, env, opts, [19, 14]);
    expect(commit(done.effects)!.ops[0]).toMatchObject({
      op: 'create_garden_object',
      data: {
        geometry: {
          kind: 'polyline',
          points: [
            [16, 14],
            [19, 14],
          ],
          width_m: 0.3,
        },
      },
    });
  });

  it('a press that turns into a drag adds no point; a repeated position adds none either', () => {
    const env = makeEnv(testPlan());
    const opts = bedOptions('polygon');
    const down = drawDown(INITIAL_DRAW_STATE, at(env, [16, 14]), env, opts);
    const dragged = drawMove(down.state, at(env, [17, 14]), env, true);
    expect(pointCount(drawUp(dragged.state, at(env, [17, 14]), env, opts).state)).toBe(0);
    const one = click(INITIAL_DRAW_STATE, env, opts, [16, 14]);
    expect(pointCount(click(one.state, env, opts, [16, 14]).state)).toBe(1);
  });

  it('Backspace removes the last point and the last remaining one ends the draft', () => {
    const env = makeEnv(testPlan());
    const opts = bedOptions('polygon');
    const one = click(INITIAL_DRAW_STATE, env, opts, [16, 14]);
    expect(drawUndoPoint(one.state)).toEqual(INITIAL_DRAW_STATE);
  });
});

describe('pan tool (GP-FR-010)', () => {
  it('emits the travel of each move and stops on release', () => {
    const down = panDown({ last: null }, atPx([100, 100]));
    const first = panMove(down.state, atPx([110, 95]));
    expect(first.effects).toEqual([{ type: 'pan', dxPx: 10, dyPx: -5 }]);
    const second = panMove(first.state, atPx([112, 95]));
    expect(second.effects).toEqual([{ type: 'pan', dxPx: 2, dyPx: 0 }]);
    expect(panMove(panUp().state, atPx([300, 300])).effects).toEqual([]);
    expect(panMove(second.state, atPx([112, 95])).effects).toEqual([]);
  });
});

describe('type choice and touch taps (WP 2.6)', () => {
  it('creates the bed with the chosen bed type, not the plan default', () => {
    const env = makeEnv(testPlan());
    const opts = { ...bedOptions('rect'), bedTypeKey: 'raised_bed' };
    const down = drawDown(INITIAL_DRAW_STATE, at(env, [16, 14]), env, opts);
    const up = drawUp(down.state, at(env, [18, 16]), env, opts);
    expect(commit(up.effects)!.ops[0]).toMatchObject({
      data: { location_type_key: 'raised_bed' },
    });
  });

  it('creates the object with the chosen type and its required props', () => {
    const env = makeEnv(testPlan());
    const opts = { ...objectOptions('rect'), objectType: 'trellis' as const };
    const down = drawDown(INITIAL_DRAW_STATE, at(env, [16, 14]), env, opts);
    const up = drawUp(down.state, at(env, [18, 16]), env, opts);
    expect(commit(up.effects)!.ops[0]).toMatchObject({
      op: 'create_garden_object',
      data: { object_type: 'trellis', props: { height_m: 1.8 } },
    });
  });

  it('keeps the old placeholder `other` when no type is chosen', () => {
    const env = makeEnv(testPlan());
    const down = drawDown(INITIAL_DRAW_STATE, at(env, [16, 14]), env, objectOptions('rect'));
    const up = drawUp(down.state, at(env, [18, 16]), env, objectOptions('rect'));
    expect(commit(up.effects)!.ops[0]).toMatchObject({ data: { object_type: 'other' } });
  });

  it('a touch tap sets the first corner; the second tap completes the rectangle', () => {
    const env = makeEnv(testPlan());
    const opts = bedOptions('rect');
    const tap = (point: [number, number], state: DrawState) => {
      const sample = at(env, point, { pointerType: 'touch' });
      const down = drawDown(state, sample, env, opts);
      return drawUp(down.state, sample, env, opts);
    };
    const first = tap([16, 14], INITIAL_DRAW_STATE);
    expect(first.state.kind).toBe('corner');
    expect(first.effects).toEqual([]);
    const second = tap([18, 16], first.state);
    expect(commit(second.effects)!.ops[0]).toMatchObject({
      data: { geometry: { origin: [16, 14], width_m: 2, length_m: 2 } },
    });
  });

  it('a mouse click without a drag still creates nothing', () => {
    const env = makeEnv(testPlan());
    const opts = bedOptions('rect');
    const down = drawDown(INITIAL_DRAW_STATE, at(env, [16, 14]), env, opts);
    const up = drawUp(down.state, at(env, [16, 14]), env, opts);
    expect(up.state).toEqual(INITIAL_DRAW_STATE);
  });
});
