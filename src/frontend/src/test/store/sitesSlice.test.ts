import { describe, it, expect } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  fetchSites,
  fetchSite,
  fetchLocations,
  fetchLocation,
  fetchSlots,
  clearCurrent,
  clearError,
} from '@/store/slices/sitesSlice';

function createStore() {
  return configureStore({ reducer: { sites: reducer } });
}

describe('sitesSlice', () => {
  it('has correct initial state', () => {
    const state = reducer(undefined, { type: 'unknown' });
    expect(state.sites).toEqual([]);
    expect(state.currentSite).toBeNull();
    expect(state.locations).toEqual([]);
    expect(state.currentLocation).toBeNull();
    expect(state.slots).toEqual([]);
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('clearCurrent resets both site and location', () => {
    const state = reducer(
      {
        sites: [], currentSite: { key: 'x' } as never,
        locations: [], currentLocation: { key: 'y' } as never,
        slots: [], loading: false, error: null,
      },
      clearCurrent(),
    );
    expect(state.currentSite).toBeNull();
    expect(state.currentLocation).toBeNull();
  });

  it('clearError resets error', () => {
    const state = reducer(
      { sites: [], currentSite: null, locations: [], currentLocation: null, slots: [], loading: false, error: 'err' },
      clearError(),
    );
    expect(state.error).toBeNull();
  });

  it('fetchSites.pending sets loading', () => {
    const state = reducer(undefined, { type: fetchSites.pending.type });
    expect(state.loading).toBe(true);
  });

  it('fetchSites.fulfilled sets sites', () => {
    const sites = [{ key: 's1', name: 'Main' }];
    const state = reducer(undefined, {
      type: fetchSites.fulfilled.type,
      payload: sites,
    });
    expect(state.sites).toEqual(sites);
    expect(state.loading).toBe(false);
  });

  it('fetchSites.rejected sets error', () => {
    const state = reducer(undefined, {
      type: fetchSites.rejected.type,
      error: { message: 'Fail' },
    });
    expect(state.error).toBe('Fail');
  });

  it('fetchSite.fulfilled sets currentSite', () => {
    const site = { key: 's1', name: 'Main' };
    const state = reducer(undefined, {
      type: fetchSite.fulfilled.type,
      payload: site,
    });
    expect(state.currentSite).toEqual(site);
  });

  it('fetchLocations.fulfilled sets locations', () => {
    const locs = [{ key: 'l1', name: 'Zone A' }];
    const state = reducer(undefined, {
      type: fetchLocations.fulfilled.type,
      payload: locs,
    });
    expect(state.locations).toEqual(locs);
  });

  it('fetchLocation.fulfilled sets currentLocation', () => {
    const loc = { key: 'l1', name: 'Zone A' };
    const state = reducer(undefined, {
      type: fetchLocation.fulfilled.type,
      payload: loc,
    });
    expect(state.currentLocation).toEqual(loc);
  });

  it('fetchSlots.fulfilled sets slots', () => {
    const slots = [{ key: 'sl1', slot_id: 'A1' }];
    const state = reducer(undefined, {
      type: fetchSlots.fulfilled.type,
      payload: slots,
    });
    expect(state.slots).toEqual(slots);
  });

  it('fetches sites via thunk with MSW', async () => {
    const store = createStore();
    await store.dispatch(fetchSites({}));
    const state = store.getState().sites;
    expect(state.sites.length).toBe(1);
    expect(state.sites[0].name).toBe('Main Greenhouse');
  });
});
