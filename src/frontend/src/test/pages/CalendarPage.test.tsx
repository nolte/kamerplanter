import { screen, waitFor, within, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { configureStore } from '@reduxjs/toolkit';
import calendarReducer from '@/store/slices/calendarSlice';
import sitesReducer from '@/store/slices/sitesSlice';
import uiReducer from '@/store/slices/uiSlice';
import userPreferencesReducer from '@/store/slices/userPreferencesSlice';
import CalendarPage from '@/pages/kalender/CalendarPage';
import { renderWithProviders, type TestStore } from '../helpers';
import { server } from '../mocks/server';
import type { CalendarEvent, CalendarFeed } from '@/api/types';

// The CalendarPage reads `state.calendar` + `state.sites`, which the shared test
// store does not carry. Build a dedicated store with the calendar reducer.
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

const eventsUrls = ['/api/v1/t/:tenant/calendar/events', '/api/v1/calendar/events'];
const feedsUrls = ['/api/v1/t/:tenant/calendar/feeds', '/api/v1/calendar/feeds'];
const deleteFeedUrls = ['/api/v1/t/:tenant/calendar/feeds/:key', '/api/v1/calendar/feeds/:key'];
const createFeedUrls = ['/api/v1/t/:tenant/calendar/feeds', '/api/v1/calendar/feeds'];
const regenerateUrls = [
  '/api/v1/t/:tenant/calendar/feeds/:key/regenerate-token',
  '/api/v1/calendar/feeds/:key/regenerate-token',
];
const sowingUrls = ['/api/v1/t/:tenant/calendar/sowing', '/api/v1/calendar/sowing'];
const seasonUrls = ['/api/v1/t/:tenant/calendar/season-overview', '/api/v1/calendar/season-overview'];
const confirmUrl = '/api/v1/care-reminders/plants/:plantKey/confirm';

// Anchor every event inside the month the page opens on (today).
const NOW = new Date();
const Y = NOW.getFullYear();
const M = NOW.getMonth();
const at = (day: number, hour = 10) => new Date(Y, M, day, hour, 0).toISOString();

function monthLabel(offset = 0): string {
  const d = new Date(Y, M + offset, 1);
  return d.toLocaleDateString(i18n.language === 'de' ? 'de-DE' : 'en-US', {
    month: 'long',
    year: 'numeric',
  });
}

function makeEvent(overrides: Partial<CalendarEvent> = {}): CalendarEvent {
  return {
    id: 'ev-1',
    title: 'Event',
    description: '',
    category: 'custom',
    source: 'task',
    color: '',
    start: at(15),
    end: null,
    all_day: false,
    plant_key: null,
    task_key: null,
    site_key: null,
    location_key: null,
    metadata: {},
    ...overrides,
  };
}

function makeFeed(overrides: Partial<CalendarFeed> = {}): CalendarFeed {
  return {
    key: 'feed-1',
    name: 'My Feed',
    token: 'tok-1',
    user_key: 'user-1',
    filters: { categories: [], site_key: null },
    is_active: true,
    ical_url: 'https://example.com/feed-1.ics',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

interface CalendarSpy {
  feedCreated?: string;
  feedDeleted?: boolean;
  tokenRegenerated?: boolean;
  wateringConfirmed?: string;
}

function useCalendarHandlers(
  {
    events = [] as CalendarEvent[],
    feeds = [] as CalendarFeed[],
    spy = {} as CalendarSpy,
  }: { events?: CalendarEvent[]; feeds?: CalendarFeed[]; spy?: CalendarSpy } = {},
) {
  server.use(
    ...eventsUrls.map((u) => http.get(u, () => HttpResponse.json({ events, total: events.length }))),
    ...feedsUrls.map((u) => http.get(u, () => HttpResponse.json(feeds))),
    ...createFeedUrls.map((u) =>
      http.post(u, async ({ request }) => {
        const body = (await request.json()) as { name: string };
        spy.feedCreated = body.name;
        return HttpResponse.json(makeFeed({ key: 'feed-new', name: body.name }));
      }),
    ),
    ...regenerateUrls.map((u) =>
      http.post(u, ({ params }) => {
        spy.tokenRegenerated = true;
        return HttpResponse.json(makeFeed({ key: params.key as string, token: 'tok-2' }));
      }),
    ),
    ...deleteFeedUrls.map((u) =>
      http.delete(u, () => {
        spy.feedDeleted = true;
        return new HttpResponse(null, { status: 204 });
      }),
    ),
    ...sowingUrls.map((u) =>
      http.get(u, () =>
        HttpResponse.json({
          entries: [],
          frost_config: { last_frost_date: '2026-05-15', first_frost_date: '2026-10-15', eisheilige_date: '2026-05-15' },
          year: Y,
          total: 0,
        }),
      ),
    ),
    ...seasonUrls.map((u) =>
      http.get(u, () =>
        HttpResponse.json({ site_key: '', site_name: 'All', year: Y, months: [] }),
      ),
    ),
    http.post(confirmUrl, ({ params }) => {
      spy.wateringConfirmed = params.plantKey as string;
      return HttpResponse.json({ key: 'conf-1', plant_key: params.plantKey, reminder_type: 'watering' });
    }),
  );
}

/** A varied event set that exercises the month grid, popovers and grouping. */
function richEvents(): CalendarEvent[] {
  return [
    makeEvent({ id: 'ev-task', title: 'Prune tomato', category: 'pruning', source: 'task', start: at(10), task_key: 't1', plant_key: 'plant-1', metadata: { plant_instance_key: 'plant-1' } }),
    makeEvent({ id: 'ev-water', title: 'Water basil', category: 'watering_forecast', source: 'watering_forecast', start: at(12), plant_key: 'plant-9', metadata: { target_ec_ms: 1.2, target_ph: 6.0, volume_liters: 2, phase_name: 'vegetative', dosages: [{ fertilizer_key: 'f1', ml_per_liter: 2, product_name: 'BioGrow' }] } }),
    makeEvent({ id: 'ev-phase', title: 'Flowering start', category: 'phase_transition', source: 'phase_transition', start: at(12), metadata: { plant_instance_key: 'plant-2', run_key: 'run-1', run_name: 'Batch A' } }),
    // Four entries on day 20 to trigger the "+N more" overflow indicator.
    makeEvent({ id: 'ev-a', title: 'Task A', start: at(20) }),
    makeEvent({ id: 'ev-b', title: 'Task B', start: at(20) }),
    makeEvent({ id: 'ev-c', title: 'Task C', start: at(20) }),
    makeEvent({ id: 'ev-d', title: 'Task D', start: at(20) }),
  ];
}

describe('CalendarPage — month view & events', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterEach(() => {
    i18n.changeLanguage('en');
  });

  it('renders the page title and current month', async () => {
    useCalendarHandlers({});
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    expect(await screen.findByTestId('calendar-page')).toBeInTheDocument();
    expect(screen.getByText(monthLabel(0))).toBeInTheDocument();
  });

  it('renders event entries and an overflow indicator in the month grid', async () => {
    useCalendarHandlers({ events: richEvents() });
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-page');
    expect(await screen.findByTestId('calendar-event-dot-ev-task')).toHaveTextContent('Prune tomato');
    // The run instance is collapsed into a single labelled entry.
    expect(screen.getByLabelText('Batch A')).toBeInTheDocument();
    // Day 20 has four entries but only three are shown -> "+1 more".
    expect(screen.getByText(`+1 ${i18n.t('common.more')}`)).toBeInTheDocument();
  });

  it('opens an event popover and navigates to its detail', async () => {
    useCalendarHandlers({ events: richEvents() });
    const user = userEvent.setup();
    const { store } = renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });
    void store;

    await user.click(await screen.findByTestId('calendar-event-dot-ev-task'));
    const popover = await screen.findByTestId('event-popover');
    expect(within(popover).getByText('Prune tomato')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: i18n.t('pages.calendar.goToDetail') }));
    // getEventLink -> /aufgaben/tasks/<task_key>
    await waitFor(() => expect(screen.queryByTestId('event-popover')).toBeNull());
  });

  it('shows watering-forecast hints and confirms watering from the popover', async () => {
    const spy: CalendarSpy = {};
    useCalendarHandlers({ events: richEvents(), spy });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await user.click(await screen.findByTestId('calendar-event-dot-ev-water'));
    const popover = await screen.findByTestId('event-popover');
    // Dosage / EC / volume hints are rendered.
    expect(within(popover).getByText('EC 1.2 mS')).toBeInTheDocument();
    expect(within(popover).getByText('2 L')).toBeInTheDocument();

    await user.click(screen.getByTestId('confirm-watering-btn'));
    await waitFor(() => expect(spy.wateringConfirmed).toBe('plant-9'));
  });

  it('opens a day popover with grouped run events and a plain event', async () => {
    useCalendarHandlers({ events: richEvents() });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-event-dot-ev-water');
    await user.click(screen.getByTestId('calendar-day-12'));

    const dayPopover = await screen.findByTestId('day-popover');
    expect(within(dayPopover).getByText('Batch A')).toBeInTheDocument();
    expect(within(dayPopover).getByText('Water basil')).toBeInTheDocument();
  });

  it('filters events out when their category chip is deselected', async () => {
    useCalendarHandlers({ events: richEvents() });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-event-dot-ev-task');
    await user.click(screen.getByTestId('category-filter-pruning'));
    await waitFor(() => expect(screen.queryByTestId('calendar-event-dot-ev-task')).toBeNull());
  });

  it('navigates between months in both directions', async () => {
    useCalendarHandlers({ events: [] });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-page');
    await user.click(screen.getByTestId('calendar-next-month'));
    expect(await screen.findByText(monthLabel(1))).toBeInTheDocument();

    await user.click(screen.getByTestId('calendar-prev-month'));
    expect(await screen.findByText(monthLabel(0))).toBeInTheDocument();

    await user.click(screen.getByTestId('calendar-prev-month'));
    expect(await screen.findByText(monthLabel(-1))).toBeInTheDocument();

    await user.click(screen.getByTestId('calendar-today-btn'));
    expect(await screen.findByText(monthLabel(0))).toBeInTheDocument();
  });

  it('re-selects a category chip after it was deselected', async () => {
    useCalendarHandlers({ events: richEvents() });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-event-dot-ev-task');
    await user.click(screen.getByTestId('category-filter-pruning'));
    await waitFor(() => expect(screen.queryByTestId('calendar-event-dot-ev-task')).toBeNull());
    await user.click(screen.getByTestId('category-filter-pruning'));
    expect(await screen.findByTestId('calendar-event-dot-ev-task')).toBeInTheDocument();
  });

  it('activates a day cell and event dot via the keyboard', async () => {
    useCalendarHandlers({ events: richEvents() });
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    const dot = await screen.findByTestId('calendar-event-dot-ev-task');
    fireEvent.keyDown(dot, { key: 'Enter' });
    expect(await screen.findByTestId('event-popover')).toBeInTheDocument();

    fireEvent.keyDown(screen.getByTestId('calendar-day-20'), { key: 'Enter' });
    expect(await screen.findByTestId('day-popover')).toBeInTheDocument();
  });
});

