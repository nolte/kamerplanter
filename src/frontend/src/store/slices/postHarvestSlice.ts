import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type {
  DryingProgress,
  MoldAlert,
  PostHarvestBatch,
  PostHarvestBatchDetail,
  PostHarvestStage,
  StartDryingRequest,
  StorageObservation,
  StorageObservationCreate,
  DryingProgressCreate,
} from '@/api/types';
import * as api from '@/api/endpoints/postHarvest';

interface PostHarvestState {
  batches: PostHarvestBatch[];
  currentDetail: PostHarvestBatchDetail | null;
  dryingProgress: DryingProgress[];
  observations: StorageObservation[];
  moldAlerts: MoldAlert[];
  loading: boolean;
  error: string | null;
}

const initialState: PostHarvestState = {
  batches: [],
  currentDetail: null,
  dryingProgress: [],
  observations: [],
  moldAlerts: [],
  loading: false,
  error: null,
};

export const fetchPostHarvestBatches = createAsyncThunk(
  'postHarvest/fetchBatches',
  async ({ offset, limit }: { offset?: number; limit?: number } = {}) => {
    return api.getBatches(offset, limit);
  },
);

export const fetchPostHarvestBatch = createAsyncThunk(
  'postHarvest/fetchBatch',
  async (key: string) => {
    return api.getBatch(key);
  },
);

export const startDrying = createAsyncThunk(
  'postHarvest/startDrying',
  async (payload: StartDryingRequest) => {
    return api.startDrying(payload);
  },
);

export const advancePostHarvestStage = createAsyncThunk(
  'postHarvest/advanceStage',
  async ({ key, targetStage }: { key: string; targetStage: PostHarvestStage }) => {
    return api.advanceStage(key, targetStage);
  },
);

export const recordDryingProgress = createAsyncThunk(
  'postHarvest/recordDryingProgress',
  async ({ key, payload }: { key: string; payload: DryingProgressCreate }) => {
    await api.recordDryingProgress(key, payload);
    return api.getBatch(key);
  },
);

export const recordObservation = createAsyncThunk(
  'postHarvest/recordObservation',
  async ({ key, payload }: { key: string; payload: StorageObservationCreate }) => {
    await api.recordObservation(key, payload);
    return api.getBatch(key);
  },
);

export const fetchDryingProgress = createAsyncThunk(
  'postHarvest/fetchDryingProgress',
  async (key: string) => {
    return api.getDryingProgress(key);
  },
);

export const fetchObservations = createAsyncThunk(
  'postHarvest/fetchObservations',
  async (key: string) => {
    return api.getObservations(key);
  },
);

export const fetchMoldAlerts = createAsyncThunk(
  'postHarvest/fetchMoldAlerts',
  async (key: string) => {
    return api.getMoldAlerts(key);
  },
);

const postHarvestSlice = createSlice({
  name: 'postHarvest',
  initialState,
  reducers: {
    clearCurrentDetail(state) {
      state.currentDetail = null;
      state.dryingProgress = [];
      state.observations = [];
      state.moldAlerts = [];
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPostHarvestBatches.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPostHarvestBatches.fulfilled, (state, action) => {
        state.loading = false;
        state.batches = action.payload;
      })
      .addCase(fetchPostHarvestBatches.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'errors.loadFailed';
      })
      .addCase(fetchPostHarvestBatch.fulfilled, (state, action) => {
        state.currentDetail = action.payload;
      })
      .addCase(advancePostHarvestStage.fulfilled, (state, action) => {
        if (state.currentDetail) {
          state.currentDetail.batch = action.payload;
        }
      })
      .addCase(recordDryingProgress.fulfilled, (state, action) => {
        state.currentDetail = action.payload;
      })
      .addCase(recordObservation.fulfilled, (state, action) => {
        state.currentDetail = action.payload;
      })
      .addCase(fetchDryingProgress.fulfilled, (state, action) => {
        state.dryingProgress = action.payload;
      })
      .addCase(fetchObservations.fulfilled, (state, action) => {
        state.observations = action.payload;
      })
      .addCase(fetchMoldAlerts.fulfilled, (state, action) => {
        state.moldAlerts = action.payload ?? [];
      });
  },
});

export const { clearCurrentDetail, clearError } = postHarvestSlice.actions;
export default postHarvestSlice.reducer;
