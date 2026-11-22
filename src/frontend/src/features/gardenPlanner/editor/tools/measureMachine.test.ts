/**
 * The measure tool's machine (REQ-053 GP-UX-071, #2913): points click by click, snapped like a drawn point, the
 * length of every segment and the total, Backspace, Esc (the initial state), finishing by Enter or a click on the last
 * point - and nothing that could reach the plan.
 */
import { describe, expect, it } from 'vitest';
import type { Point } from '../../model/types';
import type { ToolEnv } from './machineTypes';
import {
  INITIAL_MEASURE_STATE,
  measureDown,
  measureFinish,
  measureFinishable,
  measureMove,
  measurePointCount,
  measureRelease,
  measureUndoPoint,
  measureUp,
  measureView,
  polylineLengths,
  type MeasureState,
} from './measureMachine';
import { at, makeEnv, testPlan } from './toolTestKit';

/** A click: press and release at the same model point. */
function click(state: MeasureState, env: ToolEnv, pointM: Point, mods: Parameters<typeof at>[2] = {}): MeasureState {
  const sample = at(env, pointM, mods);
  return measureUp(measureDown(state, sample, env), sample, env);
}

function measured(env: ToolEnv, points: Point[]): MeasureState {
  return points.reduce<MeasureState>((state, point) => click(state, env, point), INITIAL_MEASURE_STATE);
}

describe('polylineLengths', () => {
  it('sums the segments of a polyline', () => {
    expect(polylineLengths([[0, 0], [3, 4], [3, 10]])).toEqual({ segmentsM: [5, 6], totalM: 11 });
    expect(polylineLengths([[1, 1]])).toEqual({ segmentsM: [], totalM: 0 });
  });
});

describe('measuring click by click', () => {
  it('sets the start, follows the pointer with a live line and fixes the segment on the second click', () => {
    const env = makeEnv(testPlan());
    const started = click(INITIAL_MEASURE_STATE, env, [1, 14]);
    expect(measurePointCount(started)).toBe(1);
    // The lone start has no length yet; the hover draws the live line with its length.
    expect(measureView(started)).toMatchObject({ pathM: [[1, 14]], totalM: 0, fixedPoints: 1 });
    const hovering = measureMove(started, at(env, [4, 18]), env, false);
    expect(measureView(hovering)).toMatchObject({ pathM: [[1, 14], [4, 18]], segmentsM: [5], totalM: 5 });
    // The status speaks of fixed points only: the hover is not measured yet.
    expect(measureView(hovering)?.fixedTotalM).toBe(0);

    const fixed = click(hovering, env, [4, 18]);
    expect(measureView(fixed)).toMatchObject({ fixedPoints: 2, fixedTotalM: 5, done: false });
  });

  it('continues as a polyline: a length per segment and the total', () => {
    const env = makeEnv(testPlan());
    const state = measured(env, [
      [1, 14],
      [4, 18],
      [4, 12],
    ]);
    const view = measureView(state)!;
    expect(view.segmentsM).toEqual([5, 6]);
    expect(view.totalM).toBe(11);
    expect(view.fixedTotalM).toBe(11);
  });

  it('snaps every point through env.snapPoint (grid and object snap), Alt passes the bypass on', () => {
    const calls: boolean[] = [];
    // A 1 m grid stands in for the editor's snap.
    const env = makeEnv(testPlan(), {
      snapPoint: ([x, y], bypass) => {
        calls.push(bypass);
        return bypass ? [x, y] : [Math.round(x), Math.round(y)];
      },
    });
    const state = measured(env, [
      [1.2, 13.9],
      [3.8, 18.3],
    ]);
    expect(measureView(state)?.pathM).toEqual([
      [1, 14],
      [4, 18],
    ]);
    expect(measureView(state)?.fixedTotalM).toBe(5);
    const free = click(state, env, [6.4, 18], { alt: true });
    expect(measureView(free)?.pathM[2]).toEqual([6.4, 18]);
    expect(calls).toContain(true);
  });

  it('ignores a press that turned into a drag, and a second click on the same spot', () => {
    const env = makeEnv(testPlan());
    const one = click(INITIAL_MEASURE_STATE, env, [1, 14]);
    const pressed = measureDown(one, at(env, [3, 14]), env);
    const dragged = measureMove(pressed, at(env, [6, 14]), env, true);
    expect(measurePointCount(measureUp(dragged, at(env, [6, 14]), env))).toBe(1);
    // The second click of a double click on the start adds nothing.
    expect(measurePointCount(click(one, env, [1, 14]))).toBe(1);
  });
});

describe('Backspace, Esc and finishing', () => {
  it('takes the last point back with Backspace; the last one gone is the initial state', () => {
    const env = makeEnv(testPlan());
    const state = measured(env, [
      [1, 14],
      [4, 18],
      [4, 12],
    ]);
    const back = measureUndoPoint(state);
    expect(measureView(back)).toMatchObject({ fixedPoints: 2, fixedTotalM: 5 });
    expect(measureUndoPoint(measureUndoPoint(back))).toEqual(INITIAL_MEASURE_STATE);
  });

  it('finishes from two points on by Enter; one point is not enough', () => {
    const env = makeEnv(testPlan());
    const one = click(INITIAL_MEASURE_STATE, env, [1, 14]);
    expect(measureFinishable(one)).toBe(false);
    expect(measureFinish(one)).toBe(one);
    const two = click(one, env, [4, 18]);
    expect(measureFinishable(two)).toBe(true);
    const done = measureFinish(two);
    expect(measureView(done)).toMatchObject({ done: true, fixedTotalM: 5, pathM: [[1, 14], [4, 18]] });
    expect(measureFinishable(done)).toBe(false);
    // A finished measurement no longer follows the pointer.
    expect(measureView(measureMove(done, at(env, [10, 10]), env, false))?.pathM).toHaveLength(2);
  });

  it('finishes on a click on the last point - the second click of a double click', () => {
    const env = makeEnv(testPlan());
    const two = measured(env, [
      [1, 14],
      [4, 18],
    ]);
    const done = click(two, env, [4, 18]);
    expect(measureView(done)).toMatchObject({ done: true, fixedPoints: 2 });
  });

  it('keeps a finished measurement until the next click starts a new one', () => {
    const env = makeEnv(testPlan());
    const done = measureFinish(measured(env, [[1, 14], [4, 18]]));
    const next = click(done, env, [10, 15]);
    expect(measureView(next)).toMatchObject({ done: false, fixedPoints: 1, pathM: [[10, 15]] });
  });

  it('Backspace on a finished measurement opens it again without its last point', () => {
    const env = makeEnv(testPlan());
    const done = measureFinish(measured(env, [[1, 14], [4, 18], [4, 12]]));
    expect(measureView(measureUndoPoint(done))).toMatchObject({ done: false, fixedPoints: 2 });
  });

  it('a cancelled pointer ends only the press, never the measurement', () => {
    const env = makeEnv(testPlan());
    const pressed = measureDown(measured(env, [[1, 14]]), at(env, [3, 14]), env);
    const released = measureRelease(pressed);
    expect(measurePointCount(released)).toBe(1);
    expect(measurePointCount(measureUp(released, at(env, [3, 14]), env))).toBe(1);
  });
});
