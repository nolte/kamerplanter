import { isValidElement } from 'react';
import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider, type RouteObject } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { ThemeContextProvider } from '@/theme';
import MainLayout from '@/layouts/MainLayout';
import { router as appRouter } from '@/routes/AppRoutes';
import { BOTTOM_NAV_DESTINATIONS } from '@/components/layout/MobileBottomNav';
import { setSidebarOpen } from '@/store/slices/uiSlice';
import { authState, createStoreWithExpertise, createTestStore, flattenRoutes, type TestStore } from '../helpers';
import { restoreViewport, stubViewport } from '../viewport';
import { server } from '../mocks/server';

/**
 * #3018 (audit N-01) — UI-NFR-005 R-010, R-023..R-031: below `md` the shell has a bottom navigation with the
 * same four destinations for every experience level plus "Mehr", which opens the existing sidebar drawer.
 *
 * Rendered through the production path: the `MainLayout` element taken from the app's own route table,
 * inside a real data router, at a phone width. The pages behind the destinations are stand-ins with a
 * heading; the destinations themselves are checked against the real route table.
 */

type ExpertiseLevel = Parameters<typeof createStoreWithExpertise>[0];

const PHONE = 390;
const DESKTOP = 1024;

function layoutElement(routes: RouteObject[]): RouteObject['element'] {
  for (const route of routes) {
    if (isValidElement(route.element) && route.element.type === MainLayout) return route.element;
    const nested = route.children ? layoutElement(route.children) : null;
    if (nested) return nested;
  }
  return null;
}

const page = (title: string) => (
  <>
    <h1>{title}</h1>
    <p>Inhalt</p>
  </>
);

