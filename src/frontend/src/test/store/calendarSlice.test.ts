import { describe, it, expect } from 'vitest';
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
