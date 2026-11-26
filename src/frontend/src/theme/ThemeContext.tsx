import { createContext, useContext, useState, useEffect, useMemo, type ReactNode } from 'react';
import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useTranslation } from 'react-i18next';
import { selectAppTheme } from './theme';
import { muiLocaleFor } from './muiLocale';
import { KioskContext } from '@/kiosk/KioskProvider';

type ThemeMode = 'light' | 'dark';

interface ThemeContextValue {
  mode: ThemeMode;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const STORAGE_KEY = 'kamerplanter-theme';

const DARK_QUERY = '(prefers-color-scheme: dark)';

/** The mode the user picked by hand, or `null` while the OS preference decides (UI-NFR-006 R-004, #3021). */
function readStoredMode(): ThemeMode | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'light' || stored === 'dark' ? stored : null;
  } catch {
    return null;
  }
}

function readSystemMode(): ThemeMode {
  try {
    return window.matchMedia(DARK_QUERY).matches ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}

export function ThemeContextProvider({ children }: { children: ReactNode }) {
  // Only a manual pick is persisted. Until there is one, the OS preference decides and keeps deciding: a later
  // OS switch (e.g. automatic dark mode at sunset) is followed instead of being frozen at the first visit.
  const [storedMode, setStoredMode] = useState<ThemeMode | null>(readStoredMode);
  const [systemMode, setSystemMode] = useState<ThemeMode>(readSystemMode);
  const mode: ThemeMode = storedMode ?? systemMode;

  useEffect(() => {
    if (storedMode !== null) return undefined;
    let query: MediaQueryList;
    try {
      query = window.matchMedia(DARK_QUERY);
    } catch {
      return undefined;
    }
    if (typeof query?.addEventListener !== 'function') return undefined;
    const onChange = (event: MediaQueryListEvent) => setSystemMode(event.matches ? 'dark' : 'light');
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  }, [storedMode]);

  // UI-NFR-019 — the kiosk context is optional so components rendered without a
  // KioskProvider (e.g. isolated tests) fall back to the standard light/dark
  // theme. When present, its flags select the high-contrast / touch theme and a
  // change re-renders this consumer, flipping the theme without a reload (R-004).
  const kiosk = useContext(KioskContext);
  const isKiosk = kiosk?.isKiosk ?? false;
  const highContrast = kiosk?.highContrast ?? false;

  useEffect(() => {
    if (storedMode === null) return;
    try {
      localStorage.setItem(STORAGE_KEY, storedMode);
    } catch {
      // localStorage unavailable in tests
    }
  }, [storedMode]);

  const value = useMemo(
    () => ({
      mode,
      // The toggle is the manual pick: from then on the chosen mode is kept and the OS preference no longer applies.
      toggleTheme: () => setStoredMode(mode === 'light' ? 'dark' : 'light'),
    }),
    [mode],
  );

  // MUI's built-in texts follow the UI language (L-03). `useTranslation` re-renders this
  // provider on a language switch, so the merged theme changes with it at runtime.
  const { i18n } = useTranslation();
  const language = i18n.language;
  const theme = useMemo(
    () => createTheme(selectAppTheme(mode, isKiosk, highContrast), muiLocaleFor(language)),
    [mode, isKiosk, highContrast, language],
  );

  return (
    <ThemeContext.Provider value={value}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline enableColorScheme />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
}

export function useThemeMode(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useThemeMode must be used within ThemeContextProvider');
  return ctx;
}
