/**
 * The width the canvas has without a docked side panel (#3034): the canvas row less the tool rail and its gap. The
 * panel's form is decided from it (`sidePanelVariant`), so it is measured on the page - the app sidebar, the page
 * padding and the rail count, a viewport breakpoint alone would not see them.
 *
 * Docking the panel does not change this width (the canvas shrinks, the row does not), so the decision cannot
 * oscillate. It is read in a layout effect - before the browser paints the form chosen from it - when the rail
 * appears or goes away, and again in the callback whenever the row or the window resizes. A measurement that gives the
 * width already held changes no state, so a resize that leaves it as it was does not render the editor again. Where
 * nothing is laid out (jsdom, a hidden tab: width 0) it keeps `null` or the last width measured.
 */
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type RefObject } from 'react';
import { PANEL_GAP_PX } from './layout';

export function useCanvasRoom(
  rowRef: RefObject<HTMLElement | null>,
  railRef: RefObject<HTMLElement | null>,
  railShown: boolean,
): number | null {
  const [room, setRoom] = useState<number | null>(null);
  // The width last set: an unchanged measurement sets no state at all (a functional update that returns the same
  // value may still render the editor once before React bails out).
  const lastRoom = useRef<number | null>(null);

  const measure = useCallback(() => {
    const row = rowRef.current;
    if (!row) return;
    const rowWidth = row.clientWidth;
    if (rowWidth <= 0) return;
    const rail = railShown ? railRef.current : null;
    const railWidth = rail ? rail.getBoundingClientRect().width + PANEL_GAP_PX : 0;
    const next = Math.floor(rowWidth - railWidth);
    if (next === lastRoom.current) return;
    lastRoom.current = next;
    setRoom(next);
  }, [rowRef, railRef, railShown]);

  useLayoutEffect(() => {
    measure();
  }, [measure]);

  useEffect(() => {
    window.addEventListener('resize', measure);
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(measure);
    if (rowRef.current) observer?.observe(rowRef.current);
    return () => {
      window.removeEventListener('resize', measure);
      observer?.disconnect();
    };
  }, [rowRef, measure]);

  return room;
}
