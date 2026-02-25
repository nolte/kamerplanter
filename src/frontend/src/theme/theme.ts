import { createTheme, type Theme } from '@mui/material/styles';
import { lightPalette, darkPalette } from './palette';
import { typography } from './typography';
import { breakpoints, radii } from './tokens';

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

export const lightTheme = buildTheme('light');
export const darkTheme = buildTheme('dark');
