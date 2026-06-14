import { describe, it, expect } from 'vitest';
import reducer, {
  clearCurrentJob,
  clearImportError,
  uploadFile,
  fetchImportJob,
  fetchImportJobs,
  confirmImportJob,
  deleteImportJob,
} from '@/store/slices/importSlice';

const baseState = { currentJob: null, jobs: [], total: 0, loading: false, error: null };

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
