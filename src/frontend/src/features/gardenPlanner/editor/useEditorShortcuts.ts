import { useCallback, type KeyboardEvent as ReactKeyboardEvent } from 'react';
import { useAppDispatch } from '@/store/hooks';
import { redo, saveGardenPlan, undo } from '../state/gardenPlanSlice';

/** A field keeps its own undo history and its own Ctrl+Z (WCAG 3.2 predictability, no surprises). */
function isTextField(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement &&
    (/^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName) || target.isContentEditable)
  );
}

/**
 * Undo, redo and save by keyboard (REQ-053 GP-FR-026): Ctrl/Cmd+Z, Ctrl/Cmd+Shift+Z, Ctrl+Y and
 * Ctrl/Cmd+S. Attach the handler to the editor root; it only reacts to keys that come from inside
 * it (a modal rendered in a portal bubbles through the React tree but is not part of the editor)
 * and leaves Ctrl+Z / Ctrl+Y to text fields. Ctrl+S is claimed everywhere in the editor so that the
 * browser's "save page" never opens; a field is left first so that its value is committed.
 */
export function useEditorShortcuts(): (event: ReactKeyboardEvent<HTMLElement>) => void {
  const dispatch = useAppDispatch();
  return useCallback(
    (event) => {
      if (!(event.ctrlKey || event.metaKey) || event.altKey) return;
      if (!(event.target instanceof Node) || !event.currentTarget.contains(event.target)) return;
      const key = event.key.toLowerCase();
      if (key === 's' && !event.shiftKey) {
        event.preventDefault();
        if (isTextField(event.target)) (event.target as HTMLElement).blur(); // commits the field
        void dispatch(saveGardenPlan());
        return;
      }
      if (isTextField(event.target)) return;
      if (key === 'z' && !event.shiftKey) {
        event.preventDefault();
        dispatch(undo());
      } else if ((key === 'z' && event.shiftKey) || (key === 'y' && event.ctrlKey && !event.shiftKey)) {
        event.preventDefault();
        dispatch(redo());
      }
    },
    [dispatch],
  );
}