function renderShell(entry: string, store: TestStore = createTestStore(authState())) {
  // `uiSlice` seeds the drawer from the width jsdom had when the module loaded (1024 px); a phone starts with
  // the drawer closed, as `innerWidth >= 768` decides there.
  store.dispatch(setSidebarOpen(window.innerWidth >= 768));
  const router = createMemoryRouter(
    [
      {
        element: layoutElement(appRouter.routes),
        children: [
          { path: '/dashboard', element: page('Dashboard') },
          { path: '/pflanzen/plant-instances', element: page('Pflanzen') },
          { path: '/pflanzen/plant-instances/:key', element: page('Pflanze') },
          { path: '/aufgaben/queue', element: page('Aufgaben') },
          { path: '/aufgaben/tasks/:key', element: page('Aufgabe') },
          { path: '/kalender', element: page('Kalender') },
          { path: '/stammdaten/species', element: page('Arten') },
        ],
      },
    ],
    { initialEntries: [entry] },
  );
  render(
    <Provider store={store}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
  return { router, store };
}

const bottomNav = () => screen.getByRole('navigation', { name: 'Schnellnavigation' });
const entry = (name: string) => within(bottomNav()).getByRole(name === 'Mehr' ? 'button' : 'link', { name });

describe('MainLayout — mobile bottom navigation (#3018, UI-NFR-005 R-023..R-031)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    const storage = new Map<string, string>();
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => storage.get(k) ?? null,
      setItem: (k: string, v: string) => void storage.set(k, String(v)),
      removeItem: (k: string) => void storage.delete(k),
      clear: () => storage.clear(),
    });
    server.use(
      http.get('/api/v1/t/:tenant/notifications/count', () => HttpResponse.json({ unread_count: 0 })),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    restoreViewport();
  });

  it('leads to routes the app actually registers', () => {
    const registered = new Set(flattenRoutes(appRouter.routes).map((r) => `/${r.path}`));
    for (const destination of BOTTOM_NAV_DESTINATIONS) expect(registered).toContain(destination.path);
  });

  it('shows four destinations and "Mehr" in a labelled landmark of its own, labels always visible', async () => {
    stubViewport({ width: PHONE });
    renderShell('/dashboard');
    await screen.findByRole('heading', { name: 'Dashboard' });

    const nav = bottomNav();
    expect(nav.tagName).toBe('NAV');
    // A second landmark of the same name would be indistinguishable for a screen reader.
    expect(screen.getByTestId('sidebar').querySelector('nav')).toHaveAttribute('aria-label', 'Hauptnavigation');

    const links = within(nav).getAllByRole('link');
    expect(links.map((a) => a.textContent)).toEqual(['Start', 'Pflanzen', 'Aufgaben', 'Kalender']);
    expect(links.map((a) => a.getAttribute('href'))).toEqual([
      '/dashboard',
      '/pflanzen/plant-instances',
      '/aufgaben/queue',
      '/kalender',
    ]);
    const more = entry('Mehr');
    expect(more.tagName).toBe('BUTTON');
    // R-027 — 56 px high (the bar's height) and never squeezed below that by MUI's 80 px minimum width.
    for (const action of [...links, more]) {
      expect(window.getComputedStyle(action).minHeight).toBe('56px');
      expect(window.getComputedStyle(action).minWidth).toBe('0px');
      expect(action.querySelector('.MuiBottomNavigationAction-label')).not.toHaveClass(
        'MuiBottomNavigationAction-iconOnly',
      );
    }
  });

  it('keeps every label on one line with an ellipsis, at 12 px, the full text as its name', async () => {
    stubViewport({ width: PHONE });
    renderShell('/dashboard');
    await screen.findByRole('heading', { name: 'Dashboard' });
    for (const name of ['Start', 'Pflanzen', 'Aufgaben', 'Kalender', 'Mehr']) {
      const label = entry(name).querySelector('.MuiBottomNavigationAction-label') as HTMLElement;
      const style = window.getComputedStyle(label);
      expect(style.whiteSpace).toBe('nowrap');
      expect(style.overflow).toBe('hidden');
      expect(style.textOverflow).toBe('ellipsis');
      expect(style.fontSize).toBe('0.75rem');
      expect(window.getComputedStyle(entry(name)).minHeight).toBe('56px');
    }
  });

  it('returns the focus to "Mehr" when the drawer is closed with Escape', async () => {
    stubViewport({ width: PHONE });
    const user = userEvent.setup();
    const { store } = renderShell('/dashboard');
    await screen.findByRole('heading', { name: 'Dashboard' });
    const more = entry('Mehr');
    more.focus();
    await user.keyboard('{Enter}');
    const drawer = await screen.findByRole('dialog');
    await waitFor(() => expect(drawer).toContainElement(document.activeElement as HTMLElement));

    await user.keyboard('{Escape}');

    expect(store.getState().ui.sidebarOpen).toBe(false);
    await waitFor(() => expect(screen.getByTestId('bottom-nav-more')).toHaveFocus());
  });

  it('replaces the hamburger on the phone and leaves the desktop shell as it was', async () => {
    stubViewport({ width: PHONE });
    renderShell('/dashboard');
    await screen.findByRole('heading', { name: 'Dashboard' });
    expect(screen.queryByTestId('sidebar-toggle')).toBeNull();
    expect(bottomNav()).toBeInTheDocument();
  });

  it('renders no bottom navigation at desktop width, where the sidebar and its toggle stay', async () => {
    stubViewport({ width: DESKTOP });
    renderShell('/dashboard');
    await screen.findByRole('heading', { name: 'Dashboard' });
    expect(screen.queryByTestId('bottom-nav')).toBeNull();
    expect(screen.getByTestId('sidebar-toggle')).toBeInTheDocument();
    expect(screen.getByTestId('sidebar').className).toContain('MuiDrawer-docked');
  });

  it('marks the destination of the current route — a detail page included — and never "Mehr"', async () => {
    stubViewport({ width: PHONE });
    renderShell('/pflanzen/plant-instances/p-1');
    await screen.findByRole('heading', { name: 'Pflanze' });

    expect(entry('Pflanzen')).toHaveAttribute('aria-current', 'page');
    expect(entry('Pflanzen')).toHaveClass('Mui-selected');
    for (const name of ['Start', 'Aufgaben', 'Kalender']) expect(entry(name)).not.toHaveAttribute('aria-current');
    expect(entry('Mehr')).not.toHaveAttribute('aria-current');
    expect(entry('Mehr')).not.toHaveClass('Mui-selected');
  });

  it('marks nothing on a page that is none of the four', async () => {
    stubViewport({ width: PHONE });
    renderShell('/stammdaten/species');
    await screen.findByRole('heading', { name: 'Arten' });
    expect(within(bottomNav()).queryByRole('link', { current: 'page' })).toBeNull();
  });

  it('navigates through a real link and moves the active state along', async () => {
    stubViewport({ width: PHONE });
    const user = userEvent.setup();
    const { router } = renderShell('/dashboard');
    await screen.findByRole('heading', { name: 'Dashboard' });

    await user.click(entry('Aufgaben'));
    expect(router.state.location.pathname).toBe('/aufgaben/queue');
    expect(await screen.findByRole('heading', { name: 'Aufgaben' })).toBeInTheDocument();
    expect(entry('Aufgaben')).toHaveAttribute('aria-current', 'page');
    expect(entry('Start')).not.toHaveAttribute('aria-current');
  });

  it('scrolls to the top on a tap of the active destination, without a navigation (R-029)', async () => {
    stubViewport({ width: PHONE });
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
    const user = userEvent.setup();
    const { router } = renderShell('/kalender#list');
    await screen.findByRole('heading', { name: 'Kalender' });
    const before = router.state.location;

    await user.click(entry('Kalender'));

    expect(scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' });
    // Same history entry, and the calendar keeps its view.
    expect(router.state.location).toBe(before);
    expect(router.state.location.hash).toBe('#list');
  });

  it('scrolls without animation when the user asks for reduced motion', async () => {
    stubViewport({ width: PHONE, reducedMotion: true });
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
    const user = userEvent.setup();
    renderShell('/dashboard');
    await screen.findByRole('heading', { name: 'Dashboard' });

    await user.click(entry('Start'));
    expect(scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'auto' });
  });

  it('follows the link from a detail page of the active destination instead of scrolling', async () => {
    stubViewport({ width: PHONE });
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
    const user = userEvent.setup();
    const { router } = renderShell('/aufgaben/tasks/t-1');
    await screen.findByRole('heading', { name: 'Aufgabe' });
    // A task's detail page belongs to the queue.
    expect(entry('Aufgaben')).toHaveAttribute('aria-current', 'page');

    await user.click(entry('Aufgaben'));
    expect(router.state.location.pathname).toBe('/aufgaben/queue');
    expect(scrollTo).not.toHaveBeenCalled();
  });

  it('opens the existing sidebar as a drawer from "Mehr" and works with the keyboard', async () => {
    stubViewport({ width: PHONE });
    const user = userEvent.setup();
    const { store } = renderShell('/dashboard');
    await screen.findByRole('heading', { name: 'Dashboard' });
    const more = entry('Mehr');
    expect(more).toHaveAttribute('aria-haspopup', 'dialog');
    expect(more).toHaveAttribute('aria-expanded', 'false');

    more.focus();
    await user.keyboard('{Enter}');

    expect(store.getState().ui.sidebarOpen).toBe(true);
    // The one sidebar, now as the temporary drawer — not a second menu.
    const drawer = await screen.findByRole('dialog');
    expect(screen.getByTestId('sidebar')).toContainElement(drawer);
    expect(within(drawer).getByRole('navigation', { name: 'Hauptnavigation' })).toBeInTheDocument();
    expect(screen.getAllByTestId('sidebar')).toHaveLength(1);
    await waitFor(() => expect(screen.getByTestId('bottom-nav-more')).toHaveAttribute('aria-expanded', 'true'));
  });

  it('reserves the bar height plus 8 px below the page and publishes the offset (R-031)', async () => {
    stubViewport({ width: PHONE });
    renderShell('/dashboard');
    await screen.findByRole('heading', { name: 'Dashboard' });

    const main = screen.getByRole('main');
    expect(window.getComputedStyle(main).paddingBottom).toBe('calc(var(--kp-bottom-nav-offset, 0px) + 8px)');
    const css = [...document.querySelectorAll('style')].map((s) => s.textContent).join('\n');
    // The offset is the bar plus the phone's safe-area inset; a dialog resets it.
    expect(css).toMatch(/--kp-bottom-nav-offset:\s*calc\(56px \+ env\(safe-area-inset-bottom, 0px\)\)/);
    expect(css).toMatch(/\.MuiDialog-root\{--kp-bottom-nav-offset:\s*0px;\}/);
    expect(css).toMatch(/\.notistack-SnackbarContainer\{bottom:\s*calc\(14px \+ var\(--kp-bottom-nav-offset\)\);\}/);
    // The bar itself sits above the inset (jsdom drops `env()` from the computed style; the rule is read).
    expect(css).toMatch(/position:fixed;[^}]*bottom:0;[^}]*padding-bottom:env\(safe-area-inset-bottom, 0px\)/);
    expect(window.getComputedStyle(bottomNav()).position).toBe('fixed');
  });

  it.each<ExpertiseLevel>(['beginner', 'intermediate', 'expert'])(
    'shows the same destinations for the %s level (R-024)',
    async (level) => {
      stubViewport({ width: PHONE });
      renderShell('/dashboard', createStoreWithExpertise(level));
      await screen.findByRole('heading', { name: 'Dashboard' });
      expect(within(bottomNav()).getAllByRole('link').map((a) => a.textContent)).toEqual([
        'Start',
        'Pflanzen',
        'Aufgaben',
        'Kalender',
      ]);
      expect(entry('Mehr')).toBeInTheDocument();
    },
  );

  it('carries English labels in English', async () => {
    stubViewport({ width: PHONE });
    await act(() => i18n.changeLanguage('en'));
    renderShell('/dashboard');
    const nav = await screen.findByRole('navigation', { name: 'Quick navigation' });
    expect(within(nav).getAllByRole('link').map((a) => a.textContent)).toEqual(['Home', 'Plants', 'Tasks', 'Calendar']);
    expect(within(nav).getByRole('button', { name: 'More' })).toBeInTheDocument();
    await act(() => i18n.changeLanguage('de'));
  });
});
