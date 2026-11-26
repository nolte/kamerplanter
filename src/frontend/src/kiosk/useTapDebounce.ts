import { useMemo, useRef, type MouseEvent, type PointerEvent } from 'react';

/** UI-NFR-019 R-029 — window in which a second tap counts as an accidental double tap. */
export const KIOSK_TAP_DEBOUNCE_MS = 300;

export interface TapDebounceHandlers {
  onPointerDownCapture: (event: PointerEvent<HTMLElement>) => void;
  onClickCapture: (event: MouseEvent<HTMLElement>) => void;
  onKeyDownCapture: () => void;
}

/**
 * UI-NFR-019 R-029 — global touch debounce for the kiosk shell. Spread the returned capture
 * handlers on the shell's root element: they see every click below it, including those in
 * portalled dialogs and menus (React propagates through the component tree, not the DOM).
 *
 * The measure is the PRESS, not the click. A pointer press that lands within
 * {@link KIOSK_TAP_DEBOUNCE_MS} of the previous one marks the click it produces, and that click
 * is stopped before any handler (or a router link's navigation) sees it. Clicks without a pointer
 * press of their own pass untouched: the click a `<label>` forwards to its control, a
 * `input.click()` a handler issues for a file picker, and every keyboard activation — debouncing
 * those would break controls, and a double tap is a touch phenomenon.
 */
export function useTapDebounce(windowMs: number = KIOSK_TAP_DEBOUNCE_MS): TapDebounceHandlers {
  const lastPressAt = useRef<number | null>(null);
  const suppressClick = useRef(false);

  return useMemo<TapDebounceHandlers>(
    () => ({
      onPointerDownCapture: () => {
        const now = Date.now();
        suppressClick.current = lastPressAt.current !== null && now - lastPressAt.current < windowMs;
        lastPressAt.current = now;
      },
      onClickCapture: (event) => {
        if (!suppressClick.current) return;
        suppressClick.current = false;
        // Both: stopping propagation alone would let an anchor follow its href natively.
        event.preventDefault();
        event.stopPropagation();
      },
      // A press that produced no click (released elsewhere) must not swallow a later key press.
      onKeyDownCapture: () => {
        suppressClick.current = false;
      },
    }),
    [windowMs],
  );
}
