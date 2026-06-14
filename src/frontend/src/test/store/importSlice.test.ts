import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import { AxiosError, AxiosHeaders } from 'axios';
import reducer, {
  clearCurrentJob,
  clearImportError,
  uploadFile,
  fetchImportJob,
  fetchImportJobs,
  confirmImportJob,
  deleteImportJob,
} from '@/store/slices/importSlice';
import { ApiError } from '@/api/errors';
import * as importApi from '@/api/endpoints/import';

// Isolated module mock — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/import');

const baseState = { currentJob: null, jobs: [], total: 0, loading: false, error: null };

function makeStore() {
  return configureStore({ reducer: { import: reducer } });
}

function apiError(code: string, message = 'msg', status = 400) {
  return new ApiError(
    { error_id: 'e', error_code: code, message, details: [], timestamp: '', path: '/', method: 'POST' },
    status,
  );
}

function axiosError(status?: number, data?: unknown, code?: string) {
  const err = new AxiosError('failed', code);
  if (status !== undefined) {
    err.response = {
      status, statusText: '', data, headers: {}, config: { headers: new AxiosHeaders() },
    };
  }
  return err;
}

const job = { key: 'j1' } as Awaited<ReturnType<typeof importApi.getImportJob>>;

describe('importSlice', () => {
  it('has the empty initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(baseState);
  });

  it('clearCurrentJob resets the current job and error', () => {
    const start = { ...baseState, currentJob: { key: 'j1' } as never, error: 'boom' };
    const state = reducer(start, clearCurrentJob());
    expect(state.currentJob).toBeNull();
    expect(state.error).toBeNull();
  });

  it('clearImportError resets only the error', () => {
    const state = reducer({ ...baseState, error: 'boom' }, clearImportError());
    expect(state.error).toBeNull();
  });

  it('uploadFile.pending sets loading and clears prior error', () => {
    const state = reducer({ ...baseState, error: 'old' }, { type: uploadFile.pending.type });
    expect(state.loading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('uploadFile.fulfilled stores the created job', () => {
    const state = reducer(baseState, { type: uploadFile.fulfilled.type, payload: { key: 'j1' } });
    expect(state.currentJob).toEqual({ key: 'j1' });
    expect(state.loading).toBe(false);
  });

  it('uploadFile.rejected prefers the rejectWithValue payload', () => {
    const state = reducer(baseState, {
      type: uploadFile.rejected.type,
      payload: 'translated message',
      error: { message: 'raw' },
    });
    expect(state.error).toBe('translated message');
  });

  it('uploadFile.rejected falls back to the error message without a payload', () => {
    const state = reducer(baseState, {
      type: uploadFile.rejected.type,
      error: { message: 'raw failure' },
    });
    expect(state.error).toBe('raw failure');
  });

  it('fetchImportJob.fulfilled stores the current job', () => {
    const state = reducer(baseState, { type: fetchImportJob.fulfilled.type, payload: { key: 'j1' } });
    expect(state.currentJob).toEqual({ key: 'j1' });
  });

  it('fetchImportJobs.fulfilled stores jobs and total', () => {
    const state = reducer(baseState, {
      type: fetchImportJobs.fulfilled.type,
      payload: { items: [{ key: 'j1' }], total: 1 },
    });
    expect(state.jobs).toEqual([{ key: 'j1' }]);
    expect(state.total).toBe(1);
  });

  it('confirmImportJob handles pending, fulfilled and rejected', () => {
    expect(reducer(baseState, { type: confirmImportJob.pending.type }).loading).toBe(true);
    const fulfilled = reducer(baseState, { type: confirmImportJob.fulfilled.type, payload: { key: 'j1' } });
    expect(fulfilled.currentJob).toEqual({ key: 'j1' });
    const rejected = reducer(baseState, { type: confirmImportJob.rejected.type, payload: 'nope' });
    expect(rejected.error).toBe('nope');
  });

  it('deleteImportJob.fulfilled removes the job and clears it if current', () => {
    const start = {
      ...baseState,
      jobs: [{ key: 'j1' }, { key: 'j2' }] as never,
      currentJob: { key: 'j1' } as never,
    };
    const state = reducer(start, { type: deleteImportJob.fulfilled.type, payload: 'j1' });
    expect(state.jobs.map((j) => j.key)).toEqual(['j2']);
    expect(state.currentJob).toBeNull();
  });
});

describe('importSlice thunks', () => {
  const mocked = vi.mocked(importApi);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('uploadFile dispatches the API call and stores the job', async () => {
    mocked.uploadImportFile.mockResolvedValue(job);
    const store = makeStore();
    const file = new File(['name\n'], 'data.csv', { type: 'text/csv' });
    await store.dispatch(uploadFile({ file, entityType: 'species', duplicateStrategy: 'skip' }));
    expect(mocked.uploadImportFile).toHaveBeenCalledWith(file, 'species', 'skip');
    expect(store.getState().import.currentJob).toEqual(job);
  });

  it('uploadFile translates a VALIDATION_ERROR into the rejected payload', async () => {
    mocked.uploadImportFile.mockRejectedValue(apiError('VALIDATION_ERROR', 'Spalte fehlt', 422));
    const store = makeStore();
    const file = new File([''], 'bad.csv');
    await store.dispatch(uploadFile({ file, entityType: 'species', duplicateStrategy: 'skip' }));
    expect(store.getState().import.error).toBeTruthy();
  });

  it('uploadFile translates a DUPLICATE_ENTRY error', async () => {
    mocked.uploadImportFile.mockRejectedValue(apiError('DUPLICATE_ENTRY', 'dup', 409));
    const store = makeStore();
    await store.dispatch(uploadFile({ file: new File([''], 'x.csv'), entityType: 'species', duplicateStrategy: 'skip' }));
    expect(store.getState().import.error).toBeTruthy();
  });

  it('uploadFile translates an ENTITY_NOT_FOUND error', async () => {
    mocked.uploadImportFile.mockRejectedValue(apiError('ENTITY_NOT_FOUND', 'nope', 404));
    const store = makeStore();
    await store.dispatch(uploadFile({ file: new File([''], 'x.csv'), entityType: 'species', duplicateStrategy: 'skip' }));
    expect(store.getState().import.error).toBeTruthy();
  });

  it('uploadFile falls back to the message for an unmapped error code', async () => {
    mocked.uploadImportFile.mockRejectedValue(apiError('WEIRD', 'raw detail', 400));
    const store = makeStore();
    await store.dispatch(uploadFile({ file: new File([''], 'x.csv'), entityType: 'species', duplicateStrategy: 'skip' }));
    expect(store.getState().import.error).toBe('raw detail');
  });

  it('uploadFile translates an axios 422 with a detail body', async () => {
    mocked.uploadImportFile.mockRejectedValue(axiosError(422, { detail: 'Zeile 3 ungültig' }));
    const store = makeStore();
    await store.dispatch(uploadFile({ file: new File([''], 'x.csv'), entityType: 'species', duplicateStrategy: 'skip' }));
    expect(store.getState().import.error).toBeTruthy();
  });

  it('uploadFile translates an axios 500 into a server error', async () => {
    mocked.uploadImportFile.mockRejectedValue(axiosError(500));
    const store = makeStore();
    await store.dispatch(uploadFile({ file: new File([''], 'x.csv'), entityType: 'species', duplicateStrategy: 'skip' }));
    expect(store.getState().import.error).toBeTruthy();
  });

  it('uploadFile translates an axios timeout', async () => {
    mocked.uploadImportFile.mockRejectedValue(axiosError(undefined, undefined, 'ECONNABORTED'));
    const store = makeStore();
    await store.dispatch(uploadFile({ file: new File([''], 'x.csv'), entityType: 'species', duplicateStrategy: 'skip' }));
    expect(store.getState().import.error).toBeTruthy();
  });

  it('uploadFile translates an axios network error (no response)', async () => {
    mocked.uploadImportFile.mockRejectedValue(axiosError());
    const store = makeStore();
    await store.dispatch(uploadFile({ file: new File([''], 'x.csv'), entityType: 'species', duplicateStrategy: 'skip' }));
    expect(store.getState().import.error).toBeTruthy();
  });

  it('uploadFile translates a plain Network Error', async () => {
    mocked.uploadImportFile.mockRejectedValue(new Error('Network Error'));
    const store = makeStore();
    await store.dispatch(uploadFile({ file: new File([''], 'x.csv'), entityType: 'species', duplicateStrategy: 'skip' }));
    expect(store.getState().import.error).toBeTruthy();
  });

  it('uploadFile translates an unknown error', async () => {
    mocked.uploadImportFile.mockRejectedValue({ weird: true });
    const store = makeStore();
    await store.dispatch(uploadFile({ file: new File([''], 'x.csv'), entityType: 'species', duplicateStrategy: 'skip' }));
    expect(store.getState().import.error).toBeTruthy();
  });

  it('fetchImportJob dispatches the API call and stores the job', async () => {
    mocked.getImportJob.mockResolvedValue(job);
    const store = makeStore();
    await store.dispatch(fetchImportJob('j1'));
    expect(mocked.getImportJob).toHaveBeenCalledWith('j1');
    expect(store.getState().import.currentJob).toEqual(job);
  });

  it('fetchImportJobs dispatches the API call and stores jobs + total', async () => {
    mocked.listImportJobs.mockResolvedValue({ items: [job], total: 1 });
    const store = makeStore();
    await store.dispatch(fetchImportJobs({ offset: 0, limit: 10 }));
    expect(mocked.listImportJobs).toHaveBeenCalledWith(0, 10);
    expect(store.getState().import.jobs).toEqual([job]);
    expect(store.getState().import.total).toBe(1);
  });

  it('confirmImportJob dispatches the API call and stores the job', async () => {
    mocked.confirmImportJob.mockResolvedValue(job);
    const store = makeStore();
    await store.dispatch(confirmImportJob('j1'));
    expect(mocked.confirmImportJob).toHaveBeenCalledWith('j1');
    expect(store.getState().import.currentJob).toEqual(job);
  });

  it('confirmImportJob translates a rejection into the error payload', async () => {
    mocked.confirmImportJob.mockRejectedValue(apiError('VALIDATION_ERROR', 'bad', 422));
    const store = makeStore();
    await store.dispatch(confirmImportJob('j1'));
    expect(store.getState().import.error).toBeTruthy();
  });

  it('deleteImportJob dispatches the API call and removes the job', async () => {
    mocked.deleteImportJob.mockResolvedValue(undefined);
    const store = configureStore({
      reducer: { import: reducer },
      preloadedState: { import: { ...baseState, jobs: [job] } },
    });
    await store.dispatch(deleteImportJob('j1'));
    expect(mocked.deleteImportJob).toHaveBeenCalledWith('j1');
    expect(store.getState().import.jobs).toEqual([]);
  });
});
