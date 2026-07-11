import { type PaletteOptions } from '@mui/material/styles';

export const lightPalette: PaletteOptions = {
  mode: 'light',
  primary: {
    main: '#2e7d32',
    light: '#60ad5e',
    dark: '#005005',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#5c6bc0',
    light: '#8e99f3',
    dark: '#26418f',
    contrastText: '#ffffff',
  },
  error: {
    main: '#d32f2f',
  },
  warning: {
    main: '#ed6c02',
  },
  success: {
    main: '#2e7d32',
  },
  background: {
    default: '#f5f5f5',
    paper: '#ffffff',
  },
};

/**
 * UI-NFR-019 §2.7 — high-contrast palette for kiosk & outdoor use. Pure
 * black-on-white surfaces (R-041), all text ≥ 7:1 against white (WCAG AAA,
 * R-040). Action colors keep a distinct hue but stay dark enough that their
 * white contrast text also clears 7:1 (used on filled buttons/chips).
 */
export const highContrastPalette: PaletteOptions = {
  mode: 'light',
  common: {
    black: '#000000',
    white: '#ffffff',
  },
  primary: {
    main: '#000000',
    light: '#000000',
    dark: '#000000',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#0b3d91',
    light: '#0b3d91',
    dark: '#062561',
    contrastText: '#ffffff',
  },
  error: {
    main: '#b71c1c',
    contrastText: '#ffffff',
  },
  warning: {
    main: '#8a5000',
    contrastText: '#ffffff',
  },
  success: {
    main: '#1b5e20',
    contrastText: '#ffffff',
  },
  info: {
    main: '#0b3d91',
    contrastText: '#ffffff',
  },
  background: {
    default: '#ffffff',
    paper: '#ffffff',
  },
  text: {
    primary: '#000000',
    secondary: '#000000',
  },
  divider: '#000000',
};

export const darkPalette: PaletteOptions = {
  mode: 'dark',
  primary: {
    main: '#66bb6a',
    light: '#98ee99',
    dark: '#338a3e',
    contrastText: '#000000',
  },
  secondary: {
    main: '#9fa8da',
    light: '#d1d9ff',
    dark: '#6f79a8',
    contrastText: '#000000',
  },
  error: {
    main: '#ef5350',
  },
  warning: {
    main: '#ffa726',
  },
  success: {
    main: '#66bb6a',
  },
  background: {
    default: '#121212',
    paper: '#1e1e1e',
  },
};
