/**
 * The click machine of the tool "Pflanze setzen" (REQ-053 GP-UX-071, #2913). A press that does not travel is a click:
 * on a free point slot it asks the editor to open the plant dialog for that slot (`plantSlot`) and selects the slot;
 * anywhere else it says why nothing opens (`notice`) and, where it helps, selects what was hit or zooms to where the
 * planting spots can be hit. A press that travels pans the plan - with a finger that is the only way to move it while
 * the tool is on, so the tool keeps the gesture the pan tool has.
 *
 * Pure: the editor carries out the effects. Nothing reaches the plan model - the plant is written through the plant
 * API once the dialog is confirmed, outside the plan batch.
 */
import type { Point } from '../../model/types';
import type { SelectionRef } from '../../state/gardenPlanSlice';
import { dragThresholdPx, distancePx, type Effect, type PointerSample, type Step, type ToolEnv } from './machineTypes';
import { plantTargetAt, type PlantTarget } from './plantTarget';
import { keysNearPoint } from './touchGestures';

export type PlantState =
  | { kind: 'idle' }
  | { kind: 'press'; startPx: Point; lastPx: Point; pointerType: PointerSample['pointerType']; panning: boolean };

export const INITIAL_PLANT_STATE: PlantState = { kind: 'idle' };

export interface PlantClickOptions {
  /** The view can zoom: markers hidden by the level of detail are zoomed to instead of only named. */
  canZoom: boolean;
  /** The highest zoom (px per metre). */
  maxPxPerM: number;
}

/** The pointer tolerance around a row slot's line, in pixels (as for a shape edge). */
const ROW_SLOP_PX = 4;

export function plantDown(sample: PointerSample): PlantState {
  return { kind: 'press', startPx: sample.pointPx, lastPx: sample.pointPx, pointerType: sample.pointerType, panning: false };
}

/** A press that travelled past the drag threshold pans by the pointer's step. */
export function plantMove(state: PlantState, sample: PointerSample): Step<PlantState> {
  if (state.kind !== 'press') return { state, effects: [] };
  const panning = state.panning || distancePx(state.startPx, sample.pointPx) > dragThresholdPx(state.pointerType);
  if (!panning) return { state, effects: [] };
  const effects: Effect[] = [
    { type: 'pan', dxPx: sample.pointPx[0] - state.lastPx[0], dyPx: sample.pointPx[1] - state.lastPx[1] },
  ];
  return { state: { ...state, lastPx: sample.pointPx, panning: true }, effects };
}

const select = (ref: SelectionRef): Effect[] => [
  { type: 'select', selection: [ref] },
  { type: 'stack', stack: null },
];

/** The effects of a click on `target`. */
export function plantEffects(target: PlantTarget, pointPx: Point, options: PlantClickOptions): Effect[] {
  switch (target.kind) {
    case 'free':
      return [...select({ entity: 'slot', key: target.slotKey }), { type: 'plantSlot', bedKey: target.bedKey, slotKey: target.slotKey }];
    case 'occupied':
      return [
        ...select(
          target.plantKey ? { entity: 'plant', key: target.plantKey } : { entity: 'slot', key: target.slotKey },
        ),
        { type: 'notice', code: 'plant.occupied' },
      ];
    case 'reserved':
      return [...select({ entity: 'slot', key: target.slotKey }), { type: 'notice', code: 'plant.reserved' }];
    case 'rowSlot':
      return [...select({ entity: 'location', key: target.bedKey }), { type: 'notice', code: 'plant.row_slot' }];
    case 'noSlots':
      // The bed's panel holds the way on: "Bepflanzen" / "Details öffnen" lead to the bed page that lays out spots.
      return [...select({ entity: 'location', key: target.bedKey }), { type: 'notice', code: 'plant.no_slots' }];
    case 'zoomIn':
      return options.canZoom
        ? [
            { type: 'zoom', pxPerM: target.pxPerM, anchorPx: pointPx },
            { type: 'notice', code: 'plant.zoomed_in' },
          ]
        : [{ type: 'notice', code: 'plant.zoom_in' }];
    case 'missed':
      return [{ type: 'notice', code: 'plant.missed' }];
    case 'noBed':
      return [{ type: 'notice', code: 'plant.no_bed' }];
  }
}

/** The release: a click resolves its target; the end of a pan does nothing more. */
export function plantUp(
  state: PlantState,
  sample: PointerSample,
  env: ToolEnv,
  options: PlantClickOptions,
): Step<PlantState> {
  if (state.kind !== 'press') return { state: INITIAL_PLANT_STATE, effects: [] };
  const moved = plantMove(state, sample);
  if (moved.state.kind === 'press' && moved.state.panning) {
    return { state: INITIAL_PLANT_STATE, effects: moved.effects };
  }
  return { state: INITIAL_PLANT_STATE, effects: plantClick(sample, env, options) };
}

/** A click (or a tap) at the sample's point: what lies under it, for a finger also what lies around it. */
export function plantClick(sample: PointerSample, env: ToolEnv, options: PlantClickOptions): Effect[] {
  const keys =
    sample.pointerType === 'touch' ? keysNearPoint(env.hitTestAll, sample.pointPx) : env.hitTestAll(sample.pointPx);
  const target = plantTargetAt(
    env.plan,
    keys,
    env.toModel(sample.pointPx),
    env.pxPerM,
    ROW_SLOP_PX / env.pxPerM,
    options.maxPxPerM,
  );
  return plantEffects(target, sample.pointPx, options);
}
