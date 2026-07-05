import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { DashboardWidgetCatalogEntry } from '@/api/types';
import * as api from '@/api/endpoints/dashboard';

/**
 * REQ-045 — dashboard personalization read-state: the server-authoritative
 * widget catalog (availability) and the REQ-009 aggregated payloads for the
 * user's active widgets. Kept separate from userPreferences (which owns the
 * layout itself) so both the dashboard page and the settings tab can consume
 * catalog availability.
 */

interface DashboardState {
  catalog: DashboardWidgetCatalogEntry[];
  catalogLoaded: boolean;
  aggregated: Record<string, unknown>;
  loading: boolean;
  error: string | null;
}

const initialState: DashboardState = {
  catalog: [],
  catalogLoaded: false,
  aggregated: {},
  loading: false,
  error: null,
};

export const fetchWidgetCatalog = createAsyncThunk('dashboard/fetchWidgetCatalog', async () => {
  const res = await api.getWidgetCatalog();
  return res.widgets;
});

export const fetchAggregated = createAsyncThunk('dashboard/fetchAggregated', async (widgetKeys: string[]) => {
  if (widgetKeys.length === 0) return {};
  const res = await api.getAggregated(widgetKeys);
  return res.widgets;
});

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchWidgetCatalog.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchWidgetCatalog.fulfilled, (state, action) => {
        state.loading = false;
        state.catalog = action.payload;
        state.catalogLoaded = true;
      })
      .addCase(fetchWidgetCatalog.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'errors.dashboardCatalogLoadFailed';
      })
      .addCase(fetchAggregated.fulfilled, (state, action) => {
        state.aggregated = action.payload;
      });
  },
});

export default dashboardSlice.reducer;
