/**
 * The click machine of the tool "Text" (REQ-053 GP-UX-071, #2913): a click sets the snapped anchor of a new caption
 * and asks for its text; a drag pans; nothing reaches the plan before the text is confirmed.
 */
import { describe, expect, it } from 'vitest';
import type { Effect } from './machineTypes';
import { INITIAL_TEXT_STATE, textClick, textDown, textMove, textUp } from './textMachine';
import { at, atPx, makeEnv, testPlan } from './toolTestKit';

const anchorOf = (effects: Effect[]) => effects.find((effect) => effect.type === 'textAnchor');

describe('the text machine', () => {
  it('turns a click into the snapped anchor of a caption and clears the selection - no commit yet', () => {
    // A half-metre grid: the click at (4.2, 6.9) lands on (4, 7), like a drawn corner.
    const env = makeEnv(testPlan(), {
      selection: [{ entity: 'location', key: 'b1' }],
      snapPoint: ([x, y]) => [Math.round(x * 2) / 2, Math.round(y * 2) / 2],
    });
    const sample = at(env, [4.2, 6.9]);

    const { state, effects } = textUp(textDown(sample), sample, env);

    expect(state).toEqual(INITIAL_TEXT_STATE);
    expect(anchorOf(effects)).toEqual({ type: 'textAnchor', point: [4, 7] });
    expect(effects).toContainEqual({ type: 'select', selection: [] });
    expect(effects.some((effect) => effect.type === 'commit')).toBe(false);
  });

  it('passes Alt and the pointer type to the snap (Alt places freely, a finger snaps wider)', () => {
    const calls: unknown[][] = [];
    const env = makeEnv(testPlan(), {
      snapPoint: (point, bypass, pointerType) => {
        calls.push([bypass, pointerType]);
        return point;
      },
    });

    textClick(at(env, [1, 1], { alt: true, pointerType: 'touch' }), env);

    expect(calls).toEqual([[true, 'touch']]);
  });

  it('pans instead of setting an anchor once the press travels past the drag threshold', () => {
    const env = makeEnv(testPlan());
    const down = textDown(atPx([100, 100]));
    const moved = textMove(down, atPx([120, 100]));

    expect(moved.effects).toEqual([{ type: 'pan', dxPx: 20, dyPx: 0 }]);
    const up = textUp(moved.state, atPx([130, 100]), env);
    expect(anchorOf(up.effects)).toBeUndefined();
    expect(up.effects).toEqual([{ type: 'pan', dxPx: 10, dyPx: 0 }]);
  });

  it('keeps a press inside the threshold a click (a finger gets 8 px, a mouse 4 px)', () => {
    const env = makeEnv(testPlan());
    const finger = textDown(atPx([100, 100], { pointerType: 'touch' }));
    expect(textMove(finger, atPx([106, 100], { pointerType: 'touch' })).effects).toEqual([]);
    expect(anchorOf(textUp(finger, atPx([106, 100], { pointerType: 'touch' }), env).effects)).toBeDefined();

    const mouse = textDown(atPx([100, 100]));
    expect(textMove(mouse, atPx([106, 100])).effects).toHaveLength(1);
  });

  it('ignores a release without a press', () => {
    const env = makeEnv(testPlan());
    expect(textUp(INITIAL_TEXT_STATE, atPx([10, 10]), env)).toEqual({ state: INITIAL_TEXT_STATE, effects: [] });
  });
});
