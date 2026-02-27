import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import type { DuplicateStrategy, EntityType, ImportJob } from '@/api/types';
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
  }) => {
    return api.uploadImportFile(file, entityType, duplicateStrategy);
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
  async (key: string) => {
    return api.confirmImportJob(key);
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
        state.error = action.error.message ?? 'Upload failed';
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
        state.error = action.error.message ?? 'Confirm failed';
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
