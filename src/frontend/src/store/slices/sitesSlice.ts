import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Site, Location, Slot } from '@/api/types';
import * as api from '@/api/endpoints/sites';
import {
  isOfflineCacheMiss,
  readThrough,
  scopeFromState,
  siteListEntry,
  type ScopeState,
} from '@/features/gardenPlanner/offline/planCache';

interface SitesState {
  sites: Site[];
  currentSite: Site | null;
  locations: Location[];
  currentLocation: Location | null;
  slots: Slot[];
  loading: boolean;
  error: string | null;
  /**
   * The site list comes from the plan cache (REQ-053 WP 9.2): epoch milliseconds of the online read it
   * was stored by; `null` = from the server.
   */
  sitesCachedAt: number | null;
  /** Offline and no cached site list for this user and tenant. */
  sitesOfflineMiss: boolean;
}

const initialState: SitesState = {
  sites: [],
  currentSite: null,
  locations: [],
  currentLocation: null,
  slots: [],
  loading: false,
  error: null,
  sitesCachedAt: null,
  sitesOfflineMiss: false,
};

/**
 * The site list. Its first page is the offline-readable one (REQ-053 WP 9.2, UI-NFR-012 R-020): written to
 * the plan cache after every online read, read from it when there is no connection.
 */
export const fetchSites = createAsyncThunk<
  Site[],
  { offset?: number; limit?: number } | undefined,
  { fulfilledMeta: { cachedAt: number | null }; rejectedMeta: { offlineMiss: boolean } }
>('sites/fetchAll', async (args, { getState, fulfillWithValue, rejectWithValue }) => {
  const { offset, limit } = args ?? {};
  const scope = scopeFromState(getState() as ScopeState);
  const entry = scope && !offset ? siteListEntry(scope) : null;
  try {
    const read = await readThrough(entry, () => api.listSites(offset, limit));
    return fulfillWithValue(read.data, { cachedAt: read.cachedAt });
  } catch (error) {
    if (isOfflineCacheMiss(error)) return rejectWithValue(undefined, { offlineMiss: true });
    throw error;
  }
});

export const fetchSite = createAsyncThunk('sites/fetchOne', async (key: string) => {
  return api.getSite(key);
});

export const fetchLocations = createAsyncThunk(
  'sites/fetchLocations',
  async (siteKey: string) => {
    return api.listLocations(siteKey);
  },
);

export const fetchLocation = createAsyncThunk(
  'sites/fetchLocation',
  async (key: string) => {
    return api.getLocation(key);
  },
);

export const fetchSlots = createAsyncThunk(
  'sites/fetchSlots',
  async (locationKey: string) => {
    return api.listSlots(locationKey);
  },
);

const sitesSlice = createSlice({
  name: 'sites',
  initialState,
  reducers: {
    clearCurrent(state) {
      state.currentSite = null;
      state.currentLocation = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchSites.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.sitesOfflineMiss = false;
      })
      .addCase(fetchSites.fulfilled, (state, action) => {
        state.loading = false;
        state.sites = action.payload;
        state.sitesCachedAt = action.meta?.cachedAt ?? null;
      })
      .addCase(fetchSites.rejected, (state, action) => {
        state.loading = false;
        state.sitesOfflineMiss = action.meta?.offlineMiss ?? false;
        state.error = state.sitesOfflineMiss ? null : (action.error.message ?? 'errors.loadFailed');
      })
      .addCase(fetchSite.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSite.fulfilled, (state, action) => {
        state.loading = false;
        state.currentSite = action.payload;
      })
      .addCase(fetchSite.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'errors.loadFailed';
      })
      .addCase(fetchLocations.fulfilled, (state, action) => {
        state.locations = action.payload;
      })
      .addCase(fetchLocation.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchLocation.fulfilled, (state, action) => {
        state.loading = false;
        state.currentLocation = action.payload;
      })
      .addCase(fetchLocation.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'errors.loadFailed';
      })
      .addCase(fetchSlots.fulfilled, (state, action) => {
        state.slots = action.payload;
      });
  },
});

export const { clearCurrent, clearError } = sitesSlice.actions;
export default sitesSlice.reducer;
