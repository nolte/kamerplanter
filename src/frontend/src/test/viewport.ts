import { vi } from 'vitest';

/**
 * A width-driven `matchMedia` stub (jsdom has none). MUI's `useMediaQuery` only asks `matchMedia` whether a
 * query matches, so evaluating `(min-width: …)` / `(max-width: …)` against a fixed width is enough to put the
 * shell into its phone (< md) or desktop layout. `prefers-reduced-motion` answers `reducedMotion`.
 *
 * Undo with {@link restoreViewport} in `afterEach`.
 */
export function stubViewport({ width, reducedMotion = false }: { width: number; reducedMotion?: boolean }): void {
  window.innerWidth = width;
  window.matchMedia = ((query: string) => {
    let matches: boolean;
    if (query.includes('prefers-reduced-motion')) {
      matches = reducedMotion === query.includes('reduce');
    } else {
      const min = /\(min-width:\s*([\d.]+)px\)/.exec(query);
      const max = /\(max-width:\s*([\d.]+)px\)/.exec(query);
      matches = (min === null || width >= Number(min[1])) && (max === null || width <= Number(max[1]));
    }
    return {
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    } as unknown as MediaQueryList;
  }) as typeof window.matchMedia;
}

const ORIGINAL_INNER_WIDTH = window.innerWidth;

/** Drop the stub so the next suite sees jsdom's own (absent) `matchMedia` again. */
export function restoreViewport(): void {
  window.innerWidth = ORIGINAL_INNER_WIDTH;
  // @ts-expect-error — jsdom ships no matchMedia; the stub is removed, not reset.
  delete window.matchMedia;
}
