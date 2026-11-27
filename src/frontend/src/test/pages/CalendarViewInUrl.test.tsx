import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { combineReducers, configureStore } from '@reduxjs/toolkit';
import calendarReducer from '@/store/slices/calendarSlice';
import sitesReducer from '@/store/slices/sitesSlice';
import uiReducer from '@/store/slices/uiSlice';
import userPreferencesReducer from '@/store/slices/userPreferencesSlice';
import tenantsReducer from '@/store/slices/tenantSlice';
import { ThemeContextProvider } from '@/theme';
import CalendarPage from '@/pages/kalender/CalendarPage';
import { tenantState } from '../helpers';
import { server } from '../mocks/server';

/**
 * #3018 (audit N-19, UI-NFR-005 R-001) — the calendar's view is part of its URL.
 *
 * The view lived in component state only: a reload, a shared link and the way back from an event's
 * detail page all reopened the month view. It now follows the app's tab pattern (`useTabUrl`, the URL
 * fragment): `/kalender#list`. The first view carries no fragment, so the old `/kalender` still opens
 * the month view.
 */

function makeCalendarStore() {
  return configureStore({
    reducer: combineReducers({
      calendar: calendarReducer,
      sites: sitesReducer,
      ui: uiReducer,
      userPreferences: userPreferencesReducer,
      tenants: tenantsReducer,
    }),
    preloadedState: tenantState('lead') as never,
  });
}

function renderCalendarAt(entry: string) {
  const router = createMemoryRouter(
    [
      { path: '/kalender', element: <CalendarPage /> },
      { path: '/elsewhere', element: <p>elsewhere</p> },
    ],
    { initialEntries: [entry] },
  );
  render(
    <Provider store={makeCalendarStore()}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
  return router;
}

function selectedView(): string | null {
  const tab = screen.getAllByRole('tab').find((el) => el.getAttribute('aria-selected') === 'true');
  return tab?.getAttribute('data-testid') ?? null;
}

describe('CalendarPage — the view is restored from the URL (#3018 N-19)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    server.use(
      http.get('/api/v1/t/:tenant/calendar/events', () => HttpResponse.json({ events: [], total: 0 })),
      http.get('/api/v1/t/:tenant/calendar/feeds', () => HttpResponse.json([])),
      http.get('/api/v1/t/:tenant/calendar/season-overview', () =>
        HttpResponse.json({ site_key: '', site_name: 'All', year: 2026, months: [] }),
      ),
    );
  });
  afterEach(() => {
    cleanup();
  });

  it('opens the view the fragment names, as a reload or a bookmark does', async () => {
    renderCalendarAt('/kalender#list');
    await waitFor(() => expect(selectedView()).toBe('calendar-view-list'));
  });

  it('opens the month view on the old URL without a fragment, and on an unknown one', async () => {
    renderCalendarAt('/kalender');
    await waitFor(() => expect(selectedView()).toBe('calendar-view-month'));
    cleanup();
    renderCalendarAt('/kalender#no-such-view');
    await waitFor(() => expect(selectedView()).toBe('calendar-view-month'));
  });

  it('writes the chosen view into the URL and restores it on Back and Forward', async () => {
    const user = userEvent.setup();
    const router = renderCalendarAt('/kalender');
    await user.click(await screen.findByTestId('calendar-view-season'));
    expect(router.state.location.hash).toBe('#season');
    expect(selectedView()).toBe('calendar-view-season');

    await act(() => router.navigate('/elsewhere'));
    expect(screen.getByText('elsewhere')).toBeInTheDocument();

    await act(() => router.navigate(-1));
    expect(router.state.location.pathname).toBe('/kalender');
    expect(router.state.location.hash).toBe('#season');
    await waitFor(() => expect(selectedView()).toBe('calendar-view-season'));

    await act(() => router.navigate(1));
    expect(screen.getByText('elsewhere')).toBeInTheDocument();
    await act(() => router.navigate(-1));
    await waitFor(() => expect(selectedView()).toBe('calendar-view-season'));
  });

  it('drops the fragment again for the month view', async () => {
    const user = userEvent.setup();
    const router = renderCalendarAt('/kalender#phases');
    await user.click(await screen.findByTestId('calendar-view-month'));
    expect(router.state.location.hash).toBe('');
    expect(selectedView()).toBe('calendar-view-month');
  });
});
