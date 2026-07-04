import { describe, it, expect, vi } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import { createListSlice } from '@/store/createListSlice';

interface Item {
  key: string;
  name?: string;
}

function makeSlice(overrides: Partial<Parameters<typeof createListSlice<Item>>[0]> = {}) {
  return createListSlice<Item>({
    name: 'widgets',
    list: async ({ offset = 0, limit = 50 } = {}) => ({ items: [], total: 0, offset, limit }),
    getOne: async (key) => ({ key }),
    ...overrides,
  });
}

describe('createListSlice', () => {
  it('exposes thunks with the configured action-type prefix', () => {
    const { fetchList, fetchOne } = makeSlice();
    expect(fetchList.pending.type).toBe('widgets/fetchAll/pending');
    expect(fetchOne?.fulfilled.type).toBe('widgets/fetchOne/fulfilled');
  });

  it('has the shared initial state', () => {
    const { reducer } = makeSlice();
    const state = reducer(undefined, { type: 'unknown' });
    expect(state).toEqual({
      items: [],
      total: 0,
      offset: 0,
      limit: 50,
      current: null,
      loading: false,
      error: null,
    });
  });

  it('fetchList.fulfilled with a paginated envelope fills pagination fields', () => {
    const { reducer, fetchList } = makeSlice();
    const payload = { items: [{ key: 'w1' }], total: 7, offset: 10, limit: 20 };
    const state = reducer(undefined, { type: fetchList.fulfilled.type, payload });
    expect(state.loading).toBe(false);
    expect(state.items).toEqual([{ key: 'w1' }]);
    expect(state.total).toBe(7);
    expect(state.offset).toBe(10);
    expect(state.limit).toBe(20);
  });

  it('fetchList.fulfilled with a plain array fills items only', () => {
    const { reducer, fetchList } = makeSlice();
    const payload = [{ key: 'w1' }, { key: 'w2' }];
    const state = reducer(undefined, { type: fetchList.fulfilled.type, payload });
    expect(state.items).toEqual(payload);
    expect(state.total).toBe(0);
    expect(state.limit).toBe(50);
  });

  it('fetchList.pending sets loading and clears prior error', () => {
    const { reducer, fetchList } = makeSlice();
    const prior = {
      items: [], total: 0, offset: 0, limit: 50, current: null, loading: false, error: 'errors.loadFailed',
    };
    const state = reducer(prior, { type: fetchList.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('fetchList.rejected without a message stores the default i18n key', () => {
    const { reducer, fetchList } = makeSlice();
    const state = reducer(undefined, { type: fetchList.rejected.type, error: {} });
    expect(state.error).toBe('errors.loadFailed');
    expect(state.loading).toBe(false);
  });

  it('fetchList.rejected preserves an ApiError message', () => {
    const { reducer, fetchList } = makeSlice();
    const state = reducer(undefined, {
      type: fetchList.rejected.type,
      error: { message: 'Widget not found' },
    });
    expect(state.error).toBe('Widget not found');
  });

  it('uses a custom errorKey as the fallback', () => {
    const { reducer, fetchList } = makeSlice({ errorKey: 'errors.optionsLoadFailed' });
    const state = reducer(undefined, { type: fetchList.rejected.type, error: {} });
    expect(state.error).toBe('errors.optionsLoadFailed');
  });

  it('fetchOne.fulfilled sets current and rejected sets error', () => {
    const { reducer, fetchOne } = makeSlice();
    const loaded = reducer(undefined, {
      type: fetchOne!.fulfilled.type,
      payload: { key: 'w9', name: 'Nine' },
    });
    expect(loaded.current).toEqual({ key: 'w9', name: 'Nine' });

    const failed = reducer(undefined, { type: fetchOne!.rejected.type, error: {} });
    expect(failed.error).toBe('errors.loadFailed');
  });

  it('clearCurrent and clearError reset their fields', () => {
    const { reducer, actions } = makeSlice();
    const withCurrent = {
      items: [], total: 0, offset: 0, limit: 50, current: { key: 'x' }, loading: false, error: 'e',
    };
    expect(reducer(withCurrent, actions.clearCurrent()).current).toBeNull();
    expect(reducer(withCurrent, actions.clearError()).error).toBeNull();
  });

  it('omits fetchOne when getOne is not configured', () => {
    const { fetchOne } = createListSlice<Item>({
      name: 'listOnly',
      list: async ({ offset = 0, limit = 50 } = {}) => ({ items: [], total: 0, offset, limit }),
    });
    expect(fetchOne).toBeUndefined();
  });

  it('invokes the extraCases builder extension', () => {
    const extraCases = vi.fn();
    const { reducer } = makeSlice({ extraCases });
    // RTK builds extraReducers lazily on first reducer invocation.
    reducer(undefined, { type: '@@init/force-build' });
    expect(extraCases).toHaveBeenCalledOnce();
  });

  it('loads via the real thunk using the configured list function', async () => {
    const list = vi.fn(async ({ offset = 0, limit = 50 }: { offset?: number; limit?: number } = {}) => ({
      items: [{ key: 'a' }],
      total: 1,
      offset,
      limit,
    }));
    const { reducer, fetchList } = makeSlice({ list });
    const store = configureStore({ reducer: { widgets: reducer } });
    await store.dispatch(fetchList({ offset: 5, limit: 25 }));
    expect(list).toHaveBeenCalledWith({ offset: 5, limit: 25 });
    expect(store.getState().widgets.items).toEqual([{ key: 'a' }]);
    expect(store.getState().widgets.offset).toBe(5);
  });
});
