import { act, renderHook } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import type { ReactNode } from 'react';
import { Provider } from 'react-redux';
import { KioskProvider, useKiosk } from '@/kiosk/KioskProvider';
import { createTestStore, type TestStore } from '@/test/helpers';

const STORAGE_KEY = 'kp-kiosk-preference';

// Mode is read lazily so individual tests can flip between Light and Full mode.
const modeMock = { isLightMode: true };
vi.mock('@/config/mode', () => ({
  get isLightMode() {
    return modeMock.isLightMode;
  },
  get isFullMode() {
    return !modeMock.isLightMode;
  },
  get KAMERPLANTER_MODE() {
    return modeMock.isLightMode ? 'light' : 'full';
  },
}));

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

function makeWrapper(store: TestStore) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <Provider store={store}>
        <KioskProvider>{children}</KioskProvider>
      </Provider>
    );
  };
}

describe('KioskProvider', () => {
  beforeEach(() => {
    modeMock.isLightMode = true;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('defaults to kiosk off and high-contrast off when nothing is stored', () => {
    stubLocalStorage();
    const { result } = renderHook(() => useKiosk(), { wrapper: makeWrapper(createTestStore()) });
    expect(result.current.isKiosk).toBe(false);
    expect(result.current.highContrast).toBe(false);
  });

  it('reads the persisted preference on mount', () => {
    stubLocalStorage({
      [STORAGE_KEY]: JSON.stringify({ kiosk_enabled: true, high_contrast: true }),
    });
    const { result } = renderHook(() => useKiosk(), { wrapper: makeWrapper(createTestStore()) });
    expect(result.current.isKiosk).toBe(true);
    expect(result.current.highContrast).toBe(true);
  });

  it('enabling kiosk also activates high-contrast by default (R-005)', () => {
    stubLocalStorage();
    const { result } = renderHook(() => useKiosk(), { wrapper: makeWrapper(createTestStore()) });

    act(() => result.current.enableKiosk());

    expect(result.current.isKiosk).toBe(true);
    expect(result.current.highContrast).toBe(true);
  });

  it('persists the kiosk preference to localStorage (R-002)', () => {
    const store = stubLocalStorage();
    const { result } = renderHook(() => useKiosk(), { wrapper: makeWrapper(createTestStore()) });

    act(() => result.current.enableKiosk());

    const persisted = JSON.parse(store.get(STORAGE_KEY)!);
    expect(persisted).toEqual({ kiosk_enabled: true, high_contrast: true });
  });

  it('toggleKiosk switches kiosk on and off', () => {
    stubLocalStorage();
    const { result } = renderHook(() => useKiosk(), { wrapper: makeWrapper(createTestStore()) });

    act(() => result.current.toggleKiosk());
    expect(result.current.isKiosk).toBe(true);

    act(() => result.current.toggleKiosk());
    expect(result.current.isKiosk).toBe(false);
  });

  it('disabling kiosk keeps the high-contrast preference untouched', () => {
    stubLocalStorage({
      [STORAGE_KEY]: JSON.stringify({ kiosk_enabled: true, high_contrast: true }),
    });
    const { result } = renderHook(() => useKiosk(), { wrapper: makeWrapper(createTestStore()) });

    act(() => result.current.disableKiosk());

    expect(result.current.isKiosk).toBe(false);
    expect(result.current.highContrast).toBe(true);
  });

  it('high-contrast can be toggled independently of kiosk (R-045)', () => {
    stubLocalStorage();
    const { result } = renderHook(() => useKiosk(), { wrapper: makeWrapper(createTestStore()) });

    act(() => result.current.setHighContrast(true));

    expect(result.current.highContrast).toBe(true);
    expect(result.current.isKiosk).toBe(false);
  });

  it('hydrates from the server preference in Full mode when no local choice exists', () => {
    modeMock.isLightMode = false;
    stubLocalStorage();
    const store = createTestStore({
      userPreferences: {
        preferences: {
          key: 'pref-1',
          user_key: 'user-1',
          experience_level: 'beginner',
          onboarding_completed: true,
          locale: 'de',
          theme: 'light',
          watering_can_liters: 5,
          smart_home_enabled: false,
          kiosk_enabled: true,
          high_contrast: true,
          module_visibility: {},
        },
        loading: false,
        error: null,
      },
    });
    const { result } = renderHook(() => useKiosk(), { wrapper: makeWrapper(store) });
    expect(result.current.isKiosk).toBe(true);
    expect(result.current.highContrast).toBe(true);
  });

  it('throws when useKiosk is used outside a provider', () => {
    expect(() => renderHook(() => useKiosk())).toThrow(/must be used within KioskProvider/);
  });
});
