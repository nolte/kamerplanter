import { createTheme, type Theme } from '@mui/material/styles';
import { lightPalette, darkPalette, highContrastPalette } from './palette';
import { typography } from './typography';
import { breakpoints, radii } from './tokens';
import { kioskThemeOverrides } from '@/kiosk/kioskTheme';

const reducedMotion = '@media (prefers-reduced-motion: reduce)';

function buildTheme(mode: 'light' | 'dark'): Theme {
  const palette = mode === 'light' ? lightPalette : darkPalette;

  return createTheme({
    palette,
    typography,
    breakpoints,
    shape: {
      borderRadius: radii.md,
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          [reducedMotion]: {
            '*, *::before, *::after': {
              animationDuration: '0.01ms !important',
              animationIterationCount: '1 !important',
              transitionDuration: '0.01ms !important',
              scrollBehavior: 'auto !important',
            },
          },
        },
      },
      MuiButton: {
        defaultProps: {
          disableElevation: true,
        },
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 600,
          },
        },
      },
      MuiCard: {
        defaultProps: {
          variant: 'outlined',
        },
      },
      MuiTextField: {
        defaultProps: {
          size: 'small',
          variant: 'outlined',
        },
      },
      MuiTableCell: {
        styleOverrides: {
          head: {
            fontWeight: 600,
          },
        },
      },
    },
  });
}

/**
 * UI-NFR-019 §2.7 — high-contrast theme. Pure black/white surfaces (R-041),
 * medium+ font weight (R-042), no elevation/gradients/hover tints (R-043).
 * Built on the light base so shared component conventions are preserved.
 */
function buildHighContrastTheme(): Theme {
  return createTheme(buildTheme('light'), {
    palette: highContrastPalette,
    typography: {
      // R-042 — minimum Medium weight throughout.
      fontWeightRegular: 500,
      body1: { fontWeight: 500 },
      body2: { fontWeight: 500 },
    },
    components: {
      MuiPaper: {
        defaultProps: { elevation: 0 },
        styleOverrides: {
          root: { backgroundImage: 'none', boxShadow: 'none' },
        },
      },
      MuiCard: {
        defaultProps: { variant: 'outlined' },
        styleOverrides: {
          root: { borderColor: '#000000', borderWidth: 2, boxShadow: 'none' },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: { boxShadow: 'none' },
          outlined: { borderWidth: 2, borderColor: '#000000' },
        },
      },
      MuiAppBar: {
        defaultProps: { elevation: 0 },
        styleOverrides: {
          root: { boxShadow: 'none', borderBottom: '2px solid #000000' },
        },
      },
    },
  });
}

export const lightTheme = buildTheme('light');
export const darkTheme = buildTheme('dark');
export const highContrastTheme = buildHighContrastTheme();

/** Kiosk theme = high-contrast base + touch-target overrides (UI-NFR-019). */
export const kioskHighContrastTheme = createTheme(highContrastTheme, kioskThemeOverrides);
export const kioskLightTheme = createTheme(lightTheme, kioskThemeOverrides);
export const kioskDarkTheme = createTheme(darkTheme, kioskThemeOverrides);

/**
 * Resolve the effective application theme from the current mode and kiosk flags
 * (UI-NFR-019). The switch is pure so {@link ThemeContext} can flip themes
 * without a page reload (R-004).
 */
export function selectAppTheme(
  mode: 'light' | 'dark',
  isKiosk: boolean,
  highContrast: boolean,
): Theme {
  if (isKiosk) {
    if (highContrast) return kioskHighContrastTheme;
    return mode === 'dark' ? kioskDarkTheme : kioskLightTheme;
  }
  if (highContrast) return highContrastTheme;
  return mode === 'dark' ? darkTheme : lightTheme;
}
