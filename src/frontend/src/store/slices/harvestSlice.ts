import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type {
  HarvestBatch,
  HarvestIndicator,
  HarvestObservation,
  QualityAssessment,
  ReadinessAssessment,
  YieldMetric,
} from '@/api/types';
import * as api from '@/api/endpoints/harvest';

interface HarvestState {
  indicators: HarvestIndicator[];
  observations: HarvestObservation[];
  batches: HarvestBatch[];
  currentBatch: HarvestBatch | null;
  quality: QualityAssessment | null;
  yieldMetric: YieldMetric | null;
  readiness: ReadinessAssessment | null;
  /**
   * Plant the cached {@link readiness} (or {@link readinessError}) belongs to.
   *
   * The assessment is plant-scoped but lives in a single shared slot, so a
   * consumer must be able to tell "this is my plant's assessment" from "this is
   * the sibling I navigated away from". Recording the requested plant on
   * ``pending`` and re-checking it on ``fulfilled``/``rejected`` also discards
   * out-of-order responses: switching plants mid-flight can otherwise let the
   * first plant's late response overwrite the second plant's fresh one.
   */
  readinessPlantKey: string | null;
  /**
   * Dedicated flags for the readiness request. The shared ``loading``/``error``
   * pair is driven by the harvest list thunks (indicators, batches), so reusing
   * it would make an embedded readiness card flicker whenever an unrelated
   * harvest list loads elsewhere in the app.
   */
  readinessLoading: boolean;
  readinessError: string | null;
  loading: boolean;
  error: string | null;
}

const initialState: HarvestState = {
  indicators: [],
  observations: [],
  batches: [],
  currentBatch: null,
  quality: null,
  yieldMetric: null,
  readiness: null,
  readinessPlantKey: null,
  readinessLoading: false,
  readinessError: null,
  loading: false,
  error: null,
};

export const fetchIndicators = createAsyncThunk(
  'harvest/fetchIndicators',
  async ({ offset, limit }: { offset?: number; limit?: number } = {}) => {
    return api.getIndicators(offset, limit);
  },
);

export const fetchBatches = createAsyncThunk(
  'harvest/fetchBatches',
  async ({ offset, limit }: { offset?: number; limit?: number } = {}) => {
    return api.getBatches(offset, limit);
  },
);

export const fetchBatch = createAsyncThunk(
  'harvest/fetchBatch',
  async (key: string) => {
    return api.getBatch(key);
  },
);

export const fetchQuality = createAsyncThunk(
  'harvest/fetchQuality',
  async (batchKey: string) => {
    return api.getQuality(batchKey);
  },
);

export const fetchYieldMetric = createAsyncThunk(
  'harvest/fetchYieldMetric',
  async (batchKey: string) => {
    return api.getYield(batchKey);
  },
);

export const fetchObservations = createAsyncThunk(
  'harvest/fetchObservations',
  async ({
    plantKey,
    offset,
    limit,
  }: {
    plantKey: string;
    offset?: number;
    limit?: number;
  }) => {
    return api.getObservations(plantKey, offset, limit);
  },
);

export const fetchReadiness = createAsyncThunk(
  'harvest/fetchReadiness',
  async (plantKey: string) => {
    return api.assessReadiness(plantKey);
  },
);

const harvestSlice = createSlice({
  name: 'harvest',
  initialState,
  reducers: {
    clearCurrentBatch(state) {
      state.currentBatch = null;
      state.quality = null;
      state.yieldMetric = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Indicators
      .addCase(fetchIndicators.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchIndicators.fulfilled, (state, action) => {
        state.loading = false;
        state.indicators = action.payload;
      })
      .addCase(fetchIndicators.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'errors.loadFailed';
      })
      // Batches
      .addCase(fetchBatches.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBatches.fulfilled, (state, action) => {
        state.loading = false;
        state.batches = action.payload;
      })
      .addCase(fetchBatches.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'errors.loadFailed';
      })
      // Single batch
      .addCase(fetchBatch.fulfilled, (state, action) => {
        state.currentBatch = action.payload;
      })
      // Quality
      .addCase(fetchQuality.fulfilled, (state, action) => {
        state.quality = action.payload;
      })
      // Yield
      .addCase(fetchYieldMetric.fulfilled, (state, action) => {
        state.yieldMetric = action.payload;
      })
      // Observations
      .addCase(fetchObservations.fulfilled, (state, action) => {
        state.observations = action.payload;
      })
      // Readiness
      .addCase(fetchReadiness.pending, (state, action) => {
        state.readinessLoading = true;
        state.readinessError = null;
        // Drop the previous plant's assessment immediately so a consumer never
        // paints a stale score while the new one is in flight.
        state.readiness = null;
        state.readinessPlantKey = action.meta.arg;
      })
      .addCase(fetchReadiness.fulfilled, (state, action) => {
        // Ignore a response that a newer request has already superseded.
        if (action.meta.arg !== state.readinessPlantKey) return;
        state.readinessLoading = false;
        state.readiness = action.payload;
      })
      .addCase(fetchReadiness.rejected, (state, action) => {
        if (action.meta.arg !== state.readinessPlantKey) return;
        state.readinessLoading = false;
        state.readinessError = action.error.message ?? 'errors.loadFailed';
      });
  },
});

export const { clearCurrentBatch, clearError } = harvestSlice.actions;
export default harvestSlice.reducer;
