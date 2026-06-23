import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import type {
  PestDetectionResult,
  PestDetectionStatus,
} from '@/api/types';
import { isApiError } from '@/api/errors';
import * as api from '@/api/endpoints/pestDetection';
import i18n from '@/i18n/i18n';

/**
 * REQ-044 — image-based pest detection state.
 *
 * Holds the per-tenant feature status, the in-flight detection result and the
 * history for the active plant. `rejectWithValue` carries an already-translated
 * message plus a machine-readable code so the dialog can branch on
 * CONSENT_REQUIRED / FEATURE_NOT_CONFIGURED.
 */

interface PestDetectionState {
  status: PestDetectionStatus | null;
  statusLoading: boolean;
  result: PestDetectionResult | null;
  detecting: boolean;
  history: PestDetectionResult[];
  historyLoading: boolean;
  error: string | null;
  errorCode: string | null;
}

const initialState: PestDetectionState = {
  status: null,
  statusLoading: false,
  result: null,
  detecting: false,
  history: [],
  historyLoading: false,
  error: null,
  errorCode: null,
};

interface RejectValue {
  message: string;
  code: string | null;
}

function toRejectValue(error: unknown): RejectValue {
  const t = i18n.t.bind(i18n);
  if (isApiError(error)) {
    switch (error.errorCode) {
      case 'CONSENT_REQUIRED':
        return { message: t('pages.pests.consentRequired'), code: error.errorCode };
      case 'FEATURE_NOT_CONFIGURED':
        return { message: t('pages.pests.notConfigured'), code: error.errorCode };
      case 'PAYLOAD_TOO_LARGE':
        return { message: t('pages.pests.imageTooLarge'), code: error.errorCode };
      case 'UNSUPPORTED_MEDIA_TYPE':
        return { message: t('pages.pests.unsupportedFormat'), code: error.errorCode };
      default:
        return { message: error.message || t('errors.server'), code: error.errorCode };
    }
  }
  if (error instanceof Error) {
    return { message: error.message || t('errors.unknown'), code: null };
  }
  return { message: t('errors.unknown'), code: null };
}

export const fetchPestDetectionStatus = createAsyncThunk<PestDetectionStatus>(
  'pestDetection/fetchStatus',
  async () => api.getPestDetectionStatus(),
);

export const detectPests = createAsyncThunk<
  PestDetectionResult,
  { plantKey: string; image: File; language?: string },
  { rejectValue: RejectValue }
>('pestDetection/detect', async ({ plantKey, image, language }, { rejectWithValue }) => {
  try {
    return await api.detectPests(plantKey, image, language);
  } catch (err) {
    return rejectWithValue(toRejectValue(err));
  }
});

export const detectPestsGlobal = createAsyncThunk<
  PestDetectionResult,
  { image: File; language?: string },
  { rejectValue: RejectValue }
>('pestDetection/detectGlobal', async ({ image, language }, { rejectWithValue }) => {
  try {
    return await api.detectPestsGlobal(image, language);
  } catch (err) {
    return rejectWithValue(toRejectValue(err));
  }
});

export const fetchPestDetectionHistory = createAsyncThunk<
  PestDetectionResult[],
  { plantKey: string; limit?: number }
>('pestDetection/fetchHistory', async ({ plantKey, limit }) =>
  api.listPestDetectionHistory(plantKey, limit),
);

export const submitPestFeedback = createAsyncThunk<
  PestDetectionResult,
  {
    detectionKey: string;
    findingLabel: string;
    confirmed: boolean;
    actualLabel?: string | null;
    wasBeneficial?: boolean;
  },
  { rejectValue: RejectValue }
>('pestDetection/feedback', async (arg, { rejectWithValue }) => {
  try {
    return await api.submitPestFeedback(arg.detectionKey, {
      finding_label: arg.findingLabel,
      confirmed: arg.confirmed,
      actual_label: arg.actualLabel ?? null,
      was_beneficial: arg.wasBeneficial ?? false,
    });
  } catch (err) {
    return rejectWithValue(toRejectValue(err));
  }
});

export const createInspectionFromDetection = createAsyncThunk<
  { inspectionKey: string | null },
  { detectionKey: string; plantKey: string },
  { rejectValue: RejectValue }
>('pestDetection/createInspection', async ({ detectionKey, plantKey }, { rejectWithValue }) => {
  try {
    const res = await api.createInspectionFromDetection(detectionKey, plantKey);
    return { inspectionKey: res.inspection_key };
  } catch (err) {
    return rejectWithValue(toRejectValue(err));
  }
});

const pestDetectionSlice = createSlice({
  name: 'pestDetection',
  initialState,
  reducers: {
    resetPestDetection(state) {
      state.result = null;
      state.error = null;
      state.errorCode = null;
      state.detecting = false;
    },
    clearPestDetectionError(state) {
      state.error = null;
      state.errorCode = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPestDetectionStatus.pending, (state) => {
        state.statusLoading = true;
      })
      .addCase(fetchPestDetectionStatus.fulfilled, (state, action) => {
        state.statusLoading = false;
        state.status = action.payload;
      })
      .addCase(fetchPestDetectionStatus.rejected, (state) => {
        state.statusLoading = false;
        // An unreachable status endpoint means "unavailable" — never block UI.
        state.status = {
          available: false,
          feature_enabled: false,
          primary_adapter: '',
          active_adapter: null,
          adapters: {},
        };
      })
      .addCase(detectPests.pending, (state) => {
        state.detecting = true;
        state.error = null;
        state.errorCode = null;
        state.result = null;
      })
      .addCase(detectPests.fulfilled, (state, action) => {
        state.detecting = false;
        state.result = action.payload;
      })
      .addCase(detectPests.rejected, (state, action) => {
        state.detecting = false;
        state.error = action.payload?.message ?? action.error.message ?? 'Detection failed';
        state.errorCode = action.payload?.code ?? null;
      })
      // ── global detect (plant-agnostic) — shares the in-flight result state ──
      .addCase(detectPestsGlobal.pending, (state) => {
        state.detecting = true;
        state.error = null;
        state.errorCode = null;
        state.result = null;
      })
      .addCase(detectPestsGlobal.fulfilled, (state, action) => {
        state.detecting = false;
        state.result = action.payload;
      })
      .addCase(detectPestsGlobal.rejected, (state, action) => {
        state.detecting = false;
        state.error = action.payload?.message ?? action.error.message ?? 'Detection failed';
        state.errorCode = action.payload?.code ?? null;
      })
      .addCase(fetchPestDetectionHistory.pending, (state) => {
        state.historyLoading = true;
      })
      .addCase(fetchPestDetectionHistory.fulfilled, (state, action) => {
        state.historyLoading = false;
        state.history = action.payload;
      })
      .addCase(fetchPestDetectionHistory.rejected, (state) => {
        state.historyLoading = false;
      })
      .addCase(submitPestFeedback.fulfilled, (state, action) => {
        if (state.result && state.result.key === action.payload.key) {
          state.result = action.payload;
        }
      });
  },
});

export const { resetPestDetection, clearPestDetectionError } = pestDetectionSlice.actions;
export default pestDetectionSlice.reducer;
