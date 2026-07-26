import { cleanup, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { configureStore } from '@reduxjs/toolkit';
import calendarReducer from '@/store/slices/calendarSlice';
import sitesReducer from '@/store/slices/sitesSlice';
import uiReducer from '@/store/slices/uiSlice';
import userPreferencesReducer from '@/store/slices/userPreferencesSlice';
import { renderWithProviders, type TestStore } from '../helpers';
import { server } from '../mocks/server';

// Force the mobile branch: the category-filter disclosure only renders below
// the `sm` breakpoint.
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => true }));

// Import after the mock so the mocked useMediaQuery is picked up.
import CalendarPage from '@/pages/kalender/CalendarPage';

function makeCalendarStore(): TestStore {
  return configureStore({
    reducer: {
      calendar: calendarReducer,
      sites: sitesReducer,
      ui: uiReducer,
      userPreferences: userPreferencesReducer,
    },
  }) as unknown as TestStore;
}

function seedEmptyCalendar() {
  server.use(
    ...['/api/v1/t/:tenant/calendar/events', '/api/v1/calendar/events'].map((u) =>
      http.get(u, () => HttpResponse.json({ events: [], total: 0 })),
    ),
    ...['/api/v1/t/:tenant/calendar/feeds', '/api/v1/calendar/feeds'].map((u) =>
      http.get(u, () => HttpResponse.json([])),
    ),
  );
}

describe('CalendarPage — mobile category filter disclosure', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it('exposes the category disclosure under a stable hook', async () => {
    seedEmptyCalendar();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-page');
    // The disclosure had no hook at all, so a page object had to anchor on the
    // Collapse wrapping the `category-filter-*` chips, or on the translated
    // "Kategorien (n/m)" label.
    const toggle = screen.getByTestId('calendar-category-filter-toggle');
    expect(toggle.tagName).toBe('BUTTON');
    expect(toggle.textContent).toContain(i18n.t('pages.calendar.categories'));
  });

  it('expands the category chips through the hook', async () => {
    seedEmptyCalendar();
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-page');
    const collapse = screen
      .getByTestId('category-filter-pruning')
      .closest('.MuiCollapse-root') as HTMLElement;

    // Collapsed at mobile width until the disclosure is used. (Only the entry
    // transition is asserted: the exit transition never completes in jsdom,
    // which has no transitionend.)
    expect(collapse.className).toContain('MuiCollapse-hidden');
    await user.click(screen.getByTestId('calendar-category-filter-toggle'));
    expect(collapse.className).not.toContain('MuiCollapse-hidden');
  });
});
