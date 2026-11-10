/**
 * The size of the canvas area (REQ-053 §17.3, GP-UX-067): it takes the rest of the viewport height below
 * everything above it (the header bar, messages and tool hints), at least
 * `MIN_CANVAS_HEIGHT_PX`, and the width its flex row leaves next to the tool rail and a docked side panel. Below md
 * the docked bars at the bottom (`TouchBar`, tool bar) are kept clear, so they do not cover the plan.
 *
 * `fitReservePx` is room beside the area that the plan's fit still counts as its own (WP 10.5): the side panel that a
 * selection docked beside the canvas. The route fits the plan into `fitWidthPx` (the width plus that room) and keeps
 * the top-left corner, so a click that selects a bed does not rescale or move the plan under the pointer; the panel
 * just covers the right edge of the fitted view. It is measured in the same layout pass as the width that changed
 * with it, so the two never disagree for a frame.
 *
 * The top is read in a layout effect whenever the page, the area or the window resizes - a hint that appears above
 * the canvas makes the page taller and is measured before the browser paints. Writing the height does not move the
 * top, so there is no loop. Where nothing is laid out (jsdom, a hidden tab) the area reports
 * nothing and keeps its natural height.
 */
import { useEffect, useLayoutEffect, useState, type RefObject } from 'react';

/** The canvas is never lower than this (GP-UX-067). */
export const MIN_CANVAS_HEIGHT_PX = 400;
/** Room under the canvas: the bottom padding of the page. */
const BOTTOM_GAP_PX = 8;

export interface CanvasAreaSize {
  widthPx: number;
  heightPx: number;
  /** The width the plan is fitted into: `widthPx` plus the room a selection's docked panel took (default: the width). */
  fitWidthPx?: number;
}

export function availableCanvasHeight(innerHeight: number, documentTop: number, bottomReservePx: number): number {
  return Math.max(MIN_CANVAS_HEIGHT_PX, Math.floor(innerHeight - documentTop - bottomReservePx - BOTTOM_GAP_PX));
}

export function useCanvasArea(
  areaRef: RefObject<HTMLElement | null>,
  bottomRef: RefObject<HTMLElement | null>,
  fitReservePx = 0,
): CanvasAreaSize | null {
  const [size, setSize] = useState<CanvasAreaSize | null>(null);
  // Bumped by a resize: the next render measures again.
  const [tick, setTick] = useState(0);

  useLayoutEffect(() => {
    const area = areaRef.current;
    if (!area) return;
    const rect = area.getBoundingClientRect();
    // Hidden (the "Beete" tab) or not laid out at all: keep what was measured last.
    if (rect.width === 0 && rect.height === 0) return;
    const documentTop = rect.top + window.scrollY;
    const reserve = bottomRef.current?.getBoundingClientRect().height ?? 0;
    const heightPx = availableCanvasHeight(window.innerHeight, documentTop, reserve);
    const widthPx = Math.floor(area.clientWidth);
    if (widthPx <= 0) return;
    const fitWidthPx = widthPx + fitReservePx;
    setSize((previous) =>
      previous &&
      previous.widthPx === widthPx &&
      previous.heightPx === heightPx &&
      previous.fitWidthPx === fitWidthPx
        ? previous
        : { widthPx, heightPx, fitWidthPx },
    );
  }, [areaRef, bottomRef, tick, fitReservePx]);

  // A resize of the window or of anything on the page may move the area or change its width.
  useEffect(() => {
    const bump = () => setTick((value) => value + 1);
    window.addEventListener('resize', bump);
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(bump);
    observer?.observe(document.body);
    if (areaRef.current) observer?.observe(areaRef.current);
    return () => {
      window.removeEventListener('resize', bump);
      observer?.disconnect();
    };
  }, [areaRef]);

  return size;
}
