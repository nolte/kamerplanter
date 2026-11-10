/**
 * Roving tabindex for a tool bar (WAI-ARIA "Toolbar" pattern; REQ-053 GP-UX-066 "wie GP-NFR-068"): the bar is ONE tab
 * stop. Inside, the arrow keys of its orientation move between the enabled buttons (wrapping around), Home and End
 * jump to the first and last. The tab stop is the button that had the focus last; before that the pressed tool, else
 * the first button. Buttons appear and disappear with the tool and the selection, so the tab stop is reapplied after
 * every render of the bar and whenever the focus enters it.
 *
 * Menus opened from the bar live in a portal: their keys bubble through the React tree but not through the DOM, and
 * the bar leaves every key alone whose target is not one of its own buttons.
 */
import {
  useCallback,
  useLayoutEffect,
  useMemo,
  useRef,
  type FocusEvent as ReactFocusEvent,
  type KeyboardEvent as ReactKeyboardEvent,
  type RefObject,
} from 'react';

export type ToolbarOrientation = 'vertical' | 'horizontal';

const KEYS: Record<ToolbarOrientation, { next: string; previous: string }> = {
  vertical: { next: 'ArrowDown', previous: 'ArrowUp' },
  horizontal: { next: 'ArrowRight', previous: 'ArrowLeft' },
};

function itemsOf(bar: HTMLElement | null): HTMLButtonElement[] {
  if (!bar) return [];
  return Array.from(bar.querySelectorAll<HTMLButtonElement>('button')).filter((button) => !button.disabled);
}

export interface RovingToolbar {
  onKeyDown: (event: ReactKeyboardEvent<HTMLElement>) => void;
  onFocus: (event: ReactFocusEvent<HTMLElement>) => void;
}

export function useRovingToolbar(
  barRef: RefObject<HTMLElement | null>,
  orientation: ToolbarOrientation,
): RovingToolbar {
  const current = useRef<HTMLButtonElement | null>(null);

  const apply = useCallback(() => {
    const items = itemsOf(barRef.current);
    if (items.length === 0) return;
    const keep = current.current !== null && items.includes(current.current) ? current.current : null;
    const stop = keep ?? items.find((item) => item.getAttribute('aria-pressed') === 'true') ?? items[0];
    current.current = stop;
    for (const item of items) item.tabIndex = item === stop ? 0 : -1;
  }, [barRef]);

  // Every render may add or remove buttons (draw options, the selection group): one tab stop afterwards.
  useLayoutEffect(() => {
    apply();
  });

  const onFocus = useCallback(
    (event: ReactFocusEvent<HTMLElement>) => {
      const target = event.target;
      if (target instanceof HTMLButtonElement && itemsOf(barRef.current).includes(target)) {
        current.current = target;
        apply();
      }
    },
    [apply, barRef],
  );

  const onKeyDown = useCallback(
    (event: ReactKeyboardEvent<HTMLElement>) => {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const items = itemsOf(barRef.current);
      const index = items.indexOf(event.target as HTMLButtonElement);
      if (index < 0) return; // a key from a menu in a portal, or from something that is no button of the bar
      const { next, previous } = KEYS[orientation];
      let target: number;
      if (event.key === next) target = (index + 1) % items.length;
      else if (event.key === previous) target = (index - 1 + items.length) % items.length;
      else if (event.key === 'Home') target = 0;
      else if (event.key === 'End') target = items.length - 1;
      else return;
      event.preventDefault();
      // The editor moves the selection with the arrow keys: the bar keeps them.
      event.stopPropagation();
      current.current = items[target];
      apply();
      items[target].focus();
    },
    [apply, barRef, orientation],
  );

  return useMemo(() => ({ onKeyDown, onFocus }), [onKeyDown, onFocus]);
}
