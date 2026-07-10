import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { rowsForContentHeight } from '@/lib/dashboardLayoutOps';

/**
 * REQ-045 §3.8 — content-height measurement for the edit grid.
 *
 * react-grid-layout locks every tile to a fixed ``h × rowHeight`` box, so a
 * widget whose natural content is taller than that box overflows and overlaps
 * the tile below (unlike the read-only CSS grid, which flows to
 * ``minmax(floor, min-content)``). This hook observes each tile's real content
 * height via ``ResizeObserver`` and derives the minimum number of grid rows
 * needed to cover it. The caller clamps each tile's ``h`` up to that floor, so
 * the fixed-row geometry react-grid-layout needs for drag/resize stays intact
 * while the box always covers its content.
 *
 * Convergence: once a tile's ``h`` covers its content, the measured scrollHeight
 * equals the box height ``h × rowHeight + (h - 1) × marginY``, whose row count is
 * exactly ``h`` again — so the floor is a fixed point and never oscillates.
 *
 * The returned object is stabilised with ``useMemo`` (project convention for
 * object-returning hooks): ``floors`` is the id→min-rows map, ``getContentRef``
 * yields a stable callback ref per widget instance.
 */
export function useContentRowFloors(rowHeightPx: number, marginYPx: number) {
  const [floors, setFloors] = useState<Record<string, number>>({});
  const floorsRef = useRef<Record<string, number>>({});
  const idByElement = useRef(new Map<Element, string>());
  const elementById = useRef(new Map<string, HTMLElement>());
  const refCache = useRef(new Map<string, (el: HTMLElement | null) => void>());
  const observerRef = useRef<ResizeObserver | null>(null);

  const applyMeasurement = useCallback(
    (id: string, contentPx: number) => {
      const rows = rowsForContentHeight(contentPx, rowHeightPx, marginYPx);
      if (floorsRef.current[id] === rows) return;
      floorsRef.current = { ...floorsRef.current, [id]: rows };
      setFloors(floorsRef.current);
    },
    [rowHeightPx, marginYPx],
  );

  const getObserver = useCallback((): ResizeObserver | null => {
    if (observerRef.current) return observerRef.current;
    // jsdom / SSR: no ResizeObserver — measurement is inert, tiles keep their
    // stored `h` (which the catalog defaults size to fit typical content).
    if (typeof ResizeObserver === 'undefined') return null;
    observerRef.current = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const id = idByElement.current.get(entry.target);
        if (id) applyMeasurement(id, (entry.target as HTMLElement).scrollHeight);
      }
    });
    return observerRef.current;
  }, [applyMeasurement]);

  const getContentRef = useCallback(
    (id: string) => {
      const cached = refCache.current.get(id);
      if (cached) return cached;
      const cb = (el: HTMLElement | null) => {
        const observer = getObserver();
        const previous = elementById.current.get(id);
        if (previous && previous !== el) {
          observer?.unobserve(previous);
          idByElement.current.delete(previous);
          elementById.current.delete(id);
        }
        if (el) {
          elementById.current.set(id, el);
          idByElement.current.set(el, id);
          observer?.observe(el);
          // Synchronous first measurement so the very first paint already sizes
          // the tile to its content (no one-frame overlap flash).
          applyMeasurement(id, el.scrollHeight);
        }
      };
      refCache.current.set(id, cb);
      return cb;
    },
    [getObserver, applyMeasurement],
  );

  useEffect(
    () => () => {
      observerRef.current?.disconnect();
      observerRef.current = null;
    },
    [],
  );

  return useMemo(() => ({ floors, getContentRef }), [floors, getContentRef]);
}
