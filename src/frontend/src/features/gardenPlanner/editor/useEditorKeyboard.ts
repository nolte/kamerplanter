/**
 * Keyboard operation of the plan canvas beyond what the tools bring (REQ-053 GP-NFR-020/068,
 * GP-UX-045, GP-ACC-008): with something selected the arrow keys move it by one grid step of the editor's grid (the same step the snap uses;
 * Shift: ten steps); with nothing selected - or with another tool - they scroll the view.
 * PageDown/PageUp walk the focus from object to object, `?` opens the key help (a single printable
 * key, so it follows the setting of WCAG 2.1.4). Everything that changes the plan goes out as
 * `PlanOperation`s through `onCommit`; the hook never touches the store.
 */
import {
  useCallback,
  useMemo,
  type KeyboardEvent as ReactKeyboardEvent,
  type RefObject,
} from 'react';
import type { PlanModel } from '../model/planModel';
import type { PlanOperation, Point } from '../model/types';
import type { PlanTool, SelectionRef } from '../state/gardenPlanSlice';
import { isPlanEntity } from './tools/hierarchy';
import { moveOperations } from './tools/keyboardMove';
import type { ActionLabel } from './tools/machineTypes';

/** Pixels the view scrolls per arrow press (Shift: four times that). */
export const SCROLL_STEP_PX = 40;
const COARSE = 10;

const DIRECTIONS: Record<string, Point> = {
  ArrowLeft: [-1, 0],
  ArrowRight: [1, 0],
  ArrowUp: [0, 1], // model y points up
  ArrowDown: [0, -1],
};

export interface EditorKeyboardOptions {
  plan: PlanModel;
  tool: PlanTool;
  selection: readonly SelectionRef[];
  canvasRef: RefObject<HTMLElement | null>;
  singleKeyShortcuts: boolean;
  /** The grid step in metres (the editor's one grid state, shared with the snap): one arrow press moves by it. */
  stepM: number;
  onCommit: (ops: PlanOperation[], label: ActionLabel) => void;
  onNotice: (code: string | null) => void;
  onPan: (dxPx: number, dyPx: number) => void;
  onHelp: () => void;
}

function isTextEntry(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement &&
    (/^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName) || target.isContentEditable)
  );
}

/** The focusable plan objects in the DOM, in reading order. */
function objectNodes(root: HTMLElement | null): HTMLElement[] {
  return root
    ? Array.from(root.querySelectorAll<HTMLElement>('[data-plan-key][role="button"]'))
    : [];
}

export function useEditorKeyboard(options: EditorKeyboardOptions) {
  const { plan, tool, selection, canvasRef, singleKeyShortcuts, stepM } = options;
  const { onCommit, onNotice, onPan, onHelp } = options;

  /** Shifts the selection by `delta` metres; says why not when it cannot (locked, outside, ...). */
  const moveSelection = useCallback(
    (delta: Point) => {
      const result = moveOperations(plan, selection, delta);
      if (result.ok) {
        onNotice(null);
        onCommit(result.ops, 'move');
      } else onNotice(result.notice);
    },
    [onCommit, onNotice, plan, selection],
  );

  /** Handles the key and returns `true`, or returns `false` and leaves it to the tools. */
  const handleKey = useCallback(
    (event: ReactKeyboardEvent<HTMLElement>): boolean => {
      if (isTextEntry(event.target)) return false;
      const direction = DIRECTIONS[event.key];
      if (direction && !event.ctrlKey && !event.metaKey && !event.altKey) {
        event.preventDefault();
        const movable = tool === 'select' && selection.some(isPlanEntity);
        if (movable) {
          const step = stepM * (event.shiftKey ? COARSE : 1);
          moveSelection([direction[0] * step, direction[1] * step]);
        } else {
          const px = SCROLL_STEP_PX * (event.shiftKey ? 4 : 1);
          // Arrow right shows what lies to the right: the plan slides left (see `onPan`).
          onPan(-direction[0] * px + 0, direction[1] * px + 0); // `+ 0`: no negative zero
        }
        return true;
      }
      if (
        (event.key === 'PageDown' || event.key === 'PageUp') &&
        !event.ctrlKey &&
        !event.metaKey
      ) {
        const nodes = objectNodes(canvasRef.current);
        if (nodes.length === 0) return false;
        event.preventDefault();
        const active = nodes.findIndex(
          (node) => node === document.activeElement || node.contains(document.activeElement),
        );
        const next =
          event.key === 'PageDown' ? active + 1 : active < 0 ? nodes.length - 1 : active - 1;
        nodes[(next + nodes.length) % nodes.length].focus();
        return true;
      }
      if (
        event.key === '?' &&
        singleKeyShortcuts &&
        !event.ctrlKey &&
        !event.metaKey &&
        !event.altKey
      ) {
        event.preventDefault();
        onHelp();
        return true;
      }
      return false;
    },
    [canvasRef, moveSelection, onHelp, onPan, selection, singleKeyShortcuts, stepM, tool],
  );

  return useMemo(() => ({ handleKey, moveSelection }), [handleKey, moveSelection]);
}
