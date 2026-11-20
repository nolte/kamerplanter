/**
 * The width the canvas has without a docked side panel (#3034): the canvas row less the tool rail and its gap. The
 * panel's form is decided from it (`sidePanelVariant`), so it is measured on the page - the app sidebar, the page
 * padding and the rail count, a viewport breakpoint alone would not see them.
 *
 * Docking the panel does not change this width (the canvas shrinks, the row does not), so the decision cannot
 * oscillate. It is read in a layout effect - before the browser paints the form chosen from it - whenever the row
 * resizes, the window resizes or the rail appears or goes away. Where nothing is laid out (jsdom, a hidden tab) it
 * keeps `null` or the last width measured.
 */
import { useEffect, useLayoutEffect, useState, type RefObject } from 'react';
import { PANEL_GAP_PX } from './layout';

export function useCanvasRoom(
  rowRef: RefObject<HTMLElement | null>,
  railRef: RefObject<HTMLElement | null>,
  railShown: boolean,
): number | null {
  const [room, setRoom] = useState<number | null>(null);
  // Bumped by a resize: the next render measures again.
  const [tick, setTick] = useState(0);

  useLayoutEffect(() => {
    const row = rowRef.current;
    if (!row) return;
    const rowWidth = row.clientWidth;
    if (rowWidth <= 0) return;
    const rail = railShown ? railRef.current : null;
    const railWidth = rail ? rail.getBoundingClientRect().width + PANEL_GAP_PX : 0;
    const next = Math.floor(rowWidth - railWidth);
    setRoom((previous) => (previous === next ? previous : next));
  }, [rowRef, railRef, railShown, tick]);

  useEffect(() => {
    const bump = () => setTick((value) => value + 1);
    window.addEventListener('resize', bump);
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(bump);
    if (rowRef.current) observer?.observe(rowRef.current);
    return () => {
      window.removeEventListener('resize', bump);
      observer?.disconnect();
    };
  }, [rowRef]);

  return room;
}
