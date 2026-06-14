import { describe, it, expect } from 'vitest';
import reducer, {
  clearCurrentEvent,
  clearError,
  fetchFeedingEvents,
  fetchFeedingEvent,
} from '@/store/slices/feedingEventsSlice';

const baseState = { events: [], currentEvent: null, loading: false, error: null };

describe('feedingEventsSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrentEvent resets the selection', () => {
    const state = reducer({ ...baseState, currentEvent: { key: 'e1' } as never }, clearCurrentEvent());
    expect(state.currentEvent).toBeNull();
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchFeedingEvents.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: fetchFeedingEvents.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchFeedingEvents.fulfilled stores the events', () => {
    const events = [{ key: 'e1' }];
    const state = reducer(undefined, { type: fetchFeedingEvents.fulfilled.type, payload: events });
    expect(state.events).toEqual(events);
    expect(state.loading).toBe(false);
  });

  it('fetchFeedingEvents.rejected stores the error', () => {
    const state = reducer(undefined, { type: fetchFeedingEvents.rejected.type, error: { message: 'fail' } });
    expect(state.error).toBe('fail');
  });

  it('fetchFeedingEvents.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchFeedingEvents.rejected.type, error: {} });
    expect(state.error).toBe('Failed to load feeding events');
  });

  it('fetchFeedingEvent.fulfilled stores the selected event', () => {
    const event = { key: 'e1' };
    const state = reducer(undefined, { type: fetchFeedingEvent.fulfilled.type, payload: event });
    expect(state.currentEvent).toEqual(event);
  });
});
