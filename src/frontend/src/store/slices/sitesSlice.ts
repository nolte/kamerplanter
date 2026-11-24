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
import { errorKey } from '@/api/errors';

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
 * The site list. A read from offset 0 — one page, or every page with `all: true` — is the offline-readable one
 * (REQ-053 WP 9.2, UI-NFR-012 R-020): written to the plan cache after every online read, read from it when there
 * is no connection.
 */
/** `listSites`' default page size: the cached first page is kept per page size (#2789 review C7). */
const SITE_LIST_DEFAULT_LIMIT = 50;

export const fetchSites = createAsyncThunk<
  Site[],
  { offset?: number; limit?: number; all?: boolean } | undefined,
  { fulfilledMeta: { cachedAt: number | null }; rejectedMeta: { offlineMiss: boolean } }
>('sites/fetchAll', async (args, { getState, fulfillWithValue, rejectWithValue }) => {
  // `all: true` reads every page (#3015) and is cached under its own entry, apart from the single-page ones.
  const { offset, limit, all = false } = args ?? {};
  const scope = scopeFromState(getState() as ScopeState);
  const entry = scope && (all || !offset) ? siteListEntry(scope, all ? 'all' : (limit ?? SITE_LIST_DEFAULT_LIMIT)) : null;
  try {
    const read = await readThrough(entry, () => (all ? api.listAllSites() : api.listSites(offset, limit)));
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
        // No stale "as of" banner next to a miss or an error (#2789 review C8).
        state.sitesCachedAt = null;
        state.sitesOfflineMiss = action.meta?.offlineMiss ?? false;
        state.error = state.sitesOfflineMiss ? null : (errorKey(action.error, 'errors.loadFailed'));
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
        // A superseded fetch is aborted by the detail page (#3014); its rejection
        // must not clear the loading flag or flag an error for the current site.
        if (action.meta?.aborted) return;
        state.loading = false;
        state.error = errorKey(action.error, 'errors.loadFailed');
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
        state.error = errorKey(action.error, 'errors.loadFailed');
      })
      .addCase(fetchSlots.fulfilled, (state, action) => {
        state.slots = action.payload;
      });
  },
});

export const { clearCurrent, clearError } = sitesSlice.actions;
export default sitesSlice.reducer;
