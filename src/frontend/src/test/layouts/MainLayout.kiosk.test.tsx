import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { ThemeContextProvider } from '@/theme';
import MainLayout from '@/layouts/MainLayout';
import { KioskProvider } from '@/kiosk/KioskProvider';
import { createTestStore } from '@/test/helpers';
import { server } from '@/test/mocks/server';

// Light mode keeps KioskProvider from attempting a server preference sync,
// mirroring MainLayout.light.test.tsx.
vi.mock('@/config/mode', () => ({
  isLightMode: true,
  isFullMode: false,
  KAMERPLANTER_MODE: 'light',
}));

function stubLocalStorage(seed?: Record<string, string>) {
  const store = new Map<string, string>(Object.entries(seed ?? {}));
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
    setItem: (k: string, v: string) => void store.set(k, String(v)),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
  });
  // Sidebar's responsive drawer variant relies on useMediaQuery — MainLayout's
  // own tests leave jsdom's real matchMedia in place rather than a partial
  // stub, so this mirrors that pattern instead of breaking addEventListener.
}

function renderMainLayoutOnADashboardRoute() {
  const router = createMemoryRouter(
    [
      {
        path: '/dashboard',
        element: <MainLayout />,
        children: [{ index: true, element: <div data-testid="dashboard-marker" /> }],
      },
      { path: '/kiosk', element: <div data-testid="kiosk-route-marker" /> },
    ],
    { initialEntries: ['/dashboard'] },
  );
  return render(
    <Provider store={createTestStore()}>
      <KioskProvider>
        <ThemeContextProvider>
          <RouterProvider router={router} />
        </ThemeContextProvider>
      </KioskProvider>
    </Provider>,
  );
}

/**
 * UI-NFR-019 R-003/R-018 — a kiosk quick-action tile navigates out of the
 * dedicated /kiosk shell into a regular MainLayout page (e.g. the watering
 * log). The permanent "Kiosk" indicator and a way back to the kiosk start
 * page must keep showing there too, not just inside KioskLayout.
 */
describe('MainLayout kiosk-mode indicator (UI-NFR-019 R-003, R-018)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    server.use(
      http.get('/api/v1/t/:tenant/notifications/count', () =>
        HttpResponse.json({ unread_count: 0 }),
      ),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows no kiosk badge or Home button outside kiosk mode', () => {
    stubLocalStorage();
    renderMainLayoutOnADashboardRoute();

    expect(screen.queryByTestId('kiosk-badge')).toBeNull();
    expect(screen.queryByTestId('kiosk-home-button')).toBeNull();
  });

  it('keeps the kiosk badge and Home button visible on a page reached from a kiosk tile', async () => {
    stubLocalStorage({
      'kp-kiosk-preference': JSON.stringify({ kiosk_enabled: true, high_contrast: true }),
    });
    const user = userEvent.setup();
    renderMainLayoutOnADashboardRoute();

    expect(screen.getByTestId('kiosk-badge')).toHaveTextContent('Kiosk');
    const home = screen.getByRole('button', { name: 'Start' });
    expect(home).toBeInTheDocument();

    await user.click(home);
    expect(screen.getByTestId('kiosk-route-marker')).toBeInTheDocument();
  });
});
