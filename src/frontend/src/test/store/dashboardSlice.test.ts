import { describe, it, expect, beforeEach, vi } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';

const apiMock = vi.hoisted(() => ({
  getWidgetCatalog: vi.fn(),
  getAggregated: vi.fn(),
}));
vi.mock('@/api/endpoints/dashboard', () => ({
  getWidgetCatalog: apiMock.getWidgetCatalog,
  getAggregated: apiMock.getAggregated,
}));

import reducer, { fetchWidgetCatalog, fetchAggregated } from '@/store/slices/dashboardSlice';

function createStore() {
  return configureStore({ reducer: { dashboard: reducer } });
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('dashboardSlice', () => {
  it('has the empty initial state', () => {
    const state = reducer(undefined, { type: '@@INIT' });
    expect(state).toEqual({
      catalog: [],
      catalogLoaded: false,
      aggregated: {},
      loading: false,
      error: null,
    });
  });

  describe('fetchWidgetCatalog', () => {
    it('sets loading on pending', () => {
      const state = reducer(undefined, { type: fetchWidgetCatalog.pending.type });
      expect(state.loading).toBe(true);
      expect(state.error).toBeNull();
    });

    it('stores the catalog and marks it loaded on fulfilled', async () => {
      apiMock.getWidgetCatalog.mockResolvedValue({ widgets: [{ widget_key: 'plants' }] });
      const store = createStore();
      await store.dispatch(fetchWidgetCatalog());
      const state = store.getState().dashboard;
      expect(state.catalog).toEqual([{ widget_key: 'plants' }]);
      expect(state.catalogLoaded).toBe(true);
      expect(state.loading).toBe(false);
    });

    it('records the error message on rejected', async () => {
      apiMock.getWidgetCatalog.mockRejectedValue(new Error('boom'));
      const store = createStore();
      await store.dispatch(fetchWidgetCatalog());
      expect(store.getState().dashboard.error).toBe('boom');
      expect(store.getState().dashboard.loading).toBe(false);
    });

    it('falls back to a default error message when none is given', () => {
      const state = reducer(undefined, {
        type: fetchWidgetCatalog.rejected.type,
        error: {},
      });
      expect(state.error).toBe('errors.dashboardCatalogLoadFailed');
    });
  });

  describe('fetchAggregated', () => {
    it('short-circuits to an empty object for no widget keys (no API call)', async () => {
      const store = createStore();
      await store.dispatch(fetchAggregated([]));
      expect(apiMock.getAggregated).not.toHaveBeenCalled();
      expect(store.getState().dashboard.aggregated).toEqual({});
    });

    it('stores the aggregated payload on fulfilled', async () => {
      apiMock.getAggregated.mockResolvedValue({ widgets: { plants: { count: 3 } } });
      const store = createStore();
      await store.dispatch(fetchAggregated(['plants']));
      expect(apiMock.getAggregated).toHaveBeenCalledWith(['plants']);
      expect(store.getState().dashboard.aggregated).toEqual({ plants: { count: 3 } });
    });
  });
});
