import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';

// Force light mode for this whole file. tenantSlice/client also read this flag,
// which is fine — light mode simply resolves a fixed tenant slug.
vi.mock('@/config/mode', () => ({
  KAMERPLANTER_MODE: 'light',
  isLightMode: true,
  isFullMode: false,
}));

import MainLayout from '@/layouts/MainLayout';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const WARNING_KEY = 'kp-light-mode-warning-dismissed';

describe('MainLayout (light mode)', () => {
  let originalLocation: Location;

  beforeEach(() => {
    i18n.changeLanguage('de');
    // The test environment's localStorage lacks getItem/setItem, but MainLayout's
    // light-mode warning reads it un-guarded. Provide a Map-backed stand-in.
    const store = new Map<string, string>();
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
      setItem: (k: string, v: string) => store.set(k, String(v)),
      removeItem: (k: string) => store.delete(k),
      clear: () => store.clear(),
    });
    server.use(
      http.get('/api/v1/t/:tenant/notifications/count', () =>
        HttpResponse.json({ unread_count: 0 }),
      ),
    );
    originalLocation = window.location;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
  });

  function setHostname(hostname: string) {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...originalLocation, hostname, reload: vi.fn() },
    });
  }

  it('renders a settings icon instead of the account menu and hides the tenant switcher', async () => {
    setHostname('localhost');
    const user = userEvent.setup();
    renderWithProviders(<MainLayout />);

    const settings = screen.getByRole('button', { name: 'Kontoeinstellungen' });
    expect(settings).toBeInTheDocument();
    // No avatar/account menu and no tenant switcher in light mode.
    expect(screen.queryByRole('button', { name: 'Konto-Menü' })).toBeNull();
    expect(screen.queryByRole('button', { name: /Garten wählen/ })).toBeNull();

    // The settings shortcut navigates without throwing.
    await user.click(settings);
    expect(settings).toBeInTheDocument();
  });

  it('does not show the light-mode warning on a private network', () => {
    setHostname('192.168.1.10');
    renderWithProviders(<MainLayout />);
    expect(screen.queryByText(/Light-Modus/)).toBeNull();
  });

  it('shows the light-mode warning on a public host and lets the user dismiss it', async () => {
    setHostname('app.example.com');
    const user = userEvent.setup();
    renderWithProviders(<MainLayout />);

    const warning = await screen.findByText(/Light-Modus/);
    expect(warning).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Close' }));

    await waitFor(() => expect(screen.queryByText(/Light-Modus/)).toBeNull());
    expect(localStorage.getItem(WARNING_KEY)).toBe('true');
  });

  it('keeps the warning hidden when previously dismissed', () => {
    localStorage.setItem(WARNING_KEY, 'true');
    setHostname('app.example.com');
    renderWithProviders(<MainLayout />);
    expect(screen.queryByText(/Light-Modus/)).toBeNull();
  });
});
