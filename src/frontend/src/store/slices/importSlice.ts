import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import axios from 'axios';
import type { DuplicateStrategy, EntityType, ImportJob } from '@/api/types';
import { isApiError } from '@/api/errors';
import * as api from '@/api/endpoints/import';
import i18n from '@/i18n/i18n';

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

/** Translate a caught error into a user-facing message. */
function translateError(error: unknown): string {
  const t = i18n.t.bind(i18n);
  if (isApiError(error)) {
    switch (error.errorCode) {
      case 'VALIDATION_ERROR':
        return error.message
          ? t('errors.validationWithDetail', { detail: error.message })
          : t('errors.validation');
      case 'DUPLICATE_ENTRY':
        return t('errors.duplicate');
      case 'ENTITY_NOT_FOUND':
        return t('errors.notFound');
      default:
        return error.message || t('errors.server');
    }
  }
  if (axios.isAxiosError(error)) {
    if (error.code === 'ECONNABORTED' || error.code === 'ERR_CANCELED') {
      return t('errors.networkTimeout');
    }
    if (error.response) {
      const status = error.response.status;
      if (status === 422) {
        const detail = extractDetail(error.response.data);
        return detail
          ? t('errors.validationWithDetail', { detail })
          : t('errors.validation');
      }
      if (status >= 500) return t('errors.server');
    }
    if (!error.response) return t('errors.network');
  }
  if (error instanceof Error && error.message === 'Network Error') {
    return t('errors.network');
  }
  return t('errors.unknown');
}

function extractDetail(data: unknown): string | null {
  if (typeof data === 'string' && data.length > 0 && data.length < 200) return data;
  if (typeof data === 'object' && data !== null) {
    const obj = data as Record<string, unknown>;
    if (typeof obj.detail === 'string') return obj.detail;
    if (typeof obj.message === 'string') return obj.message;
  }
  return null;
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
        state.error = (action.payload as string) ?? action.error.message ?? 'Upload failed';
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
        state.error = (action.payload as string) ?? action.error.message ?? 'Confirm failed';
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
