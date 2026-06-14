import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearError,
  fetchCalendarEvents,
  fetchCalendarFeeds,
  createCalendarFeed,
  deleteCalendarFeed,
  regenerateCalendarFeedToken,
  fetchSowingCalendar,
  fetchSeasonOverview,
} from '@/store/slices/calendarSlice';
import * as calendarApi from '@/api/endpoints/calendar';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/calendar');

function makeStore() {
  return configureStore({ reducer: { calendar: reducer } });
}

function initial() {
  return reducer(undefined, { type: 'unknown' });
}

describe('calendarSlice', () => {
  it('has sensible initial state', () => {
    const state = initial();
    expect(state.events).toEqual([]);
    expect(state.feeds).toEqual([]);
    expect(state.sowingEntries).toEqual([]);
    expect(state.seasonOverview).toBeNull();
    expect(state.sowingYear).toBe(new Date().getFullYear());
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...initial(), error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchCalendarEvents handles pending, fulfilled and rejected', () => {
    expect(reducer(initial(), { type: fetchCalendarEvents.pending.type }).loading).toBe(true);
    const fulfilled = reducer(initial(), {
      type: fetchCalendarEvents.fulfilled.type,
      payload: { events: [{ key: 'ev1' }] },
    });
    expect(fulfilled.events).toEqual([{ key: 'ev1' }]);
    const rejected = reducer(initial(), { type: fetchCalendarEvents.rejected.type, error: {} });
    expect(rejected.error).toBe('Failed to load calendar events');
  });

  it('fetchCalendarFeeds stores feeds and toggles feedsLoading', () => {
    expect(reducer(initial(), { type: fetchCalendarFeeds.pending.type }).feedsLoading).toBe(true);
    const fulfilled = reducer(initial(), {
      type: fetchCalendarFeeds.fulfilled.type,
      payload: [{ key: 'feed1' }],
    });
    expect(fulfilled.feeds).toEqual([{ key: 'feed1' }]);
    expect(fulfilled.feedsLoading).toBe(false);
    const rejected = reducer(initial(), { type: fetchCalendarFeeds.rejected.type, error: {} });
    expect(rejected.error).toBe('Failed to load feeds');
  });

  it('createCalendarFeed.fulfilled appends the new feed', () => {
    const start = { ...initial(), feeds: [{ key: 'feed1' }] as never };
    const state = reducer(start, { type: createCalendarFeed.fulfilled.type, payload: { key: 'feed2' } });
    expect(state.feeds.map((f) => f.key)).toEqual(['feed1', 'feed2']);
  });

  it('deleteCalendarFeed.fulfilled removes the feed by key', () => {
    const start = { ...initial(), feeds: [{ key: 'feed1' }, { key: 'feed2' }] as never };
    const state = reducer(start, { type: deleteCalendarFeed.fulfilled.type, payload: 'feed1' });
    expect(state.feeds.map((f) => f.key)).toEqual(['feed2']);
  });

  it('regenerateCalendarFeedToken.fulfilled replaces the matching feed', () => {
    const start = { ...initial(), feeds: [{ key: 'feed1', token: 'old' }] as never };
    const state = reducer(start, {
      type: regenerateCalendarFeedToken.fulfilled.type,
      payload: { key: 'feed1', token: 'new' },
    });
    expect(state.feeds[0]).toEqual({ key: 'feed1', token: 'new' });
  });

  it('fetchSowingCalendar stores entries, frost config and year', () => {
    expect(reducer(initial(), { type: fetchSowingCalendar.pending.type }).sowingLoading).toBe(true);
    const fulfilled = reducer(initial(), {
      type: fetchSowingCalendar.fulfilled.type,
      payload: { entries: [{ key: 's1' }], frost_config: { last: '05-15' }, year: 2026 },
    });
    expect(fulfilled.sowingEntries).toEqual([{ key: 's1' }]);
    expect(fulfilled.sowingFrostConfig).toEqual({ last: '05-15' });
    expect(fulfilled.sowingYear).toBe(2026);
    const rejected = reducer(initial(), { type: fetchSowingCalendar.rejected.type, error: {} });
    expect(rejected.error).toBe('Failed to load sowing calendar');
  });

  it('fetchSeasonOverview stores the overview', () => {
    expect(reducer(initial(), { type: fetchSeasonOverview.pending.type }).seasonLoading).toBe(true);
    const fulfilled = reducer(initial(), {
      type: fetchSeasonOverview.fulfilled.type,
      payload: { months: [] },
    });
    expect(fulfilled.seasonOverview).toEqual({ months: [] });
    const rejected = reducer(initial(), { type: fetchSeasonOverview.rejected.type, error: {} });
    expect(rejected.error).toBe('Failed to load season overview');
  });
});

