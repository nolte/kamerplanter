import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearCurrent,
  clearError,
  fetchOverwinteringProfiles,
  fetchOverwinteringProfile,
  fetchHardinessOverview,
} from '@/store/slices/overwinteringProfilesSlice';
import * as api from '@/api/endpoints/overwinteringProfiles';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/overwinteringProfiles');

function makeStore() {
  return configureStore({ reducer: { overwinteringProfiles: reducer } });
}

const overview = { green: 3, yellow: 2, red: 1, total: 6, red_plants: [] };

describe('overwinteringProfilesSlice', () => {
  it('seeds the extra overview fields in the initial state', () => {
    const state = reducer(undefined, { type: 'unknown' });
    expect(state.items).toEqual([]);
    expect(state.overview).toBeNull();
    expect(state.overviewLoading).toBe(false);
    expect(state.overviewError).toBeNull();
  });

  it('clearCurrent and clearError reset their fields', () => {
    const withCurrent = reducer(
      { ...reducer(undefined, { type: 'x' }), current: { key: 'ow1' } as never, error: 'boom' },
      clearCurrent(),
    );
    expect(withCurrent.current).toBeNull();
    expect(clearError().type).toBe('overwinteringProfiles/clearError');
  });

  it('fetchOverwinteringProfiles.fulfilled stores the list', () => {
    const rows = [{ key: 'ow1' }];
    const state = reducer(undefined, {
      type: fetchOverwinteringProfiles.fulfilled.type,
      payload: rows,
    });
    expect(state.items).toEqual(rows);
    expect(state.loading).toBe(false);
  });

  it('fetchOverwinteringProfile.fulfilled stores the current profile', () => {
    const state = reducer(undefined, {
      type: fetchOverwinteringProfile.fulfilled.type,
      payload: { key: 'ow9' },
    });
    expect(state.current).toEqual({ key: 'ow9' });
  });

  it('fetchHardinessOverview transitions pending → fulfilled', () => {
    const pending = reducer(undefined, { type: fetchHardinessOverview.pending.type });
    expect(pending.overviewLoading).toBe(true);
    const done = reducer(pending, {
      type: fetchHardinessOverview.fulfilled.type,
      payload: overview,
    });
    expect(done.overviewLoading).toBe(false);
    expect(done.overview).toEqual(overview);
  });

  it('fetchHardinessOverview.rejected stores the overview error', () => {
    const state = reducer(undefined, {
      type: fetchHardinessOverview.rejected.type,
      error: { message: 'nope' },
    });
    expect(state.overviewError).toBe('nope');
  });
});

describe('overwinteringProfilesSlice thunks', () => {
  const mocked = vi.mocked(api);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchOverwinteringProfiles forwards paging and stores the rows', async () => {
    mocked.listOverwinteringProfiles.mockResolvedValue([{ key: 'ow1' }] as never);
    const store = makeStore();
    await store.dispatch(fetchOverwinteringProfiles({ offset: 0, limit: 50 }));
    expect(mocked.listOverwinteringProfiles).toHaveBeenCalledWith(0, 50);
    expect(store.getState().overwinteringProfiles.items).toEqual([{ key: 'ow1' }]);
  });

  it('fetchHardinessOverview stores the aggregate counts', async () => {
    mocked.getHardinessOverview.mockResolvedValue(overview as never);
    const store = makeStore();
    await store.dispatch(fetchHardinessOverview());
    expect(mocked.getHardinessOverview).toHaveBeenCalledTimes(1);
    expect(store.getState().overwinteringProfiles.overview).toEqual(overview);
  });
});
