/**
 * What the live region says about a finished action (REQ-053 GP-NFR-022/070, GP-ACC-008): the
 * action and its result - "Bed 3 moved to x 1 m, y 1.5 m" - never an intermediate position. Pure:
 * the caller supplies the translation function.
 */
import type { PlanModel } from '../model/planModel';
import type { PlanOperation } from '../model/types';
import type { HistoryEntry } from '../state/gardenPlanSlice';
import { positionOf } from './tools/keyboardMove';

export type Translate = (key: string, options?: Record<string, unknown>) => string;

const PREFIX = 'pages.gardenPlan.editor.liveRegion';
const ACTIONS = [
  'move',
  'rotate',
  'resize',
  'editPoint',
  'draw',
  'delete',
  'edit',
  'lock',
  'unlock',
  'zOrder',
] as const;
type Action = (typeof ACTIONS)[number];
/** Actions that change where an object is: only these name the position (the others leave it as it was). */
const MOVES_OBJECT: readonly Action[] = ['move', 'rotate', 'resize', 'editPoint', 'draw'];

function actionOf(label: string | null): Action | null {
  const last = label?.split('.').pop();
  return ACTIONS.find((action) => action === last) ?? null;
}

function targetOf(op: PlanOperation): { entity: 'location' | 'garden_object'; key: string } | null {
  if ('entity' in op && 'key' in op && (op.entity === 'location' || op.entity === 'garden_object'))
    return { entity: op.entity, key: op.key };
  return null;
}

/** The name of an entity in `plan`, falling back to `before` for one the action removed. */
function nameOf(
  target: { entity: 'location' | 'garden_object'; key: string },
  plan: PlanModel,
  before: PlanModel,
  fallback: string,
): string {
  for (const model of [plan, before]) {
    const name =
      target.entity === 'location'
        ? model.locations[target.key]?.name
        : model.gardenObjects[target.key]?.label;
    if (name) return name;
  }
  return fallback;
}

export function announceAction(
  entry: HistoryEntry,
  plan: PlanModel,
  before: PlanModel,
  t: Translate,
  formatNumber: (value: number) => string,
  fallbackName: string,
): string {
  const action = actionOf(entry.label);
  const targets = entry.ops.flatMap((op) => {
    const target = targetOf(op);
    return target ? [target] : [];
  });
  const first = targets[0];
  if (!action || !first) return t(`${PREFIX}.done`);
  const name = nameOf(first, plan, before, fallbackName);
  // A move of an area moves what is inside; the announcement names what the user acted on.
  const roots = entry.ops.length;
  if (action === 'delete') {
    return roots > 1
      ? t(`${PREFIX}.deletedMany`, { count: roots })
      : t(`${PREFIX}.deleted`, { name });
  }
  const position = positionOf(plan, first);
  if (action === 'move' && position) {
    return t(`${PREFIX}.moved`, {
      name,
      x: formatNumber(position[0]),
      y: formatNumber(position[1]),
    });
  }
  if (position && MOVES_OBJECT.includes(action)) {
    return t(`${PREFIX}.changed`, {
      action: t(`pages.gardenPlan.editor.actions.${action}`),
      name,
      x: formatNumber(position[0]),
      y: formatNumber(position[1]),
    });
  }
  return t(`${PREFIX}.changedNoPosition`, {
    action: t(`pages.gardenPlan.editor.actions.${action}`),
    name,
  });
}
