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
    expect(screen.getByRole('navigation', { name: 'Brotkrumen-Navigation' })).toBeInTheDocument();
  });

  it('mounts the route announcer next to main (#3017, W-02)', () => {
    renderWithProviders(<MainLayout />, { store: storeWithUser(), route: '/pflanzen/plant-instances' });
    const region = screen.getByTestId('route-announcer');
    expect(region).toHaveAttribute('aria-live', 'polite');
    expect(screen.getByRole('main')).toHaveAttribute('id', 'main-content');
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
    expect(screen.getByRole('menuitem', { name: 'Einstellungen' })).toBeInTheDocument();
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
    await user.click(screen.getByRole('menuitem', { name: 'Einstellungen' }));

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
  // #3157 — the app bar lies above every drawer (`zIndex: drawer + 1`), so the notification drawer has to start
  // where the bar ends: from the top of the viewport its header and close button sat under the bar (the E2E
  // nightly measured the press landing on the bar's toolbar / avatar instead). jsdom resolves no media query, so
  // the xs values are read as computed styles and the `sm` / landscape values from the emitted rules.
  it('starts the notification drawer below the app bar that lies above it', async () => {
    server.use(
      http.get('/api/v1/t/test-tenant/notifications', () =>
        HttpResponse.json({ items: [], total: 0, unread_count: 0 }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<MainLayout />, { store: storeWithUser() });

    await user.click(screen.getByTestId('notification-bell'));
    const drawer = await screen.findByTestId('notification-drawer');
    const paper = drawer.querySelector('.MuiDrawer-paper') as HTMLElement;
    // Queried directly: the open modal drawer hides the rest of the page from the accessibility tree.
    const bar = document.querySelector('header.MuiAppBar-root') as HTMLElement;
    const toolbar = bar.querySelector('.MuiToolbar-root') as HTMLElement;

    // The reason for the offset: the bar is stacked above the drawer.
    expect(Number(window.getComputedStyle(bar).zIndex)).toBeGreaterThan(
      Number(window.getComputedStyle(drawer).zIndex),
    );
    // The paper begins at the bar's height and keeps its bottom on screen.
    const barHeight = window.getComputedStyle(toolbar).minHeight;
    expect(barHeight).toBe('56px');
    expect(window.getComputedStyle(paper).top).toBe(barHeight);
    expect(window.getComputedStyle(paper).height).toBe(`calc(100% - ${barHeight})`);

    const paperClass = [...paper.classList].find((c) => /^css-/.test(c));
    const toolbarClass = [...toolbar.classList].find((c) => /^css-/.test(c));
    const css = [...document.querySelectorAll('style')].map((s) => s.textContent).join('\n');
    const escape = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    // The theme's mixin nests the landscape height in a `min-width:0px` query; emotion emits it nested.
    for (const media of ['@media (min-width:600px)', '@media (min-width:0px){@media (orientation: landscape)']) {
      const toolbarRule = new RegExp(`${escape(media)}\\{\\.${toolbarClass}\\{min-height:(\\d+px);\\}`).exec(css);
      expect(toolbarRule, `the bar's height under ${media}`).not.toBeNull();
      const height = toolbarRule![1];
      expect(css).toContain(`${media}{.${paperClass}{top:${height};height:calc(100% - ${height});}`);
    }
    // The offset shares its media queries with the responsive width and must not replace it: full width on a
    // phone, the fixed drawer width from `sm`.
    expect(css).toContain(`@media (min-width:0px){.${paperClass}{width:100%;}`);
    expect(css).toMatch(new RegExp(`@media \\(min-width:600px\\)\\{\\.${paperClass}\\{width:\\d+px;\\}`));
  });
});
