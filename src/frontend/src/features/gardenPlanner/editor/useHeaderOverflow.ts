/**
 * How many steps of the header bar's move order (REQ-053 GP-UX-063) have to go into the overflow "⋮" so the bar
 * stays one line. The breakpoint sets the floor (below md every step is in the overflow); above it the bar is
 * measured: while its content is wider than the bar, one more step moves out. A wider bar starts again from the
 * floor, so a control comes back as soon as it fits; a control of the bar that grows (a longer save status) is
 * measured again. The level is checked in a layout effect, before the browser paints, so a clipped bar is not shown.
 * Where nothing is laid out (jsdom: every width is 0) the floor stays.
 */
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type FocusEvent as ReactFocusEvent,
  type RefObject,
} from 'react';

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

export interface HeaderFocusRescue {
  onFocus: (event: ReactFocusEvent<HTMLElement>) => void;
  onBlur: (event: ReactFocusEvent<HTMLElement>) => void;
}

/**
 * Keeps the keyboard focus in the header bar when the control that has it leaves the bar (REQ-053 GP-NFR-070, WCAG 2.2
 * SC 2.4.3): a level change moves the focused auto-save switch, tab, field-mode link or panel switch into the
 * overflow, or the bar turns narrow - the element is removed and the browser would drop the focus to the page body.
 * The bar remembers the control of its own that has the focus; once that control is gone after a render and nothing
 * else took the focus, the focus goes to the overflow "⋮" (`overflowRef`), where the control now is.
 *
 * Spread `onFocus`/`onBlur` on the bar. A focus that leaves the bar for another element forgets the control; a blur to
 * nothing (a click on the page, the window losing focus) forgets it once it is clear the control is still there.
 */
export function useHeaderFocusRescue(
  barRef: RefObject<HTMLElement | null>,
  overflowRef: RefObject<HTMLElement | null>,
): HeaderFocusRescue {
  const focused = useRef<HTMLElement | null>(null);

  const onFocus = useCallback(
    (event: ReactFocusEvent<HTMLElement>) => {
      // React lets focus events of a portal (an open menu) bubble here; only the bar's own controls count.
      const target = event.target;
      focused.current = target instanceof HTMLElement && barRef.current?.contains(target) ? target : null;
    },
    [barRef],
  );

  const onBlur = useCallback(
    (event: ReactFocusEvent<HTMLElement>) => {
      const target = event.target;
      const next = event.relatedTarget;
      if (next instanceof Node) {
        if (!barRef.current?.contains(next)) focused.current = null;
        return;
      }
      // A blur to nothing: a removal is handled by the layout effect below in the same commit; a control still in
      // place had a real blur (a click on the page) and is not followed later.
      window.setTimeout(() => {
        if (focused.current === target && target.isConnected) focused.current = null;
      }, 0);
    },
    [barRef],
  );

  // After every render of the bar: was the focused control removed, with the focus left on the body?
  useLayoutEffect(() => {
    const control = focused.current;
    if (control === null || control.isConnected) return;
    focused.current = null;
    const active = document.activeElement;
    if (active !== null && active !== document.body) return;
    overflowRef.current?.focus();
  });

  return useMemo(() => ({ onFocus, onBlur }), [onFocus, onBlur]);
}
