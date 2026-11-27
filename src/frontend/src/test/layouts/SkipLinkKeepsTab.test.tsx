import { isValidElement } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider, type RouteObject } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { ThemeContextProvider } from '@/theme';
import MainLayout from '@/layouts/MainLayout';
import CalendarPage from '@/pages/kalender/CalendarPage';
import { router as appRouter } from '@/routes/AppRoutes';
import { configureStore } from '@reduxjs/toolkit';
import { rootReducer } from '@/store/rootReducer';
import { authState, tenantState } from '../helpers';
import { server } from '../mocks/server';

/**
 * #3018 — "Zum Inhalt springen" must not change the URL fragment. The tabbed pages keep their tab there
 * (`useTabUrl`); following the link's `#main-content` replaced `/kalender#list` with an unknown fragment, so
 * the calendar fell back to the month view, and it added a history entry. The link now moves the focus to
 * the main landmark itself. Rendered with the shell from the app's route table and the real calendar page.
 */

function layoutElement(routes: RouteObject[]): RouteObject['element'] {
  for (const route of routes) {
    if (isValidElement(route.element) && route.element.type === MainLayout) return route.element;
    const nested = route.children ? layoutElement(route.children) : null;
    if (nested) return nested;
  }
  return null;
}

function selectedView(): string | null {
  const tab = screen.getAllByRole('tab').find((el) => el.getAttribute('aria-selected') === 'true');
  return tab?.getAttribute('data-testid') ?? null;
}

describe('SkipLink keeps the page tab in the URL (#3018)', () => {
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
      http.get('/api/v1/t/:tenant/calendar/events', () => HttpResponse.json({ events: [], total: 0 })),
      http.get('/api/v1/t/:tenant/calendar/feeds', () => HttpResponse.json([])),
    );
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('focuses main and leaves /kalender#list, its view and the history as they were', async () => {
    const user = userEvent.setup();
    const router = createMemoryRouter(
      [{ element: layoutElement(appRouter.routes), children: [{ path: '/kalender', element: <CalendarPage /> }] }],
      { initialEntries: ['/kalender#list'] },
    );
    render(
      <Provider
        store={configureStore({ reducer: rootReducer, preloadedState: { ...tenantState('lead'), ...authState() } as never })}
      >
        <ThemeContextProvider>
          <SnackbarProvider>
            <RouterProvider router={router} />
          </SnackbarProvider>
        </ThemeContextProvider>
      </Provider>,
    );
    await waitFor(() => expect(selectedView()).toBe('calendar-view-list'));
    const before = router.state.location;

    const skip = screen.getByRole('link', { name: 'Zum Inhalt springen' });
    expect(skip).toHaveAttribute('href', '#main-content');
    skip.focus();
    await user.keyboard('{Enter}');

    expect(screen.getByRole('main')).toHaveFocus();
    expect(router.state.location).toBe(before);
    expect(router.state.location.hash).toBe('#list');
    expect(selectedView()).toBe('calendar-view-list');

    // jsdom does not follow an in-page `href` into the memory router, so the fragment reset itself is a browser
    // effect; what prevents it is that the click's default navigation is cancelled.
    expect(fireEvent.click(skip)).toBe(false);
    expect(screen.getByRole('main')).toHaveFocus();
  });
});
