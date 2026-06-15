import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import type {
  IdentificationHistoryEntry,
  IdentificationSelection,
  IdentificationStatus,
  IdentifyResult,
  PlantOrgan,
} from '@/api/types';
import { isApiError } from '@/api/errors';
import * as api from '@/api/endpoints/identification';
import i18n from '@/i18n/i18n';

/**
 * REQ-029 / REQ-029-A — plant identification state.
 *
 * The slice keeps the public feature status, the in-flight identify result
 * (rank-sorted candidates), the persisted selection and the history list.
 * `rejectWithValue` carries an already-translated message so components can
 * render it directly; `errorCode` is surfaced separately so the dialog can
 * branch on CONSENT_REQUIRED / FEATURE_NOT_CONFIGURED / RATE_LIMIT_EXCEEDED.
 */

interface IdentificationState {
  status: IdentificationStatus | null;
  statusLoading: boolean;
  result: IdentifyResult | null;
  identifying: boolean;
  selection: IdentificationSelection | null;
  selecting: boolean;
  history: IdentificationHistoryEntry[];
  historyLoading: boolean;
  error: string | null;
  errorCode: string | null;
}

const initialState: IdentificationState = {
  status: null,
  statusLoading: false,
  result: null,
  identifying: false,
  selection: null,
  selecting: false,
  history: [],
  historyLoading: false,
  error: null,
  errorCode: null,
};

interface RejectValue {
  message: string;
  code: string | null;
}

/** Translate a caught error into a user-facing message + machine-readable code. */
function toRejectValue(error: unknown): RejectValue {
  const t = i18n.t.bind(i18n);
  if (isApiError(error)) {
    switch (error.errorCode) {
      case 'CONSENT_REQUIRED':
        return { message: t('pages.plantIdentification.consentRequired'), code: error.errorCode };
      case 'FEATURE_NOT_CONFIGURED':
        return { message: t('pages.plantIdentification.notConfigured'), code: error.errorCode };
      case 'RATE_LIMIT_EXCEEDED':
        return { message: t('pages.plantIdentification.rateLimitReached'), code: error.errorCode };
      case 'PAYLOAD_TOO_LARGE':
        return { message: t('pages.plantIdentification.imageTooLarge'), code: error.errorCode };
      case 'UNSUPPORTED_MEDIA_TYPE':
        return { message: t('pages.plantIdentification.unsupportedFormat'), code: error.errorCode };
      default:
        return { message: error.message || t('errors.server'), code: error.errorCode };
    }
  }
  if (error instanceof Error) {
    return { message: error.message || t('errors.unknown'), code: null };
  }
  return { message: t('errors.unknown'), code: null };
}

export const fetchIdentificationStatus = createAsyncThunk<IdentificationStatus>(
  'identification/fetchStatus',
  async () => api.getIdentificationStatus(),
);

export const identifyPlant = createAsyncThunk<
  IdentifyResult,
  { image: File; organ: PlantOrgan; language?: string },
  { rejectValue: RejectValue }
>('identification/identify', async ({ image, organ, language }, { rejectWithValue }) => {
  try {
    return await api.identifyPlant(image, organ, language);
  } catch (err) {
    return rejectWithValue(toRejectValue(err));
  }
});

export const selectIdentificationResult = createAsyncThunk<
  IdentificationSelection,
  { requestKey: string; selectedRank: number },
  { rejectValue: RejectValue }
>('identification/select', async ({ requestKey, selectedRank }, { rejectWithValue }) => {
  try {
    return await api.selectIdentificationResult(requestKey, selectedRank);
  } catch (err) {
    return rejectWithValue(toRejectValue(err));
  }
});

export const fetchIdentificationHistory = createAsyncThunk<
  IdentificationHistoryEntry[],
  number | undefined
>('identification/fetchHistory', async (limit) => api.listIdentificationHistory(limit));

const identificationSlice = createSlice({
  name: 'identification',
  initialState,
  reducers: {
    /** Reset the in-flight identification flow (e.g. on dialog close / retry). */
    resetIdentification(state) {
      state.result = null;
      state.selection = null;
      state.error = null;
      state.errorCode = null;
      state.identifying = false;
      state.selecting = false;
    },
    clearIdentificationError(state) {
      state.error = null;
      state.errorCode = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // ── status ──
      .addCase(fetchIdentificationStatus.pending, (state) => {
        state.statusLoading = true;
      })
      .addCase(fetchIdentificationStatus.fulfilled, (state, action) => {
        state.statusLoading = false;
        state.status = action.payload;
      })
      .addCase(fetchIdentificationStatus.rejected, (state) => {
        state.statusLoading = false;
        // Treat an unreachable status endpoint as "unavailable" — never block UI.
        state.status = {
          available: false,
          primary_adapter: '',
          active_adapter: null,
          supports_health: false,
          adapters: {},
        };
      })
      // ── identify ──
      .addCase(identifyPlant.pending, (state) => {
        state.identifying = true;
        state.error = null;
        state.errorCode = null;
        state.result = null;
        state.selection = null;
      })
      .addCase(identifyPlant.fulfilled, (state, action) => {
        state.identifying = false;
        state.result = action.payload;
      })
      .addCase(identifyPlant.rejected, (state, action) => {
        state.identifying = false;
        state.error = action.payload?.message ?? action.error.message ?? 'Identification failed';
        state.errorCode = action.payload?.code ?? null;
      })
      // ── select ──
      .addCase(selectIdentificationResult.pending, (state) => {
        state.selecting = true;
        state.error = null;
        state.errorCode = null;
      })
      .addCase(selectIdentificationResult.fulfilled, (state, action) => {
        state.selecting = false;
        state.selection = action.payload;
      })
      .addCase(selectIdentificationResult.rejected, (state, action) => {
        state.selecting = false;
        state.error = action.payload?.message ?? action.error.message ?? 'Selection failed';
        state.errorCode = action.payload?.code ?? null;
      })
      // ── history ──
      .addCase(fetchIdentificationHistory.pending, (state) => {
        state.historyLoading = true;
      })
      .addCase(fetchIdentificationHistory.fulfilled, (state, action) => {
        state.historyLoading = false;
        state.history = action.payload;
      })
      .addCase(fetchIdentificationHistory.rejected, (state) => {
        state.historyLoading = false;
      });
  },
});

export const { resetIdentification, clearIdentificationError } = identificationSlice.actions;
export default identificationSlice.reducer;