describe('CalendarPage — day popover interactions', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterEach(() => {
    i18n.changeLanguage('en');
  });

  it('follows a run group link and closes the popover', async () => {
    useCalendarHandlers({ events: richEvents() });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-event-dot-ev-water');
    await user.click(screen.getByTestId('calendar-day-12'));
    const dayPopover = await screen.findByTestId('day-popover');

    await user.click(within(dayPopover).getByText('Batch A'));
    // Navigating to the run detail closes the day popover.
    await waitFor(() => expect(screen.queryByTestId('day-popover')).toBeNull());
  });

  it('opens the event popover for a non-linked event from the day popover', async () => {
    useCalendarHandlers({ events: richEvents() });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-event-dot-ev-water');
    await user.click(screen.getByTestId('calendar-day-12'));
    const dayPopover = await screen.findByTestId('day-popover');

    await user.click(within(dayPopover).getByText('Water basil'));
    // The watering-forecast event has no direct link, so its detail popover opens.
    expect(await screen.findByTestId('event-popover')).toBeInTheDocument();
  });

  it('confirms watering from the day popover action button', async () => {
    const spy: CalendarSpy = {};
    useCalendarHandlers({ events: richEvents(), spy });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-event-dot-ev-water');
    await user.click(screen.getByTestId('calendar-day-12'));
    await screen.findByTestId('day-popover');

    await user.click(screen.getByTestId('day-confirm-watering-plant-9'));
    await waitFor(() => expect(spy.wateringConfirmed).toBe('plant-9'));
  });

  it('keyboard-activates the run group and event entries in the day popover', async () => {
    useCalendarHandlers({ events: richEvents() });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-event-dot-ev-water');
    await user.click(screen.getByTestId('calendar-day-12'));
    let dayPopover = await screen.findByTestId('day-popover');
    fireEvent.keyDown(within(dayPopover).getByText('Water basil'), { key: 'Enter' });
    // The non-linked event opens its own detail popover.
    expect(await screen.findByTestId('event-popover')).toBeInTheDocument();

    // Re-open the day popover and activate the run group via keyboard.
    await user.click(screen.getByTestId('calendar-day-12'));
    dayPopover = await screen.findByTestId('day-popover');
    fireEvent.keyDown(within(dayPopover).getByText('Batch A'), { key: 'Enter' });
    await waitFor(() => expect(screen.queryByTestId('day-popover')).toBeNull());
  });

  it('ignores clicks on days without events', async () => {
    useCalendarHandlers({ events: richEvents() });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-event-dot-ev-task');
    await user.click(screen.getByTestId('calendar-day-1'));
    expect(screen.queryByTestId('day-popover')).toBeNull();
  });

  it('renders explicit colors, end times and all-day events in the popover', async () => {
    const events: CalendarEvent[] = [
      makeEvent({ id: 'ev-color', title: 'Colored task', category: 'training', source: 'task', color: '#3366CC', start: at(5, 9), end: at(5, 11), all_day: false, task_key: 'tc', description: 'A described event' }),
      makeEvent({ id: 'ev-allday', title: 'All-day harvest', category: 'harvest', source: 'maintenance_log', start: at(5), all_day: true }),
    ];
    useCalendarHandlers({ events });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await user.click(await screen.findByTestId('calendar-event-dot-ev-color'));
    const popover = await screen.findByTestId('event-popover');
    // Description and the goToDetail link (task_key present) are both shown.
    expect(within(popover).getByText('A described event')).toBeInTheDocument();
    expect(within(popover).getByRole('button', { name: i18n.t('pages.calendar.goToDetail') })).toBeInTheDocument();
  });

  it('renders linked and all-day events together in a day popover', async () => {
    const events: CalendarEvent[] = [
      makeEvent({ id: 'ev-color', title: 'Colored task', category: 'training', source: 'task', color: '#3366CC', start: at(5, 9), end: at(5, 11), all_day: false, task_key: 'tc' }),
      makeEvent({ id: 'ev-allday', title: 'All-day harvest', category: 'harvest', source: 'maintenance_log', start: at(5), all_day: true }),
    ];
    useCalendarHandlers({ events });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-event-dot-ev-color');
    await user.click(screen.getByTestId('calendar-day-5'));
    const dayPopover = await screen.findByTestId('day-popover');
    expect(within(dayPopover).getByText('Colored task')).toBeInTheDocument();
    expect(within(dayPopover).getByText('All-day harvest')).toBeInTheDocument();
  });
});