describe('calendarSlice thunks', () => {
  const mocked = vi.mocked(calendarApi);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchCalendarEvents forwards its args and stores the events', async () => {
    mocked.getCalendarEvents.mockResolvedValue({ events: [{ key: 'e1' }] } as never);
    const store = makeStore();
    await store.dispatch(
      fetchCalendarEvents({ start: '2026-01-01', end: '2026-01-31', category: 'task', tenantKey: 't1' }),
    );
    expect(mocked.getCalendarEvents).toHaveBeenCalledWith('2026-01-01', '2026-01-31', 'task', 't1');
    expect(store.getState().calendar.events).toEqual([{ key: 'e1' }]);
  });

  it('fetchCalendarFeeds stores the feeds', async () => {
    mocked.listCalendarFeeds.mockResolvedValue([{ key: 'f1' }] as never);
    const store = makeStore();
    await store.dispatch(fetchCalendarFeeds({ userKey: 'u1', tenantKey: 't1' }));
    expect(mocked.listCalendarFeeds).toHaveBeenCalledWith('u1', 't1');
    expect(store.getState().calendar.feeds).toEqual([{ key: 'f1' }]);
  });

  it('createCalendarFeed appends the new feed', async () => {
    mocked.createCalendarFeed.mockResolvedValue({ key: 'f2' } as never);
    const store = makeStore();
    const filters = { categories: ['task'], site_key: null };
    await store.dispatch(createCalendarFeed({ name: 'My Feed', filters }));
    expect(mocked.createCalendarFeed).toHaveBeenCalledWith('My Feed', filters);
    expect(store.getState().calendar.feeds).toContainEqual({ key: 'f2' });
  });

  it('deleteCalendarFeed removes the feed by key', async () => {
    mocked.deleteCalendarFeed.mockResolvedValue(undefined);
    const store = configureStore({
      reducer: { calendar: reducer },
      preloadedState: {
        calendar: { ...reducer(undefined, { type: 'unknown' }), feeds: [{ key: 'f1' }] as never },
      },
    });
    await store.dispatch(deleteCalendarFeed('f1'));
    expect(mocked.deleteCalendarFeed).toHaveBeenCalledWith('f1');
    expect(store.getState().calendar.feeds).toEqual([]);
  });

  it('regenerateCalendarFeedToken replaces the matching feed', async () => {
    mocked.regenerateCalendarFeedToken.mockResolvedValue({ key: 'f1', token: 'new' } as never);
    const store = configureStore({
      reducer: { calendar: reducer },
      preloadedState: {
        calendar: { ...reducer(undefined, { type: 'unknown' }), feeds: [{ key: 'f1', token: 'old' }] as never },
      },
    });
    await store.dispatch(regenerateCalendarFeedToken('f1'));
    expect(store.getState().calendar.feeds[0]).toEqual({ key: 'f1', token: 'new' });
  });

  it('fetchSowingCalendar stores entries, frost config and year', async () => {
    mocked.getSowingCalendar.mockResolvedValue({
      entries: [{ species_key: 's1' }],
      frost_config: { last_frost: '2026-05-15' },
      year: 2026,
    } as never);
    const store = makeStore();
    await store.dispatch(fetchSowingCalendar({ siteId: 'site-1', year: 2026 }));
    expect(mocked.getSowingCalendar).toHaveBeenCalledWith('site-1', 2026);
    expect(store.getState().calendar.sowingYear).toBe(2026);
    expect(store.getState().calendar.sowingFrostConfig).toEqual({ last_frost: '2026-05-15' });
  });

  it('fetchSeasonOverview stores the overview', async () => {
    mocked.getSeasonOverview.mockResolvedValue({ months: [{ month: 1 }] } as never);
    const store = makeStore();
    await store.dispatch(fetchSeasonOverview({ siteId: 'site-1', year: 2026 }));
    expect(mocked.getSeasonOverview).toHaveBeenCalledWith('site-1', 2026);
    expect(store.getState().calendar.seasonOverview).toEqual({ months: [{ month: 1 }] });
  });

  it('fetchCalendarEvents surfaces a rejection as the slice error', async () => {
    mocked.getCalendarEvents.mockRejectedValue(new Error('load failed'));
    const store = makeStore();
    await store.dispatch(fetchCalendarEvents({ start: '2026-01-01', end: '2026-01-31' }));
    expect(store.getState().calendar.error).toBe('load failed');
  });
});
