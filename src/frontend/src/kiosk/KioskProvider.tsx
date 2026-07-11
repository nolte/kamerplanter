import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { updateUserPreferences } from '@/store/slices/userPreferencesSlice';
import { isLightMode } from '@/config/mode';
import {
  hasLocalKioskPreference,
  readLocalKioskPreference,
  writeLocalKioskPreference,
  type KioskPreference,
} from '@/lib/kioskPreferenceStorage';

/**
 * UI-NFR-019 — global kiosk-mode state (R-001). Owns the ``isKiosk`` and
 * ``highContrast`` flags, persists them (localStorage always; server in Full
 * mode, R-002) and drives the touch/high-contrast theme selection in
 * {@link ThemeContext} — all without a page reload (R-004).
 */
export interface KioskContextValue {
  isKiosk: boolean;
  highContrast: boolean;
  enableKiosk: () => void;
  disableKiosk: () => void;
  toggleKiosk: () => void;
  setHighContrast: (enabled: boolean) => void;
}

/**
 * Optional context: {@link ThemeContext} reads it defensively so components
 * (and tests) rendered without a {@link KioskProvider} simply fall back to the
 * standard light/dark theme.
 */
export const KioskContext = createContext<KioskContextValue | undefined>(undefined);

export function KioskProvider({ children }: { children: ReactNode }) {
  const dispatch = useAppDispatch();
  const serverPref = useAppSelector((s) => s.userPreferences.preferences);
  const [pref, setPref] = useState<KioskPreference>(() => readLocalKioskPreference());
  // Server hydration must happen at most once, and only when the user has not
  // already made an explicit local choice — otherwise a late-arriving server
  // fetch would clobber a change the user just made this session.
  const hydratedFromServer = useRef(hasLocalKioskPreference());

  useEffect(() => {
    if (hydratedFromServer.current) return;
    if (isLightMode) return;
    if (!serverPref) return;
    hydratedFromServer.current = true;
    setPref({
      kiosk_enabled: Boolean(serverPref.kiosk_enabled),
      high_contrast: Boolean(serverPref.high_contrast),
    });
  }, [serverPref]);

  const persist = useCallback(
    (next: KioskPreference) => {
      setPref(next);
      hydratedFromServer.current = true;
      writeLocalKioskPreference(next);
      if (!isLightMode) {
        // Best-effort server sync; the local copy is the reload-safe source of
        // truth, so a failed PATCH never blocks the (already applied) UI change.
        void dispatch(
          updateUserPreferences({
            updates: { kiosk_enabled: next.kiosk_enabled, high_contrast: next.high_contrast },
          }),
        );
      }
    },
    [dispatch],
  );

  const value = useMemo<KioskContextValue>(
    () => ({
      isKiosk: pref.kiosk_enabled,
      highContrast: pref.high_contrast,
      // R-005 — entering kiosk mode activates the high-contrast theme by default.
      enableKiosk: () => persist({ kiosk_enabled: true, high_contrast: true }),
      disableKiosk: () => persist({ ...pref, kiosk_enabled: false }),
      toggleKiosk: () =>
        persist(
          pref.kiosk_enabled
            ? { ...pref, kiosk_enabled: false }
            : { kiosk_enabled: true, high_contrast: true },
        ),
      setHighContrast: (enabled: boolean) => persist({ ...pref, high_contrast: enabled }),
    }),
    [pref, persist],
  );

  return <KioskContext.Provider value={value}>{children}</KioskContext.Provider>;
}

/** Kiosk state for components that require an enclosing {@link KioskProvider}. */
export function useKiosk(): KioskContextValue {
  const ctx = useContext(KioskContext);
  if (!ctx) throw new Error('useKiosk must be used within KioskProvider');
  return ctx;
}
