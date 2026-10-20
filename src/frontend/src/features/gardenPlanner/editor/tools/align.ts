/**
 * Align and distribute (REQ-053 GP-FR-029, GP-FR-155): move the selected beds and garden objects so their
 * edges line up or their gaps are equal. The result is ONE list of `update_geometry` operations, so it is one
 * undo step. Locked objects are left out - they neither move nor serve as the reference. A selected area
 * carries what is inside it (GP-FR-151), a child of a selected area is not moved twice. Pure.
 *
 * Plan frame: y points up, so "top" is the largest y.
 */
import { boundingBox } from '../../model/geometry';
import type { PlanModel } from '../../model/planModel';
import type { BoundingBox, PlanOperation, Point } from '../../model/types';
import type { SelectionRef } from '../../state/gardenPlanSlice';
import { translateGeometry } from './geometryEdit';
import { isPlanEntity, moveTargets, selectionRoots, type GeometryEntry } from './hierarchy';
import { firstViolation } from './validation';

export type AlignMode = 'left' | 'right' | 'top' | 'bottom' | 'centerH' | 'centerV';
export type DistributeAxis = 'horizontal' | 'vertical';

/** At least two objects align, at least three distribute (with two there is only one gap). */
export const MIN_ALIGN = 2;
export const MIN_DISTRIBUTE = 3;

interface Item {
  box: BoundingBox;
  targets: GeometryEntry[];
}

export type AlignOutcome =
  | { ok: true; ops: PlanOperation[] }
  | { ok: false; code: 'nothing' | 'object.locked' | string };

/** The roots that may move, with the box they span. `lockedOut` counts the roots left out because they are locked. */
function movableItems(
  plan: PlanModel,
  selection: readonly SelectionRef[],
): { items: Item[]; lockedOut: number } {
  const items: Item[] = [];
  let lockedOut = 0;
  for (const root of selectionRoots(plan, selection.filter(isPlanEntity))) {
    const targets = moveTargets(plan, [root]);
    const own = targets.find((entry) => entry.entity === root.entity && entry.key === root.key);
    if (!own) continue; // not placed on the plan
    if (targets.some((entry) => entry.locked)) {
      lockedOut += 1;
      continue;
    }
    const source =
      root.entity === 'location' ? plan.locations[root.key] : plan.gardenObjects[root.key];
    items.push({ box: source?.bbox ?? boundingBox(own.geometry), targets });
  }
  return { items, lockedOut };
}

/** Whether the selection holds enough movable objects for an alignment / a distribution. */
export function alignAvailability(
  plan: PlanModel,
  selection: readonly SelectionRef[],
): { align: boolean; distribute: boolean } {
  const { items } = movableItems(plan, selection);
  return { align: items.length >= MIN_ALIGN, distribute: items.length >= MIN_DISTRIBUTE };
}

function operationsFor(
  plan: PlanModel,
  moves: readonly { item: Item; delta: Point }[],
): AlignOutcome {
  const draft = moves
    .filter(({ delta }) => delta[0] !== 0 || delta[1] !== 0)
    .flatMap(({ item, delta }) =>
      item.targets.map((entry) => ({
        entity: entry.entity,
        key: entry.key,
        geometry: translateGeometry(entry.geometry, delta),
      })),
    );
  if (draft.length === 0) return { ok: false, code: 'nothing' };
  const violation = firstViolation(plan, draft);
  if (violation) return { ok: false, code: violation };
  return {
    ok: true,
    ops: draft.map(({ entity, key, geometry }) => ({
      op: 'update_geometry' as const,
      entity,
      key,
      geometry,
    })),
  };
}

/** Precision of a computed shift: a hair under the storage precision, so rounding noise is no move. */
const round = (value: number): number => Math.round(value * 1e6) / 1e6;

export function alignSelection(
  plan: PlanModel,
  selection: readonly SelectionRef[],
  mode: AlignMode,
): AlignOutcome {
  const { items, lockedOut } = movableItems(plan, selection);
  if (items.length < MIN_ALIGN) return { ok: false, code: lockedOut > 0 ? 'object.locked' : 'nothing' };
  const minX = Math.min(...items.map((i) => i.box[0]));
  const minY = Math.min(...items.map((i) => i.box[1]));
  const maxX = Math.max(...items.map((i) => i.box[2]));
  const maxY = Math.max(...items.map((i) => i.box[3]));
  const moves = items.map((item): { item: Item; delta: Point } => {
    const [x0, y0, x1, y1] = item.box;
    switch (mode) {
      case 'left':
        return { item, delta: [round(minX - x0), 0] };
      case 'right':
        return { item, delta: [round(maxX - x1), 0] };
      case 'top':
        return { item, delta: [0, round(maxY - y1)] };
      case 'bottom':
        return { item, delta: [0, round(minY - y0)] };
      case 'centerH':
        return { item, delta: [round((minX + maxX) / 2 - (x0 + x1) / 2), 0] };
      case 'centerV':
        return { item, delta: [0, round((minY + maxY) / 2 - (y0 + y1) / 2)] };
    }
  });
  return operationsFor(plan, moves);
}

/**
 * Equal gaps between the boxes along `axis`: the outermost objects stay, the ones between them move. The
 * order is the order of their centres.
 */
export function distributeSelection(
  plan: PlanModel,
  selection: readonly SelectionRef[],
  axis: DistributeAxis,
): AlignOutcome {
  const { items, lockedOut } = movableItems(plan, selection);
  if (items.length < MIN_DISTRIBUTE) return { ok: false, code: lockedOut > 0 ? 'object.locked' : 'nothing' };
  const lo = axis === 'horizontal' ? 0 : 1;
  const hi = lo + 2;
  const sorted = [...items].sort((a, b) => a.box[lo] + a.box[hi] - (b.box[lo] + b.box[hi]));
  const start = Math.min(...sorted.map((i) => i.box[lo]));
  const end = Math.max(...sorted.map((i) => i.box[hi]));
  const widths = sorted.reduce((sum, i) => sum + (i.box[hi] - i.box[lo]), 0);
  const gap = (end - start - widths) / (sorted.length - 1);
  let cursor = start;
  const moves = sorted.map((item): { item: Item; delta: Point } => {
    const shift = round(cursor - item.box[lo]);
    cursor += item.box[hi] - item.box[lo] + gap;
    return { item, delta: axis === 'horizontal' ? [shift, 0] : [0, shift] };
  });
  return operationsFor(plan, moves);
}
