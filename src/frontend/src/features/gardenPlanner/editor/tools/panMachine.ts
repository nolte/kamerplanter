/**
 * The pan tool (REQ-053 GP-FR-010): dragging moves the view by the pointer's travel. The machine
 * emits one `pan` effect per move; the route owns the viewport and applies it.
 */
import type { Point } from '../../model/types';
import type { PointerSample, Step } from './machineTypes';

export interface PanState {
  last: Point | null;
}

export const INITIAL_PAN_STATE: PanState = { last: null };

export function panDown(_state: PanState, sample: PointerSample): Step<PanState> {
  return { state: { last: sample.pointPx }, effects: [] };
}

export function panMove(state: PanState, sample: PointerSample): Step<PanState> {
  if (state.last === null) return { state, effects: [] };
  const dxPx = sample.pointPx[0] - state.last[0];
  const dyPx = sample.pointPx[1] - state.last[1];
  if (dxPx === 0 && dyPx === 0) return { state, effects: [] };
  return { state: { last: sample.pointPx }, effects: [{ type: 'pan', dxPx, dyPx }] };
}

export function panUp(): Step<PanState> {
  return { state: INITIAL_PAN_STATE, effects: [] };
}
