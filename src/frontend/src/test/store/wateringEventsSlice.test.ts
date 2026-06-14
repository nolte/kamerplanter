import { describe, it, expect } from 'vitest';
import reducer, {
  clearError,
  fetchWateringEvents,
  fetchLocationWateringEvents,
  fetchLocationWateringStats,
} from '@/store/slices/wateringEventsSlice';

const baseState = { events: [], stats: null, loading: false, error: null };

describe('wateringEventsSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchWateringEvents handles pending, fulfilled and rejected', () => {
    expect(reducer(baseState, { type: fetchWateringEvents.pending.type }).loading).toBe(true);
    const fulfilled = reducer(baseState, { type: fetchWateringEvents.fulfilled.type, payload: [{ key: 'w1' }] });
    expect(fulfilled.events).toEqual([{ key: 'w1' }]);
    expect(fulfilled.loading).toBe(false);
    const rejected = reducer(baseState, { type: fetchWateringEvents.rejected.type, error: {} });
    expect(rejected.error).toBe('Failed to load watering events');
  });

  it('fetchLocationWateringEvents.fulfilled stores events', () => {
    const state = reducer(baseState, { type: fetchLocationWateringEvents.fulfilled.type, payload: [{ key: 'w2' }] });
    expect(state.events).toEqual([{ key: 'w2' }]);
  });

  it('fetchLocationWateringStats.fulfilled stores stats', () => {
    const state = reducer(baseState, { type: fetchLocationWateringStats.fulfilled.type, payload: { total: 5 } });
    expect(state.stats).toEqual({ total: 5 });
  });
});
