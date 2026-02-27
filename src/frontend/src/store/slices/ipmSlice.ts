import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type {
  Disease,
  Inspection,
  KarenzPeriod,
  Pest,
  Treatment,
  TreatmentApplication,
} from '@/api/types';
import * as api from '@/api/endpoints/ipm';

interface IpmState {
  pests: Pest[];
  diseases: Disease[];
  treatments: Treatment[];
  inspections: Inspection[];
  applications: TreatmentApplication[];
  karenzPeriods: KarenzPeriod[];
  currentPest: Pest | null;
  currentDisease: Disease | null;
  currentTreatment: Treatment | null;
  loading: boolean;
  error: string | null;
}

const initialState: IpmState = {
  pests: [],
  diseases: [],
  treatments: [],
  inspections: [],
  applications: [],
  karenzPeriods: [],
  currentPest: null,
  currentDisease: null,
  currentTreatment: null,
  loading: false,
  error: null,
};

// ── Pests ─────────────────────────────────────────────────────────────

export const fetchPests = createAsyncThunk(
  'ipm/fetchPests',
  async ({
    offset,
    limit,
  }: {
    offset?: number;
    limit?: number;
  } = {}) => {
    return api.listPests(offset, limit);
  },
);

export const fetchPest = createAsyncThunk(
  'ipm/fetchPest',
  async (key: string) => {
    return api.getPest(key);
  },
);

// ── Diseases ──────────────────────────────────────────────────────────

export const fetchDiseases = createAsyncThunk(
  'ipm/fetchDiseases',
  async ({
    offset,
    limit,
  }: {
    offset?: number;
    limit?: number;
  } = {}) => {
    return api.listDiseases(offset, limit);
  },
);

export const fetchDisease = createAsyncThunk(
  'ipm/fetchDisease',
  async (key: string) => {
    return api.getDisease(key);
  },
);

// ── Treatments ────────────────────────────────────────────────────────

export const fetchTreatments = createAsyncThunk(
  'ipm/fetchTreatments',
  async ({
    offset,
    limit,
  }: {
    offset?: number;
    limit?: number;
  } = {}) => {
    return api.listTreatments(offset, limit);
  },
);

export const fetchTreatment = createAsyncThunk(
  'ipm/fetchTreatment',
  async (key: string) => {
    return api.getTreatment(key);
  },
);

// ── Inspections ───────────────────────────────────────────────────────

export const fetchInspections = createAsyncThunk(
  'ipm/fetchInspections',
  async ({
    plantKey,
    offset,
    limit,
  }: {
    plantKey: string;
    offset?: number;
    limit?: number;
  }) => {
    return api.getInspections(plantKey, offset, limit);
  },
);

// ── Treatment Applications ────────────────────────────────────────────

export const fetchApplications = createAsyncThunk(
  'ipm/fetchApplications',
  async ({
    plantKey,
    offset,
    limit,
  }: {
    plantKey: string;
    offset?: number;
    limit?: number;
  }) => {
    return api.getTreatmentApplications(plantKey, offset, limit);
  },
);

// ── Karenz ────────────────────────────────────────────────────────────

export const fetchKarenzPeriods = createAsyncThunk(
  'ipm/fetchKarenzPeriods',
  async (plantKey: string) => {
    return api.getKarenzPeriods(plantKey);
  },
);

const ipmSlice = createSlice({
  name: 'ipm',
  initialState,
  reducers: {
    clearCurrentPest(state) {
      state.currentPest = null;
    },
    clearCurrentDisease(state) {
      state.currentDisease = null;
    },
    clearCurrentTreatment(state) {
      state.currentTreatment = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Pests
      .addCase(fetchPests.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPests.fulfilled, (state, action) => {
        state.loading = false;
        state.pests = action.payload;
      })
      .addCase(fetchPests.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load pests';
      })
      .addCase(fetchPest.fulfilled, (state, action) => {
        state.currentPest = action.payload;
      })
      // Diseases
      .addCase(fetchDiseases.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDiseases.fulfilled, (state, action) => {
        state.loading = false;
        state.diseases = action.payload;
      })
      .addCase(fetchDiseases.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load diseases';
      })
      .addCase(fetchDisease.fulfilled, (state, action) => {
        state.currentDisease = action.payload;
      })
      // Treatments
      .addCase(fetchTreatments.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTreatments.fulfilled, (state, action) => {
        state.loading = false;
        state.treatments = action.payload;
      })
      .addCase(fetchTreatments.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load treatments';
      })
      .addCase(fetchTreatment.fulfilled, (state, action) => {
        state.currentTreatment = action.payload;
      })
      // Inspections
      .addCase(fetchInspections.fulfilled, (state, action) => {
        state.inspections = action.payload;
      })
      // Treatment Applications
      .addCase(fetchApplications.fulfilled, (state, action) => {
        state.applications = action.payload;
      })
      // Karenz
      .addCase(fetchKarenzPeriods.fulfilled, (state, action) => {
        state.karenzPeriods = action.payload;
      });
  },
});

export const {
  clearCurrentPest,
  clearCurrentDisease,
  clearCurrentTreatment,
  clearError,
} = ipmSlice.actions;
export default ipmSlice.reducer;
