import { useEffect, useState } from 'react';

function read(): number {
  return typeof window === 'undefined'
    ? 800
    : (window.visualViewport?.height ?? window.innerHeight);
}

/** The height of what is visible above the on-screen keyboard: the bottom sheet follows it (GP-UX-052). */
export function useVisibleHeight(): number {
  const [height, setHeight] = useState(read);
  useEffect(() => {
    const target: EventTarget = window.visualViewport ?? window;
    const update = () => setHeight(read());
    target.addEventListener('resize', update);
    return () => target.removeEventListener('resize', update);
  }, []);
  return height;
}
