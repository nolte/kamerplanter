import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import type { DuplicateStrategy, EntityType, ImportJob } from '@/api/types';
import { errorKey } from '@/api/errors';
import * as api from '@/api/endpoints/import';

interface ImportState {
  currentJob: ImportJob | null;
  jobs: ImportJob[];
  total: number;
  loading: boolean;
  error: string | null;
}

const initialState: ImportState = {
  currentJob: null,
  jobs: [],
  total: 0,
  loading: false,
  error: null,
};

/** Map a caught error to an i18n key (#3013) — the component translates it. */
function translateError(error: unknown): string {
  return errorKey(error, 'errors.unknown');
}

export const uploadFile = createAsyncThunk(
  'import/upload',
  async ({
    file,
    entityType,
    duplicateStrategy,
  }: {
    file: File;
    entityType: EntityType;
    duplicateStrategy: DuplicateStrategy;
  }, { rejectWithValue }) => {
    try {
      return await api.uploadImportFile(file, entityType, duplicateStrategy);
    } catch (err) {
      return rejectWithValue(translateError(err));
    }
  },
);

export const fetchImportJob = createAsyncThunk(
  'import/fetchJob',
  async (key: string) => {
    return api.getImportJob(key);
  },
);

export const fetchImportJobs = createAsyncThunk(
  'import/fetchJobs',
  async ({ offset, limit }: { offset: number; limit: number }) => {
    return api.listImportJobs(offset, limit);
  },
);

export const confirmImportJob = createAsyncThunk(
  'import/confirm',
  async (key: string, { rejectWithValue }) => {
    try {
      return await api.confirmImportJob(key);
    } catch (err) {
      return rejectWithValue(translateError(err));
    }
  },
);

export const deleteImportJob = createAsyncThunk(
  'import/delete',
  async (key: string) => {
    await api.deleteImportJob(key);
    return key;
  },
);

const importSlice = createSlice({
  name: 'import',
  initialState,
  reducers: {
    clearCurrentJob(state) {
      state.currentJob = null;
      state.error = null;
    },
    clearImportError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(uploadFile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(uploadFile.fulfilled, (state, action) => {
        state.loading = false;
        state.currentJob = action.payload;
      })
      .addCase(uploadFile.rejected, (state, action) => {
        state.loading = false;
        state.error = (action.payload as string | undefined) ?? errorKey(action.error);
      })
      .addCase(fetchImportJob.fulfilled, (state, action) => {
        state.currentJob = action.payload;
      })
      .addCase(fetchImportJobs.fulfilled, (state, action) => {
        state.jobs = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(confirmImportJob.pending, (state) => {
        state.loading = true;
      })
      .addCase(confirmImportJob.fulfilled, (state, action) => {
        state.loading = false;
        state.currentJob = action.payload;
      })
      .addCase(confirmImportJob.rejected, (state, action) => {
        state.loading = false;
        state.error = (action.payload as string | undefined) ?? errorKey(action.error);
      })
      .addCase(deleteImportJob.fulfilled, (state, action) => {
        state.jobs = state.jobs.filter((j) => j.key !== action.payload);
        if (state.currentJob?.key === action.payload) {
          state.currentJob = null;
        }
      });
  },
});

export const { clearCurrentJob, clearImportError } = importSlice.actions;
export default importSlice.reducer;