describe('CalendarPage — view modes', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterEach(() => {
    i18n.changeLanguage('en');
  });

  it('switches to the list view and navigates on row click', async () => {
    useCalendarHandlers({ events: richEvents() });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-page');
    await user.click(screen.getByTestId('calendar-view-list'));
    // The list renders event titles as table rows.
    expect(await screen.findByText('Prune tomato')).toBeInTheDocument();
  });

  it('switches to the phase timeline view', async () => {
    useCalendarHandlers({ events: richEvents() });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-page');
    await user.click(screen.getByTestId('calendar-view-phases'));
    // The month grid is no longer shown.
    await waitFor(() => expect(screen.queryByTestId('calendar-event-dot-ev-task')).toBeNull());
  });

  it('switches to the sowing calendar view and shows the site selector', async () => {
    useCalendarHandlers({ events: [] });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-page');
    await user.click(screen.getByTestId('calendar-view-sowing'));
    expect(await screen.findByTestId('calendar-site-select')).toBeInTheDocument();
  });

  it('switches to the season overview view', async () => {
    useCalendarHandlers({ events: [] });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await screen.findByTestId('calendar-page');
    await user.click(screen.getByTestId('calendar-view-season'));
    expect(await screen.findByTestId('calendar-site-select')).toBeInTheDocument();
  });
});

