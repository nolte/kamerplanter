import { act, renderHook } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import type { ReactNode } from 'react';
import { ThemeContextProvider, useThemeMode } from '@/theme/ThemeContext';

const STORAGE_KEY = 'kamerplanter-theme';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeContextProvider>{children}</ThemeContextProvider>;
}

/**
 * The Node test runtime ships a restricted localStorage that lacks the
 * standard methods, so we stub a deterministic in-memory implementation.
 */
function stubLocalStorage(initial: Record<string, string> = {}) {
  const store = new Map(Object.entries(initial));
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
  });
  return store;
}

function stubPrefersDark(matches: boolean) {
  vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({ matches } as MediaQueryList));
}

describe('ThemeContext', () => {
  beforeEach(() => {
    stubPrefersDark(false);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('defaults to light mode when nothing is stored and dark is not preferred', () => {
    stubLocalStorage();
    const { result } = renderHook(() => useThemeMode(), { wrapper });
    expect(result.current.mode).toBe('light');
  });

  it('uses the stored mode when one is persisted', () => {
    stubLocalStorage({ [STORAGE_KEY]: 'dark' });
    const { result } = renderHook(() => useThemeMode(), { wrapper });
    expect(result.current.mode).toBe('dark');
  });

  it('falls back to the OS preference when nothing is stored', () => {
    stubLocalStorage();
    stubPrefersDark(true);
    const { result } = renderHook(() => useThemeMode(), { wrapper });
    expect(result.current.mode).toBe('dark');
  });

  it('toggles between light and dark when toggleTheme is called', () => {
    stubLocalStorage({ [STORAGE_KEY]: 'light' });
    const { result } = renderHook(() => useThemeMode(), { wrapper });

    act(() => result.current.toggleTheme());
    expect(result.current.mode).toBe('dark');

    act(() => result.current.toggleTheme());
    expect(result.current.mode).toBe('light');
  });

  it('persists the selected mode to localStorage', () => {
    const store = stubLocalStorage({ [STORAGE_KEY]: 'light' });
    const { result } = renderHook(() => useThemeMode(), { wrapper });

    act(() => result.current.toggleTheme());
    expect(store.get(STORAGE_KEY)).toBe('dark');
  });

  it('falls back to light mode when localStorage access throws', () => {
    vi.stubGlobal('localStorage', {
      getItem: () => {
        throw new Error('blocked');
      },
      setItem: () => undefined,
      removeItem: () => undefined,
      clear: () => undefined,
    });
    const { result } = renderHook(() => useThemeMode(), { wrapper });
    expect(result.current.mode).toBe('light');
  });

  it('throws when useThemeMode is used outside a provider', () => {
    expect(() => renderHook(() => useThemeMode())).toThrow(
      /must be used within ThemeContextProvider/,
    );
  });
});
