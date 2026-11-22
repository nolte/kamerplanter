import { useEffect, useMemo, useState } from 'react';

interface UseInViewportOptions {
  /** Margin around the viewport that already counts as visible, so loading starts just before scrolling in. */
  rootMargin?: string;
}

/** A callback ref for the observed element, and whether that element has been in (or near) the viewport. */
type InViewportResult<T extends Element> = readonly [(node: T | null) => void, boolean];

function observerAvailable(): boolean {
  return typeof window !== 'undefined' && typeof window.IntersectionObserver === 'function';
}

/**
 * #3023 (N-23) — whether an element has entered the viewport, latched: once `true` it stays `true`.
 *
 * Built on `IntersectionObserver`. Where that API is missing (jsdom, very old browsers) the element counts as
 * visible right away, so the caller behaves exactly as without the hook instead of never loading.
 */
export function useInViewport<T extends Element>({ rootMargin = '200px' }: UseInViewportOptions = {}): InViewportResult<T> {
  const [node, setNode] = useState<T | null>(null);
  const [inViewport, setInViewport] = useState<boolean>(() => !observerAvailable());

  useEffect(() => {
    if (inViewport || node === null || !observerAvailable()) return;
    const observer = new window.IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setInViewport(true);
          observer.disconnect();
        }
      },
      { rootMargin },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [inViewport, node, rootMargin]);

  return useMemo(() => [setNode, inViewport] as const, [inViewport]);
}
