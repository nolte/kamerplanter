/**
 * #3017 (W-08/L-07, N-21) — theme-wide focus ring and touch-target minimum.
 *
 * Focus: UI-NFR-002 R-005 asks for a ≥2 px outline with ≥3:1 contrast to the background. MUI's own cue on
 * ListItemButton / MenuItem / IconButton was a ~12 % tint (≈1.3:1).
 * Targets: UI-NFR-001 R-011 asks for 48×48 px touch targets; R-013 lets a mouse-driven desktop go smaller.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import CssBaseline from '@mui/material/CssBaseline';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import { ThemeProvider, getContrastRatio, type Theme } from '@mui/material/styles';
import {
  darkTheme,
  highContrastTheme,
  kioskHighContrastTheme,
  kioskLightTheme,
  lightTheme,
  TOUCH_TARGET_MIN,
} from '@/theme/theme';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';

type Styles = Record<string, Record<string, unknown>>;

function baselineStyles(theme: Theme): Styles {
  const overrides = theme.components?.MuiCssBaseline?.styleOverrides;
  expect(typeof overrides).toBe('function');
  return (overrides as unknown as (t: Theme) => Styles)(theme);
}

function iconButtonRoot(theme: Theme): Record<string, Record<string, number>> {
  return theme.components?.MuiIconButton?.styleOverrides?.root as Record<string, Record<string, number>>;
}

const MODES: [string, Theme][] = [
  ['light', lightTheme],
  ['dark', darkTheme],
  ['high contrast', highContrastTheme],
];

describe('global focus ring (#3017)', () => {
  it.each(MODES)('is a 2px outline reaching >= 3:1 on every %s surface', (_mode, theme) => {
    const ring = baselineStyles(theme)['.MuiButtonBase-root.Mui-focusVisible'];
    expect(ring).toBeDefined();
    const outline = String(ring.outline);
    expect(outline).toMatch(/^2px solid /);
    const color = outline.replace('2px solid ', '');
    expect(color).toBe(theme.palette.primary.main);
    for (const surface of [theme.palette.background.default, theme.palette.background.paper]) {
      expect(getContrastRatio(color, surface)).toBeGreaterThanOrEqual(3);
    }
  });

  it('draws list-like rows inside their box so a clipping container cannot hide it', () => {
    const styles = baselineStyles(lightTheme);
    const insetKey = Object.keys(styles).find((k) => k.includes('.MuiMenuItem-root.Mui-focusVisible'));
    expect(insetKey).toBeDefined();
    expect(insetKey).toContain('.MuiListItemButton-root.Mui-focusVisible');
    expect(styles[insetKey!].outlineOffset).toBe(-2);
  });

  it('reaches a keyboard-focused IconButton in the rendered app', async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider theme={lightTheme}>
        <CssBaseline />
        <IconButton aria-label="settings">x</IconButton>
      </ThemeProvider>,
    );
    await user.tab();
    const button = screen.getByRole('button', { name: 'settings' });
    expect(button).toHaveClass('Mui-focusVisible');
    // jsdom resolves the shorthand only.
    expect(getComputedStyle(button).outline).toBe(`2px solid ${lightTheme.palette.primary.main}`);
  });

  it('applies the inset ring to a focus-visible sidebar ListItemButton', () => {
    // jsdom's focus-visible heuristic does not flag a ListItemButton reached by Tab; the class MUI sets
    // in a browser is applied directly so the stylesheet itself is what is under test.
    render(
      <ThemeProvider theme={lightTheme}>
        <CssBaseline />
        <List>
          <ListItemButton className="Mui-focusVisible">first</ListItemButton>
        </List>
      </ThemeProvider>,
    );
    const item = screen.getByRole('button', { name: 'first' });
    const style = getComputedStyle(item);
    expect(style.outline).toBe(`2px solid ${lightTheme.palette.primary.main}`);
    expect(style.outlineOffset).toBe('-2px');
  });
});

describe('IconButton touch-target minimum (#3017, UI-NFR-001 R-011)', () => {
  it('is 48x48 px under a coarse pointer and leaves fine pointers alone (R-013)', () => {
    const root = iconButtonRoot(lightTheme);
    expect(TOUCH_TARGET_MIN).toBe(48);
    expect(root['@media (pointer: coarse)']).toEqual({ minWidth: 48, minHeight: 48 });
    expect(root.minWidth).toBeUndefined();
  });

  it('keeps the kiosk 64 px minimum on touch screens, where the base media query would otherwise win', () => {
    for (const theme of [kioskLightTheme, kioskHighContrastTheme]) {
      const root = iconButtonRoot(theme);
      expect(root['@media (pointer: coarse)']).toEqual({
        minWidth: KIOSK_TOUCH_TARGET,
        minHeight: KIOSK_TOUCH_TARGET,
      });
    }
  });
});
