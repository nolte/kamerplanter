import { useMemo, useRef, type MouseEvent, type PointerEvent } from 'react';

/** UI-NFR-019 R-029 — window in which a second tap counts as an accidental double tap. */
export const KIOSK_TAP_DEBOUNCE_MS = 300;

export interface TapDebounceHandlers {
  onPointerDownCapture: (event: PointerEvent<HTMLElement>) => void;
  onPointerUpCapture: () => void;
  onPointerCancelCapture: () => void;
  onClickCapture: (event: MouseEvent<HTMLElement>) => void;
  onKeyDownCapture: () => void;
}

/**
 * UI-NFR-019 R-029 — global touch debounce for the kiosk shell. Spread the returned capture
 * handlers on the shell's root element: they see every click below it, including those in
 * portalled dialogs and menus (React propagates through the component tree, not the DOM).
 *
 * The measure is the PRESS of the primary pointer, and it is a throttle: a press within
 * {@link KIOSK_TAP_DEBOUNCE_MS} of the last ACCEPTED press marks the click it produces, and that
 * click is stopped before any handler (or a router link's navigation) sees it. Swallowed presses
 * do not extend the window, so a deliberate series of taps on a stepper at 200 ms still counts
 * every second one instead of one in total. A second finger (`isPrimary === false`) is ignored.
 *
 * Clicks without a pointer press of their own pass untouched: the click a `<label>` forwards to
 * its control, an `input.click()` a handler issues for a file picker, keyboard activation and an
 * assistive technology's activation. The mark therefore lives only until its own press ends — it
 * is cleared once the click of that press had its chance (after `pointerup`), on `pointercancel`
 * (a scroll flick) and on a key press, so it never swallows a later, press-less click.
 */
export function useTapDebounce(windowMs: number = KIOSK_TAP_DEBOUNCE_MS): TapDebounceHandlers {
  const lastAcceptedAt = useRef<number | null>(null);
  const suppressClick = useRef(false);
  const pressId = useRef(0);

  return useMemo<TapDebounceHandlers>(
    () => ({
      onPointerDownCapture: (event) => {
        if (event.isPrimary === false) return;
        pressId.current += 1;
        const now = Date.now();
        const tooSoon = lastAcceptedAt.current !== null && now - lastAcceptedAt.current < windowMs;
        suppressClick.current = tooSoon;
        if (!tooSoon) lastAcceptedAt.current = now;
      },
      onPointerUpCapture: () => {
        // The click of this press is dispatched in the same task as `pointerup`.
        const id = pressId.current;
        setTimeout(() => {
          if (pressId.current === id) suppressClick.current = false;
        }, 0);
      },
      onPointerCancelCapture: () => {
        suppressClick.current = false;
      },
      onClickCapture: (event) => {
        if (!suppressClick.current) return;
        suppressClick.current = false;
        // Both: stopping propagation alone would let an anchor follow its href natively.
        event.preventDefault();
        event.stopPropagation();
      },
      onKeyDownCapture: () => {
        suppressClick.current = false;
      },
    }),
    [windowMs],
  );
}
