/**
 * #3014 (audit 2026-11, B-15): a render error in a page must not take the shell
 * down with it. The layout's children sit under a pathless route carrying an
 * `errorElement`, so the error renders inside the layout's outlet and the app
 * bar and sidebar stay usable.
 */
import { isValidElement } from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider, type RouteObject } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { ThemeContextProvider } from '@/theme';
import MainLayout from '@/layouts/MainLayout';
import { router } from '@/routes/AppRoutes';
import { authState, createTestStore } from '../helpers';
import { server } from '../mocks/server';

function findLayoutRoute(routes: RouteObject[]): RouteObject | null {
  for (const route of routes) {
    if (isValidElement(route.element) && route.element.type === MainLayout) return route;
    const nested = route.children ? findLayoutRoute(route.children) : null;
    if (nested) return nested;
  }
  return null;
}

function Boom(): never {
  throw new Error('page render failure');
}

describe('AppRoutes — page render errors keep the shell (#3014)', () => {
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
      http.get('/api/v1/t/test-tenant/notifications/count', () => HttpResponse.json({ unread_count: 0 })),
    );
    // React reports the thrown render error; it is the point of the test.
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('wraps every layout child in one pathless route that carries an errorElement', () => {
    const layout = findLayoutRoute(router.routes);
    expect(layout).not.toBeNull();
    expect(layout!.errorElement).toBeFalsy();
    expect(layout!.children).toHaveLength(1);
    const boundary = layout!.children![0];
    expect(boundary.path).toBeUndefined();
    expect(boundary.errorElement).toBeTruthy();
    expect(boundary.children?.some((child) => child.path === 'dashboard')).toBe(true);
  });

  it('renders the error inside the layout, with app bar and sidebar toggle still there', async () => {
    const layout = findLayoutRoute(router.routes)!;
    const boundary = layout.children![0];
    const testRouter = createMemoryRouter(
      [
        {
          element: layout.element,
          children: [{ errorElement: boundary.errorElement, children: [{ path: 'boom', element: <Boom /> }] }],
        },
      ],
      { initialEntries: ['/boom'] },
    );
    render(
      <Provider store={createTestStore(authState())}>
        <ThemeContextProvider>
          <SnackbarProvider>
            <RouterProvider router={testRouter} />
          </SnackbarProvider>
        </ThemeContextProvider>
      </Provider>,
    );

    expect(await screen.findByTestId('router-error-page')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Seitenleiste umschalten' })).toBeInTheDocument();
    // The shell owns the one `main` landmark; the embedded error page does not add a second.
    expect(screen.getAllByRole('main')).toHaveLength(1);
  });
});
