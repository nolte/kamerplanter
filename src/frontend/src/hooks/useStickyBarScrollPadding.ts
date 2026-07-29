import { useCallback, useEffect, useRef } from 'react';

/** Callback ref that the pinned bar must attach to itself. */
export type StickyBarRef = (element: HTMLElement | null) => void;

const SCROLLABLE_OVERFLOW = new Set(['auto', 'scroll', 'overlay']);

function isScrollable(element: HTMLElement): boolean {
  return SCROLLABLE_OVERFLOW.has(window.getComputedStyle(element).overflowY);
}

/**
 * Nearest ancestor that actually scrolls the bar's content.
 *
 * Inside a dialog that is the `DialogContent` (`overflow-y: auto`); on a long
 * in-page edit form no ancestor scrolls and the document itself does, in which
 * case `scroll-padding` has to sit on the root element — that is the element
 * whose value propagates to the viewport.
 */
function findScrollContainer(bar: HTMLElement): HTMLElement {
  const root = document.documentElement;
  let node = bar.parentElement;
  while (node && node !== document.body && node !== root) {
    if (isScrollable(node)) return node;
    node = node.parentElement;
  }
  return root;
}

/**
 * How much space at the bottom edge of `container`'s scrollport the pinned bar
 * can cover, plus `gapPx` breathing room.
 *
 * Two summands, both measured rather than assumed:
 *
 * 1. the bar's own border-box height — whatever `py`, button size, wrapped
 *    label or spinner currently make it;
 * 2. the *tail*: a sticky box is confined to its containing block (the `<form>`
 *    that wraps the fields), so at the very end of the scroll range it comes to
 *    rest that block's remaining bottom space above the scrollport edge —
 *    `DialogContent`'s 20px bottom padding, the page region's `py`. In that
 *    position the covered band sits one tail higher than the bar's height alone
 *    would suggest.
 *
 * The tail only counts while the bar is still on screen at maximum scroll: on a
 * page whose form is followed by more content the bar has long scrolled out of
 * view by then, and adding that distance would reserve hundreds of pixels for
 * an element that is not there.
 */
function reservedSpace(bar: HTMLElement, container: HTMLElement, gapPx: number): number {
  const isViewport = container === document.documentElement;
  const barRect = bar.getBoundingClientRect();
  // Scroll-content coordinates. The root element's own box scrolls with the
  // viewport, so its rect must not be subtracted a second time.
  const barTop = isViewport
    ? barRect.top + window.scrollY
    : barRect.top -
      container.getBoundingClientRect().top -
      container.clientTop +
      container.scrollTop;
  const tail = container.scrollHeight - (barTop + barRect.height);
  const viewportHeight = container.clientHeight;
  const reachableTail = tail > 0 && tail < viewportHeight ? tail : 0;
  const reserved = barRect.height + reachableTail + gapPx;
  if (!Number.isFinite(reserved) || reserved <= 0) return 0;
  // Safety valve: `scroll-padding` larger than half the scrollport would make
  // every scroll-into-view on that container jump, so never reserve more than
  // that. With a real action row (~60px) plus a container padding tail this
  // never binds; it only bounds a pathological measurement.
  if (viewportHeight > 0) return Math.min(reserved, viewportHeight / 2);
  return reserved;
}

/**
 * Issue #768 — keep a bottom-pinned bar from occluding what the browser scrolls
 * to the bottom edge.
 *
 * A bar with `position: sticky; bottom: 0` floats over its own scroll
 * container's bottom band. Anything the browser brings into view there — a
 * field reached with Tab, `scrollIntoView`, WebDriver's click preparation —
 * lands *behind* the bar. `scroll-padding-bottom` on the scroll container is
 * the mechanism for that: the scrolling-into-view algorithm insets the
 * scrollport by it, so the browser stops short of the reserved band on its own.
 * It is set here rather than in CSS because the container is not knowable from
 * the bar's stylesheet — it is `DialogContent` in a dialog and the root element
 * on an in-page form — and because the amount is measured, so it tracks the
 * bar's real height instead of a pixel constant that drifts.
 *
 * The returned callback ref must be attached to the pinned element. While
 * `enabled` is false (wide viewport: the bar is not pinned and occludes
 * nothing) no space is reserved.
 *
 * The previous inline value is restored on unmount, so nesting — an in-page
 * form plus an open dialog — leaves no residue on either container.
 */
export function useStickyBarScrollPadding(enabled: boolean, gapPx: number): StickyBarRef {
  const barRef = useRef<HTMLElement | null>(null);
  const containerRef = useRef<HTMLElement | null>(null);
  const previousValueRef = useRef('');
  const observerRef = useRef<ResizeObserver | null>(null);

  const release = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    container.style.scrollPaddingBottom = previousValueRef.current;
    containerRef.current = null;
    previousValueRef.current = '';
  }, []);

  const measure = useCallback(() => {
    const bar = barRef.current;
    if (!enabled || !bar?.isConnected) {
      release();
      return;
    }
    const container = findScrollContainer(bar);
    if (container !== containerRef.current) {
      release();
      containerRef.current = container;
      previousValueRef.current = container.style.scrollPaddingBottom;
    }
    container.style.scrollPaddingBottom = `${reservedSpace(bar, container, gapPx)}px`;
  }, [enabled, gapPx, release]);

  const setBarRef = useCallback<StickyBarRef>(
    (element) => {
      barRef.current = element;
      // Re-observe: the ref runs again with the new node whenever the element
      // is swapped, so the observer must never keep the stale one.
      observerRef.current?.disconnect();
      if (!element) {
        release();
        return;
      }
      measure();
      // jsdom / SSR have no ResizeObserver — the resize listener below still
      // covers the viewport change, only intra-container growth is missed.
      if (typeof ResizeObserver === 'undefined') return;
      const observer = new ResizeObserver(() => measure());
      observer.observe(element);
      const container = containerRef.current;
      if (container && container !== document.documentElement) observer.observe(container);
      observerRef.current = observer;
    },
    [measure, release],
  );

  useEffect(() => {
    // Rotation / soft-keyboard resize changes both the bar's wrapping and the
    // container's scrollport, so the reservation has to be recomputed.
    const onResize = () => measure();
    window.addEventListener('resize', onResize);
    measure();
    return () => window.removeEventListener('resize', onResize);
  }, [measure]);

  useEffect(
    () => () => {
      observerRef.current?.disconnect();
      observerRef.current = null;
      release();
    },
    [release],
  );

  return setBarRef;
}
