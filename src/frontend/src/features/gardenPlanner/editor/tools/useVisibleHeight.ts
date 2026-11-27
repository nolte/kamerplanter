import { useEffect, useState } from 'react';
import { bottomNavOffsetPx } from '@/components/layout/bottomNavOffset';

function read(): number {
  return typeof window === 'undefined'
    ? 800
    : Math.max(0, (window.visualViewport?.height ?? window.innerHeight) - bottomNavOffsetPx());
}

/**
 * The height of what is visible above the on-screen keyboard and, on a phone, above the bottom navigation
 * (#3018): the bottom sheet follows it (GP-UX-052). The dock it sits in rests on the bar, so a "full" sheet
 * sized from the whole viewport would push its header with the close button up under the app bar.
 */
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
