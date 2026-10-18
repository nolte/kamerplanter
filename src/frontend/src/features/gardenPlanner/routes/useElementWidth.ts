import { useEffect, useRef, useState, type RefObject } from 'react';

/** Width used until the container has been measured (and where ResizeObserver does not exist). */
const FALLBACK_WIDTH_PX = 640;

/** The width of the element the ref points at, kept up to date while it resizes. */
export function useElementWidth<T extends HTMLElement>(): [RefObject<T | null>, number] {
  const ref = useRef<T | null>(null);
  const [width, setWidth] = useState(FALLBACK_WIDTH_PX);
  useEffect(() => {
    const element = ref.current;
    if (element === null || typeof ResizeObserver === 'undefined') return undefined;
    const measure = () => {
      if (element.clientWidth > 0) setWidth(element.clientWidth);
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  return [ref, width];
}
