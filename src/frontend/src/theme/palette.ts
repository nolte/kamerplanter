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
  // `#ed6c02` is the documented brand warning colour and stays exactly as it is:
  // as a fill, icon or illustration colour it owes only 3:1 (WCAG 1.4.11) and
  // clears it. What fails is the *text MUI puts on top of it* — `contrastText`
  // is derived from `contrastThreshold`, which defaults to 3, so `#ed6c02`
  // clears the threshold, MUI picks white, and white on that orange measures
  // 3.11:1, under WCAG AA's 4.5:1 for normal text (UI-NFR-002, issue #1289).
  // Contrast is symmetric, so it is the same 3.11:1 read either way.
  //
  // Black rather than white: 6.75:1 on the same orange, one line, every filled
  // warning surface at once. The alternatives were rejected on blast radius, not
  // on taste — raising `contrastThreshold` to 4.5 would silently re-decide
  // `error` (`#d32f2f`, ~4.5:1 borderline) and every future palette entry
  // between 3 and 4.5, and darkening `main` would move a brand token that is
  // also the favourite-star colour in six places.
  //
  // Light palette only. `darkPalette.warning` is `#ffa726`, on which MUI already
  // derives near-black (measured 9.14:1), and `highContrastPalette` states its
  // own `contrastText` on a much darker orange (7.54:1) — neither is touched.
  warning: {
    main: '#ed6c02',
    contrastText: '#000000',
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
  // R-040 — #b71c1c only reaches 6.57:1 against white, below the required
  // 7:1 (WCAG AAA). #a41919 clears it with margin (7.69:1) while staying
  // recognizably red.
  error: {
    main: '#a41919',
    contrastText: '#ffffff',
  },
  // R-040 — #8a5000 only reaches 6.51:1 against white. #7c4800 clears it
  // with margin (7.54:1) while staying a recognizable amber/brown.
  warning: {
    main: '#7c4800',
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
