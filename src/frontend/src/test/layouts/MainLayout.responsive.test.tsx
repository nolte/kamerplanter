import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';

import MainLayout from '@/layouts/MainLayout';
import { sidebarWidth } from '@/theme/tokens';
import { createTestStore, renderWithProviders, type TestStore } from '../helpers';
import { server } from '../mocks/server';

/**
 * Minimal width-driven `matchMedia` stub. jsdom has no layout engine, but MUI's
 * `useMediaQuery` only asks `matchMedia` whether a query matches — evaluating
 * `(min-width: …)` / `(max-width: …)` against a fixed viewport width is enough
 * to put `Sidebar` into its persistent (>= md) or temporary (< md) variant.
 */
function stubViewportWidth(width: number): void {
  window.innerWidth = width;
  window.matchMedia = ((query: string) => {
    const min = /\(min-width:\s*([\d.]+)px\)/.exec(query);
    const max = /\(max-width:\s*([\d.]+)px\)/.exec(query);
    const matches =
      (min === null || width >= Number(min[1])) && (max === null || width <= Number(max[1]));
    return {
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    } as unknown as MediaQueryList;
  }) as typeof window.matchMedia;
}

function storeWithSidebar(sidebarOpen: boolean): TestStore {
  return createTestStore({
    ui: {
      sidebarOpen,
      breadcrumbs: [],
      globalLoading: false,
      showAllFieldsOverride: false,
    },
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

/** The `<main>` element MainLayout renders as the flex sibling of the drawer. */
function mainRegion(): HTMLElement {
  const main = document.getElementById('main-content');
  if (main === null) throw new Error('main content region not rendered');
  return main;
}

describe('MainLayout — horizontal overflow beside the persistent drawer (UI-NFR-001 R-005/R-006)', () => {
  const originalInnerWidth = window.innerWidth;

  beforeEach(() => {
    i18n.changeLanguage('de');
    // MainLayout reads localStorage un-guarded at render; back it with a Map.
    const store = new Map<string, string>();
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
      setItem: (k: string, v: string) => store.set(k, String(v)),
      removeItem: (k: string) => store.delete(k),
      clear: () => store.clear(),
    });
    server.use(
      http.get('/api/v1/t/test-tenant/notifications/count', () =>
        HttpResponse.json({ unread_count: 0 }),
      ),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    window.innerWidth = originalInnerWidth;
    // @ts-expect-error — drop the matchMedia stub so other suites see jsdom's own.
    delete window.matchMedia;
  });

  it('lets the main region shrink beside the 240px persistent drawer at tablet width', () => {
    // 820px: the drawer is already persistent (>= md = 768) and open by default
    // (uiSlice initialises sidebarOpen from innerWidth >= 768), so main has to
    // fit into viewport - 240px.
    stubViewportWidth(820);
    renderWithProviders(<MainLayout />, { store: storeWithSidebar(true) });

    const drawerRoot = screen.getByTestId('sidebar');
    const drawerStyle = window.getComputedStyle(drawerRoot);
    // Precondition of the defect: an in-flow, non-shrinkable 240px flex sibling.
    expect(drawerRoot.className).toContain('MuiDrawer-docked');
    expect(drawerStyle.width).toBe(`${sidebarWidth}px`);
    expect(drawerStyle.flexShrink).toBe('0');

    const mainStyle = window.getComputedStyle(mainRegion());
    // Regression guard: main used to declare `width: 100%`. On a flex item that
    // is both the flex basis and — through the specified size suggestion of the
    // automatic minimum size — a floor it cannot shrink below, so the flex row
    // measured viewport + 240px and the document overflowed by exactly the
    // sidebar width. `minWidth: 0` removes that floor.
    expect(mainStyle.minWidth).toBe('0px');
    expect(mainStyle.width).not.toBe('100%');
    // It still claims the space the drawer leaves.
    expect(mainStyle.flexGrow).toBe('1');
  });

  it('keeps the main region shrinkable when the drawer is toggled closed at tablet width', () => {
    stubViewportWidth(820);
    renderWithProviders(<MainLayout />, { store: storeWithSidebar(false) });

    // Closed persistent drawer: the docked placeholder collapses to 0, so main
    // grows to the full viewport width.
    expect(window.getComputedStyle(screen.getByTestId('sidebar')).width).toBe('0px');

    const mainStyle = window.getComputedStyle(mainRegion());
    expect(mainStyle.minWidth).toBe('0px');
    expect(mainStyle.width).not.toBe('100%');
  });

  it('animates the property that actually changes on a drawer toggle', () => {
    stubViewportWidth(820);
    renderWithProviders(<MainLayout />, { store: storeWithSidebar(true) });

    // `main` used to declare `transition: margin …` although it never sets a
    // margin — an inert declaration, while the docked drawer placeholder that
    // does change jumped 240px → 0 in one frame beside the sliding paper.
    expect(window.getComputedStyle(mainRegion()).transition).not.toContain('margin');
    expect(window.getComputedStyle(screen.getByTestId('sidebar')).transition).toContain('width');
  });

  it('leaves the mobile layout untouched — the drawer overlays instead of docking', () => {
    // < md: the drawer is temporary (a Modal, position: fixed), so it is not an
    // in-flow flex sibling and main occupies the full viewport width. This is the
    // currently-green mobile profile; the fix must not change it.
    stubViewportWidth(393);
    renderWithProviders(<MainLayout />, { store: storeWithSidebar(false) });

    const drawerRoot = screen.getByTestId('sidebar');
    expect(drawerRoot.className).not.toContain('MuiDrawer-docked');
    expect(drawerRoot.className).toContain('MuiDrawer-modal');

    const mainStyle = window.getComputedStyle(mainRegion());
    expect(mainStyle.flexGrow).toBe('1');
    expect(mainStyle.minWidth).toBe('0px');
  });
});