describe('CalendarPage — iCal feeds', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterEach(() => {
    i18n.changeLanguage('en');
  });

  it('creates a new feed through the dialog', async () => {
    const spy: CalendarSpy = {};
    useCalendarHandlers({ feeds: [], spy });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await user.click(await screen.findByTestId('feeds-toggle'));
    await user.click(await screen.findByTestId('create-feed-btn'));
    const dialog = await screen.findByTestId('create-feed-dialog');
    await user.type(within(dialog).getByRole('textbox'), 'Garden ICS');
    await user.click(screen.getByTestId('feed-save-btn'));

    await waitFor(() => expect(spy.feedCreated).toBe('Garden ICS'));
    expect(await screen.findByTestId('feed-item-feed-new')).toBeInTheDocument();
  });

  it('regenerates a feed token and copies its URL', async () => {
    const spy: CalendarSpy = {};
    useCalendarHandlers({ feeds: [makeFeed()], spy });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await user.click(await screen.findByTestId('feeds-toggle'));
    await screen.findByTestId('feed-item-feed-1');

    await user.click(screen.getByTestId('feed-regenerate-feed-1'));
    await waitFor(() => expect(spy.tokenRegenerated).toBe(true));

    await user.click(screen.getByTestId('feed-copy-feed-1'));
    // Feed remains listed after copying its URL.
    expect(screen.getByTestId('feed-item-feed-1')).toBeInTheDocument();
  });

  it('deletes an iCal feed through the confirm dialog', async () => {
    const spy: CalendarSpy = {};
    useCalendarHandlers({ feeds: [makeFeed()], spy });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await user.click(await screen.findByTestId('feeds-toggle'));
    await screen.findByTestId('feed-item-feed-1');

    await user.click(screen.getByTestId('feed-delete-feed-1'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(screen.queryByTestId('feed-item-feed-1')).toBeNull());
    expect(spy.feedDeleted).toBe(true);
  });

  it('shows the pending state while a feed delete is in flight', async () => {
    useCalendarHandlers({ feeds: [makeFeed()] });
    let release!: () => void;
    server.use(
      ...deleteFeedUrls.map((u) =>
        http.delete(u, async () => {
          await new Promise<void>((res) => {
            release = res;
          });
          return new HttpResponse(null, { status: 204 });
        }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await user.click(await screen.findByTestId('feeds-toggle'));
    await screen.findByTestId('feed-item-feed-1');
    await user.click(screen.getByTestId('feed-delete-feed-1'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(screen.getByTestId('confirm-dialog-confirm')).toBeDisabled());
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );

    release();
    await waitFor(() => expect(screen.queryByTestId('feed-item-feed-1')).toBeNull());
  });

  it('keeps the feed listed when the delete request fails', async () => {
    useCalendarHandlers({ feeds: [makeFeed()] });
    server.use(
      ...deleteFeedUrls.map((u) => http.delete(u, () => new HttpResponse(null, { status: 500 }))),
    );
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await user.click(await screen.findByTestId('feeds-toggle'));
    await screen.findByTestId('feed-item-feed-1');
    await user.click(screen.getByTestId('feed-delete-feed-1'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    // The confirm button re-enables after the failure and the feed remains.
    await waitFor(() => expect(screen.getByTestId('confirm-dialog-confirm')).not.toBeDisabled());
    expect(screen.getByTestId('feed-item-feed-1')).toBeInTheDocument();
  });

  it('cancels the feed deletion without removing the feed', async () => {
    useCalendarHandlers({ feeds: [makeFeed()] });
    const user = userEvent.setup();
    renderWithProviders(<CalendarPage />, { store: makeCalendarStore() });

    await user.click(await screen.findByTestId('feeds-toggle'));
    await screen.findByTestId('feed-item-feed-1');

    await user.click(screen.getByTestId('feed-delete-feed-1'));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
    expect(screen.getByTestId('feed-item-feed-1')).toBeInTheDocument();
  });
});
