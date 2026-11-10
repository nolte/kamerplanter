/**
 * How many steps of the header bar's move order (REQ-053 GP-UX-063) have to go into the overflow "⋮" so the bar
 * stays one line. The breakpoint sets the floor (below md every step is in the overflow); above it the bar is
 * measured: while its content is wider than the bar, one more step moves out. A wider bar starts again from the
 * floor, so a control comes back as soon as it fits; a control of the bar that grows (a longer save status) is
 * measured again. The level is checked in a layout effect, before the browser paints, so a clipped bar is not shown.
 * Where nothing is laid out (jsdom: every width is 0) the floor stays.
 */
import { useEffect, useLayoutEffect, useRef, useState, type RefObject } from 'react';

/** Below this many px of extra content the bar counts as fitting (sub-pixel rounding). */
const TOLERANCE_PX = 1;

export function useHeaderOverflow(
  barRef: RefObject<HTMLElement | null>,
  minLevel: number,
  maxLevel: number,
): number {
  const [state, setState] = useState({ level: minLevel, floor: minLevel });
  // A new floor (a breakpoint was crossed) starts the measuring again from it (state adjusted during render).
  if (state.floor !== minLevel) setState({ level: minLevel, floor: minLevel });
  const level = Math.min(maxLevel, Math.max(minLevel, state.level));

  // Bumped when a control of the bar changed its size: the layout effect checks again.
  const [contentTick, setContentTick] = useState(0);
  useLayoutEffect(() => {
    const bar = barRef.current;
    if (!bar || bar.clientWidth === 0) return;
    if (bar.scrollWidth > bar.clientWidth + TOLERANCE_PX && level < maxLevel) {
      setState((previous) => ({ ...previous, level: level + 1 }));
    }
  }, [barRef, level, maxLevel, contentTick]);

  const lastWidth = useRef<number | null>(null);
  useEffect(() => {
    const bar = barRef.current;
    if (!bar || typeof ResizeObserver === 'undefined') return undefined;
    const observer = new ResizeObserver(() => {
      const width = bar.clientWidth;
      if (width === lastWidth.current) {
        setContentTick((value) => value + 1);
        return;
      }
      const grew = lastWidth.current !== null && width > lastWidth.current;
      lastWidth.current = width;
      // Narrower: the layout effect moves more out. Wider: start from the floor and let it measure again.
      if (grew) setState((previous) => ({ ...previous, level: previous.floor }));
      else setContentTick((value) => value + 1);
    });
    observer.observe(bar);
    // The controls themselves: a save status that gets longer does not change the bar's width.
    for (const child of Array.from(bar.children)) observer.observe(child);
    return () => observer.disconnect();
  }, [barRef, level]);

  return level;
}
