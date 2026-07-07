import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';

import MainLayout from '@/layouts/MainLayout';
import { createTestStore, renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

function storeWithUser() {
  return createTestStore({
    auth: {
      user: {
        key: 'user-1',
        email: 'demo@kamerplanter.local',
        display_name: 'Demo Nutzer',
        avatar_url: null,
      },
      isAuthenticated: true,
      isLoading: false,
      error: null,
    },
  });
}

describe('MainLayout (full mode)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    // MainLayout reads localStorage un-guarded at render; the test environment's
    // localStorage lacks getItem/setItem, so back it with a Map.
    const store = new Map<string, string>();
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
      setItem: (k: string, v: string) => store.set(k, String(v)),
      removeItem: (k: string) => store.delete(k),
      clear: () => store.clear(),
    });
    // Silence the NotificationBell poll so it does not hit the network.
    server.use(
      http.get('/api/v1/t/test-tenant/notifications/count', () =>
        HttpResponse.json({ unread_count: 0 }),
      ),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the top bar, skip link and breadcrumbs', () => {
    renderWithProviders(<MainLayout />, {
      store: storeWithUser(),
      route: '/pflanzen/plant-instances',
    });

    expect(screen.getByText('Zum Inhalt springen')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Seitenleiste umschalten' })).toBeInTheDocument();
    // Breadcrumbs render for a mapped route.
    expect(screen.getByLabelText('breadcrumb')).toBeInTheDocument();
  });

  it('toggles the sidebar state when the menu icon is clicked', async () => {
    const user = userEvent.setup();
    const { store } = renderWithProviders(<MainLayout />, { store: storeWithUser() });
    const before = store.getState().ui.sidebarOpen;

    await user.click(screen.getByRole('button', { name: 'Seitenleiste umschalten' }));

    expect(store.getState().ui.sidebarOpen).toBe(!before);
  });

  it('opens the account menu showing the user identity and its entries', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MainLayout />, { store: storeWithUser() });

    await user.click(screen.getByRole('button', { name: 'Konto-Menü' }));

    expect(screen.getByText('Demo Nutzer')).toBeInTheDocument();
    expect(screen.getByText('demo@kamerplanter.local')).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: 'Kontoeinstellungen' })).toBeInTheDocument();
    expect(screen.getByTestId('menu-privacy')).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: 'Abmelden' })).toBeInTheDocument();
  });

  it('renders the avatar initial from the display name', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MainLayout />, { store: storeWithUser() });
    // "Demo Nutzer" → initial "D".
    expect(screen.getByRole('button', { name: 'Konto-Menü' })).toHaveTextContent('D');
    // Menu is closed initially.
    expect(screen.queryByRole('menuitem', { name: 'Abmelden' })).toBeNull();
    await user.click(screen.getByRole('button', { name: 'Konto-Menü' }));
    expect(screen.getByRole('menuitem', { name: 'Abmelden' })).toBeInTheDocument();
  });

  it('closes the menu when the settings entry is chosen', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MainLayout />, { store: storeWithUser() });

    await user.click(screen.getByRole('button', { name: 'Konto-Menü' }));
    await user.click(screen.getByRole('menuitem', { name: 'Kontoeinstellungen' }));

    await waitFor(() =>
      expect(screen.queryByRole('menuitem', { name: 'Abmelden' })).toBeNull(),
    );
  });

  it('closes the menu when the privacy entry is chosen', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MainLayout />, { store: storeWithUser() });

    await user.click(screen.getByRole('button', { name: 'Konto-Menü' }));
    await user.click(screen.getByTestId('menu-privacy'));

    await waitFor(() =>
      expect(screen.queryByTestId('menu-privacy')).toBeNull(),
    );
  });

  it('logs the user out, clearing the auth user', async () => {
    const user = userEvent.setup();
    const { store } = renderWithProviders(<MainLayout />, { store: storeWithUser() });

    await user.click(screen.getByRole('button', { name: 'Konto-Menü' }));
    await user.click(screen.getByRole('menuitem', { name: 'Abmelden' }));

    await waitFor(() => expect(store.getState().auth.user).toBeNull());
  });

  it('renders a fallback person icon when no display name is present', () => {
    const store = createTestStore({
      auth: {
        user: { key: 'user-2', email: 'x@y.z', display_name: '', avatar_url: null },
        isAuthenticated: true,
        isLoading: false,
        error: null,
      },
    });
    renderWithProviders(<MainLayout />, { store });
    const menuButton = screen.getByRole('button', { name: 'Konto-Menü' });
    expect(menuButton.querySelector('[data-testid="PersonIcon"]')).toBeInTheDocument();
  });
});
