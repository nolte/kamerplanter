import { describe, it, expect } from 'vitest';
import reducer, {
  clearCurrentLog,
  clearError,
  fetchWateringLogs,
  fetchWateringLog,
} from '@/store/slices/wateringLogsSlice';

const baseState = { logs: [], currentLog: null, loading: false, error: null };

describe('wateringLogsSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrentLog resets the selection', () => {
    const state = reducer({ ...baseState, currentLog: { key: 'l1' } as never }, clearCurrentLog());
    expect(state.currentLog).toBeNull();
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('fetchWateringLogs.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: fetchWateringLogs.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchWateringLogs.fulfilled stores the logs', () => {
    const logs = [{ key: 'l1' }];
    const state = reducer(undefined, { type: fetchWateringLogs.fulfilled.type, payload: logs });
    expect(state.logs).toEqual(logs);
    expect(state.loading).toBe(false);
  });

  it('fetchWateringLogs.rejected stores the error', () => {
    const state = reducer(undefined, { type: fetchWateringLogs.rejected.type, error: { message: 'fail' } });
    expect(state.error).toBe('fail');
  });

  it('fetchWateringLogs.rejected falls back to a default message', () => {
    const state = reducer(undefined, { type: fetchWateringLogs.rejected.type, error: {} });
    expect(state.error).toBe('Failed to load watering logs');
  });

  it('fetchWateringLog.fulfilled stores the selected log', () => {
    const log = { key: 'l1' };
    const state = reducer(undefined, { type: fetchWateringLog.fulfilled.type, payload: log });
    expect(state.currentLog).toEqual(log);
  });
});
