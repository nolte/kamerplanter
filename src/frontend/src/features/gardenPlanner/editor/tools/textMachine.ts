/**
 * The click machine of the tool "Text" (REQ-053 GP-UX-071, #2913). A press that does not travel is a click: it sets
 * the anchor of a new caption - the lower-left corner of its text - at the snapped point (grid, object corners and
 * edges, like a drawn corner; Alt switches the snap off) and asks the editor for the text (`textAnchor`). A press
 * that travels pans the plan: with a finger that is the only way to move it while the tool is on.
 *
 * Pure: the editor carries out the effects. Nothing reaches the plan model until the text is confirmed; then the
 * caption is one `create_garden_object` of the plan batch (one undo step), like a drawn object.
 */
import type { Point } from '../../model/types';
import { dragThresholdPx, distancePx, type Effect, type PointerSample, type Step, type ToolEnv } from './machineTypes';

export type TextState =
  | { kind: 'idle' }
  | { kind: 'press'; startPx: Point; lastPx: Point; pointerType: PointerSample['pointerType']; panning: boolean };

export const INITIAL_TEXT_STATE: TextState = { kind: 'idle' };

export function textDown(sample: PointerSample): TextState {
  return { kind: 'press', startPx: sample.pointPx, lastPx: sample.pointPx, pointerType: sample.pointerType, panning: false };
}

/** A press that travelled past the drag threshold pans by the pointer's step. */
export function textMove(state: TextState, sample: PointerSample): Step<TextState> {
  if (state.kind !== 'press') return { state, effects: [] };
  const panning = state.panning || distancePx(state.startPx, sample.pointPx) > dragThresholdPx(state.pointerType);
  if (!panning) return { state, effects: [] };
  const effects: Effect[] = [
    { type: 'pan', dxPx: sample.pointPx[0] - state.lastPx[0], dyPx: sample.pointPx[1] - state.lastPx[1] },
  ];
  return { state: { ...state, lastPx: sample.pointPx, panning: true }, effects };
}

/** A click (or a tap) at the sample's point: the snapped anchor of the new caption. */
export function textClick(sample: PointerSample, env: ToolEnv): Effect[] {
  const anchor = env.snapPoint(env.toModel(sample.pointPx), sample.alt, sample.pointerType);
  return [
    { type: 'select', selection: [] },
    { type: 'stack', stack: null },
    { type: 'textAnchor', point: anchor },
  ];
}

/** The release: a click sets the anchor; the end of a pan does nothing more. */
export function textUp(state: TextState, sample: PointerSample, env: ToolEnv): Step<TextState> {
  if (state.kind !== 'press') return { state: INITIAL_TEXT_STATE, effects: [] };
  const moved = textMove(state, sample);
  if (moved.state.kind === 'press' && moved.state.panning) {
    return { state: INITIAL_TEXT_STATE, effects: moved.effects };
  }
  return { state: INITIAL_TEXT_STATE, effects: textClick(sample, env) };
}
