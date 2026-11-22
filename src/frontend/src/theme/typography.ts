import { type ThemeOptions } from '@mui/material/styles';

/**
 * System font stack (operator decision 2026-11-18, #3021): no web font is
 * loaded and no font dependency is added. Every platform renders its own UI
 * font — San Francisco, Segoe UI, Roboto on Android, Cantarell/Noto on Linux.
 * Before this, the theme named "Roboto" without ever loading it, so desktops
 * without a local Roboto silently fell back to Helvetica/Arial.
 */
export const SYSTEM_FONT_STACK =
  'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji"';

export const typography: ThemeOptions['typography'] = {
  fontFamily: SYSTEM_FONT_STACK,
  h1: {
    fontSize: '2rem',
    fontWeight: 600,
    lineHeight: 1.2,
  },
  h2: {
    fontSize: '1.75rem',
    fontWeight: 600,
    lineHeight: 1.3,
  },
  h3: {
    fontSize: '1.5rem',
    fontWeight: 600,
    lineHeight: 1.3,
  },
  h4: {
    fontSize: '1.25rem',
    fontWeight: 600,
    lineHeight: 1.4,
  },
  h5: {
    fontSize: '1.125rem',
    fontWeight: 600,
    lineHeight: 1.4,
  },
  h6: {
    fontSize: '1rem',
    fontWeight: 600,
    lineHeight: 1.5,
  },
  body1: {
    fontSize: '1rem',
    lineHeight: 1.5,
  },
  body2: {
    fontSize: '0.875rem',
    lineHeight: 1.43,
  },
  caption: {
    fontSize: '0.75rem',
    lineHeight: 1.66,
  },
};
