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
