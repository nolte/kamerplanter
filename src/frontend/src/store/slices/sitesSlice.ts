import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Site, Location, Slot } from '@/api/types';
import * as api from '@/api/endpoints/sites';

interface SitesState {
  sites: Site[];
  currentSite: Site | null;
  locations: Location[];
  currentLocation: Location | null;
  slots: Slot[];
  loading: boolean;
  error: string | null;
}

const initialState: SitesState = {
  sites: [],
  currentSite: null,
  locations: [],
  currentLocation: null,
  slots: [],
  loading: false,
  error: null,
};

export const fetchSites = createAsyncThunk(
  'sites/fetchAll',
  async ({ offset, limit }: { offset?: number; limit?: number } = {}) => {
    return api.listSites(offset, limit);
  },
);

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
      })
      .addCase(fetchSites.fulfilled, (state, action) => {
        state.loading = false;
        state.sites = action.payload;
      })
      .addCase(fetchSites.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load sites';
      })
      .addCase(fetchSite.fulfilled, (state, action) => {
        state.currentSite = action.payload;
      })
      .addCase(fetchLocations.fulfilled, (state, action) => {
        state.locations = action.payload;
      })
      .addCase(fetchLocation.fulfilled, (state, action) => {
        state.currentLocation = action.payload;
      })
      .addCase(fetchSlots.fulfilled, (state, action) => {
        state.slots = action.payload;
      });
  },
});

export const { clearCurrent, clearError } = sitesSlice.actions;
export default sitesSlice.reducer;
