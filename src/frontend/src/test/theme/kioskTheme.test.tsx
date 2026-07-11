import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import Button from '@mui/material/Button';
import { useTheme } from '@mui/material/styles';
import { Provider } from 'react-redux';
import {
  selectAppTheme,
  lightTheme,
  highContrastTheme,
  kioskHighContrastTheme,
} from '@/theme/theme';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import { ThemeContextProvider } from '@/theme/ThemeContext';
import { KioskProvider, useKiosk } from '@/kiosk/KioskProvider';
import { createTestStore } from '@/test/helpers';

vi.mock('@/config/mode', () => ({
  isLightMode: true,
  isFullMode: false,
  KAMERPLANTER_MODE: 'light',
}));

function stubLocalStorage() {
  const store = new Map<string, string>();
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
  });
  vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({ matches: false } as MediaQueryList));
}

describe('selectAppTheme (UI-NFR-019)', () => {
  it('returns the standard light theme in normal mode', () => {
    expect(selectAppTheme('light', false, false)).toBe(lightTheme);
  });

  it('returns the high-contrast theme when high-contrast is on (R-045)', () => {
    expect(selectAppTheme('light', false, true)).toBe(highContrastTheme);
  });

  it('returns the kiosk high-contrast theme in kiosk mode (R-005)', () => {
    expect(selectAppTheme('light', true, true)).toBe(kioskHighContrastTheme);
  });

  it('high-contrast theme uses pure black-on-white surfaces (R-040, R-041)', () => {
    expect(highContrastTheme.palette.background.default).toBe('#ffffff');
    expect(highContrastTheme.palette.text.primary).toBe('#000000');
  });

  it('high-contrast body text is at least medium weight (R-042)', () => {
    expect(Number(highContrastTheme.typography.fontWeightRegular)).toBeGreaterThanOrEqual(500);
  });

  it('kiosk theme enforces large touch targets and size defaults (R-007, R-013)', () => {
    const button = kioskHighContrastTheme.components?.MuiButton;
    expect(button?.defaultProps?.size).toBe('large');
    const root = button?.styleOverrides?.root as { minHeight?: number };
    expect(root.minHeight).toBe(KIOSK_TOUCH_TARGET);

    const iconButton = kioskHighContrastTheme.components?.MuiIconButton;
    const iconRoot = iconButton?.styleOverrides?.root as { minHeight?: number; minWidth?: number };
    expect(iconRoot.minHeight).toBe(KIOSK_TOUCH_TARGET);
    expect(iconRoot.minWidth).toBe(KIOSK_TOUCH_TARGET);
  });
});

function ThemeProbe() {
  const theme = useTheme();
  const { enableKiosk } = useKiosk();
  return (
    <div>
      <span data-testid="bg">{theme.palette.background.default}</span>
      <Button onClick={() => enableKiosk()}>enable</Button>
    </div>
  );
}

describe('ThemeContext kiosk integration', () => {
  beforeEach(() => stubLocalStorage());
  afterEach(() => vi.unstubAllGlobals());

  it('switches to the high-contrast theme without a reload (R-004, R-005)', async () => {
    const user = userEvent.setup();
    render(
      <Provider store={createTestStore()}>
        <KioskProvider>
          <ThemeContextProvider>
            <ThemeProbe />
          </ThemeContextProvider>
        </KioskProvider>
      </Provider>,
    );

    expect(screen.getByTestId('bg')).toHaveTextContent('#f5f5f5');

    await act(async () => {
      await user.click(screen.getByRole('button', { name: 'enable' }));
    });

    expect(screen.getByTestId('bg')).toHaveTextContent('#ffffff');
  });
});
