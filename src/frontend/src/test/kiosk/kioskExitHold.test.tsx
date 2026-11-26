import { act, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import i18n from 'i18next';
import { ThemeContextProvider } from '@/theme';
import KioskAppBar from '@/components/kiosk/KioskAppBar';
import KioskSettingsTab from '@/pages/auth/KioskSettingsTab';
import { KioskContext, type KioskContextValue } from '@/kiosk/KioskProvider';
import { KIOSK_LONG_PRESS_MS } from '@/kiosk/longPress';
import { createTestStore } from '@/test/helpers';

/**
 * Operator decision 2026-11-27 — leaving kiosk mode is held for 2 s wherever a visitor can reach
 * it inside the kiosk shell: the app bar's "Kiosk verlassen" and the settings page's switch-off.
 * A tap and a hold one millisecond short do not leave; the full hold leaves exactly once; the
 * keyboard / assistive path (a click without a pointer press) leaves directly.
 */

function kioskValue(isKiosk: boolean, disableKiosk: () => void): KioskContextValue {
  return {
    isKiosk,
    highContrast: isKiosk,
    enableKiosk: vi.fn(),
    disableKiosk,
    toggleKiosk: vi.fn(),
    setHighContrast: vi.fn(),
  };
}

function renderAt(ui: React.ReactNode, disableKiosk: () => void, isKiosk = true) {
  const router = createMemoryRouter(
    [
      { path: '/giessprotokoll', element: ui },
      { path: '/dashboard', element: <div data-testid="dashboard-route" /> },
      { path: '/kiosk', element: <div /> },
    ],
    { initialEntries: ['/giessprotokoll'] },
  );
  render(
    <Provider store={createTestStore()}>
      <KioskContext.Provider value={kioskValue(isKiosk, disableKiosk)}>
        <ThemeContextProvider>
          <RouterProvider router={router} />
        </ThemeContextProvider>
      </KioskContext.Provider>
    </Provider>,
  );
  return router;
}

function tap(el: Element) {
  fireEvent.pointerDown(el, { button: 0, isPrimary: true });
  fireEvent.pointerUp(el, { button: 0 });
  fireEvent.click(el, { detail: 1 });
}

async function settle() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(0);
  });
}

beforeEach(() => {
  i18n.changeLanguage('de');
});

afterEach(() => {
  vi.useRealTimers();
});

describe('"Kiosk verlassen" in the kiosk app bar', () => {
  it('does not leave on a tap or a 1999 ms hold, and leaves exactly once after 2000 ms', async () => {
    vi.useFakeTimers();
    const disableKiosk = vi.fn();
    const router = renderAt(<KioskAppBar />, disableKiosk);
    await settle();
    const exit = screen.getByTestId('kiosk-exit-button');

    tap(exit);
    fireEvent.pointerDown(exit, { button: 0, isPrimary: true });
    act(() => void vi.advanceTimersByTime(KIOSK_LONG_PRESS_MS - 1));
    fireEvent.pointerUp(exit, { button: 0 });
    fireEvent.click(exit, { detail: 1 });
    expect(disableKiosk).not.toHaveBeenCalled();
    expect(router.state.location.pathname).toBe('/giessprotokoll');

    fireEvent.pointerDown(exit, { button: 0, isPrimary: true });
    act(() => void vi.advanceTimersByTime(KIOSK_LONG_PRESS_MS));
    fireEvent.pointerUp(exit, { button: 0 });
    fireEvent.click(exit, { detail: 1 });
    expect(disableKiosk).toHaveBeenCalledTimes(1);
    expect(router.state.location.pathname).toBe('/dashboard');
  });

  it('leaves directly by keyboard, and names the hold in its description', async () => {
    const disableKiosk = vi.fn();
    const user = userEvent.setup();
    const router = renderAt(<KioskAppBar />, disableKiosk);
    const exit = await screen.findByTestId('kiosk-exit-button');

    expect(exit).toHaveAccessibleName('Kiosk verlassen');
    expect(exit).toHaveAccessibleDescription(/Zum Verlassen 2 Sekunden gedrückt halten/);

    exit.focus();
    await user.keyboard('{Enter}');
    expect(disableKiosk).toHaveBeenCalledTimes(1);
    expect(router.state.location.pathname).toBe('/dashboard');
  });
});

describe('kiosk switch-off on the settings page inside the kiosk shell', () => {
  it('is held: a tap and a 1999 ms hold keep kiosk mode, 2000 ms turns it off once', async () => {
    vi.useFakeTimers();
    const disableKiosk = vi.fn();
    renderAt(<KioskSettingsTab />, disableKiosk);
    await settle();
    expect(screen.queryByTestId('kiosk-mode-toggle')).toBeNull();
    const off = screen.getByTestId('kiosk-mode-exit');

    tap(off);
    fireEvent.pointerDown(off, { button: 0, isPrimary: true });
    act(() => void vi.advanceTimersByTime(KIOSK_LONG_PRESS_MS - 1));
    fireEvent.pointerUp(off, { button: 0 });
    expect(disableKiosk).not.toHaveBeenCalled();

    fireEvent.pointerDown(off, { button: 0, isPrimary: true });
    act(() => void vi.advanceTimersByTime(KIOSK_LONG_PRESS_MS));
    fireEvent.pointerUp(off, { button: 0 });
    fireEvent.click(off, { detail: 1 });
    expect(disableKiosk).toHaveBeenCalledTimes(1);
  });

  it('turns kiosk mode off directly by keyboard', async () => {
    const disableKiosk = vi.fn();
    const user = userEvent.setup();
    renderAt(<KioskSettingsTab />, disableKiosk);
    const off = await screen.findByTestId('kiosk-mode-exit');

    expect(off).toHaveAccessibleName('Kiosk-Modus beenden');
    off.focus();
    await user.keyboard('{Enter}');
    expect(disableKiosk).toHaveBeenCalledTimes(1);
  });

  it("keeps the operator's way in a plain switch outside kiosk mode", () => {
    renderAt(<KioskSettingsTab />, vi.fn(), false);
    expect(screen.getByTestId('kiosk-mode-toggle')).toBeInTheDocument();
    expect(screen.queryByTestId('kiosk-mode-exit')).toBeNull();
  });
});
