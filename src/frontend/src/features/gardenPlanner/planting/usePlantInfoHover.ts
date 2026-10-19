import { useCallback, useEffect, useRef, useState } from 'react';

/** How long the pointer rests on a marker before the bubble appears (GP-UX-058). */
export const HOVER_DELAY_MS = 300;
/** How long the bubble survives the pointer leaving; enough to cross the gap from marker to bubble. */
export const LEAVE_GRACE_MS = 150;

export interface OpenPlantInfo {
  key: string;
  source: 'hover' | 'focus';
}

interface Options {
  /** The plant key under a client point, or `null`. */
  keyAt: (clientX: number, clientY: number) => string | null;
  /** No bubble while the user draws, drags, zooms or pans (GP-UX-058). */
  suppressed?: boolean;
}

export interface PlantInfoHover {
  open: OpenPlantInfo | null;
  onPointerMove: (event: { clientX: number; clientY: number; pointerType: string }) => void;
  onPointerLeave: () => void;
  onBubbleEnter: () => void;
  onBubbleLeave: () => void;
  /** A marker took keyboard focus: show its info at once (GP-FR-190). */
  openByFocus: (key: string) => void;
  /** Focus left the canvas: a bubble opened by focus goes away. */
  closeFocus: () => void;
  close: () => void;
}

/**
 * Timing of the hover bubble: opens after {@link HOVER_DELAY_MS} on a marker, stays while the pointer is on the
 * marker **or** the bubble, closes with Esc and does not reopen for the same marker until the pointer has left
 * it (WCAG 1.4.13: dismissible, hoverable, persistent). Touch never hovers - a tap opens the sheet instead.
 */
export function usePlantInfoHover({ keyAt, suppressed = false }: Options): PlantInfoHover {
  const [open, setOpen] = useState<OpenPlantInfo | null>(null);
  const openRef = useRef<OpenPlantInfo | null>(null);
  const pending = useRef<{ key: string; timer: number } | null>(null);
  const closeTimer = useRef<number | null>(null);
  const overBubble = useRef(false);
  const dismissed = useRef<string | null>(null);

  const apply = useCallback((next: OpenPlantInfo | null) => {
    openRef.current = next;
    setOpen(next);
  }, []);
  const clearPending = useCallback(() => {
    if (pending.current) window.clearTimeout(pending.current.timer);
    pending.current = null;
  }, []);
  const clearClose = useCallback(() => {
    if (closeTimer.current !== null) window.clearTimeout(closeTimer.current);
    closeTimer.current = null;
  }, []);
  const scheduleClose = useCallback(() => {
    clearClose();
    closeTimer.current = window.setTimeout(() => {
      closeTimer.current = null;
      if (!overBubble.current && openRef.current?.source === 'hover') apply(null);
    }, LEAVE_GRACE_MS);
  }, [apply, clearClose]);

  const close = useCallback(() => {
    clearPending();
    clearClose();
    overBubble.current = false;
    apply(null);
  }, [apply, clearClose, clearPending]);

  // Drawing, dragging or zooming starts: the bubble goes at once (state adjusted during render, the documented
  // derived-state pattern) and a dwell still running is dropped.
  if (suppressed && open !== null) setOpen(null);
  useEffect(() => {
    openRef.current = open;
  }, [open]);
  useEffect(() => {
    if (!suppressed) return;
    clearPending();
    clearClose();
    overBubble.current = false;
  }, [suppressed, clearPending, clearClose]);

  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      dismissed.current = openRef.current?.key ?? null;
      close();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open, close]);

  useEffect(
    () => () => {
      if (pending.current) window.clearTimeout(pending.current.timer);
      if (closeTimer.current !== null) window.clearTimeout(closeTimer.current);
    },
    [],
  );

  const onPointerMove = useCallback(
    (event: { clientX: number; clientY: number; pointerType: string }) => {
      if (suppressed || event.pointerType === 'touch') return;
      const key = keyAt(event.clientX, event.clientY);
      if (key !== dismissed.current) dismissed.current = null;
      if (key === null) {
        clearPending();
        if (openRef.current?.source === 'hover') scheduleClose();
        return;
      }
      if (key === dismissed.current) return;
      if (openRef.current?.key === key) {
        clearClose();
        return;
      }
      if (pending.current?.key === key) return;
      clearPending();
      pending.current = {
        key,
        timer: window.setTimeout(() => {
          pending.current = null;
          clearClose();
          apply({ key, source: 'hover' });
        }, HOVER_DELAY_MS),
      };
    },
    [apply, clearClose, clearPending, keyAt, scheduleClose, suppressed],
  );

  return {
    open,
    onPointerMove,
    onPointerLeave: useCallback(() => {
      clearPending();
      dismissed.current = null;
      if (openRef.current?.source === 'hover') scheduleClose();
    }, [clearPending, scheduleClose]),
    onBubbleEnter: useCallback(() => {
      overBubble.current = true;
      clearClose();
    }, [clearClose]),
    onBubbleLeave: useCallback(() => {
      overBubble.current = false;
      scheduleClose();
    }, [scheduleClose]),
    openByFocus: useCallback(
      (key: string) => {
        if (suppressed) return;
        clearPending();
        clearClose();
        dismissed.current = null;
        apply({ key, source: 'focus' });
      },
      [apply, clearClose, clearPending, suppressed],
    ),
    closeFocus: useCallback(() => {
      if (openRef.current?.source === 'focus') apply(null);
    }, [apply]),
    close,
  };
}
