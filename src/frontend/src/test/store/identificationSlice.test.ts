import { describe, it, expect, beforeEach, vi } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  resetIdentification,
  clearIdentificationError,
  fetchIdentificationStatus,
  identifyPlant,
  selectIdentificationResult,
  fetchIdentificationHistory,
} from '@/store/slices/identificationSlice';
import { ApiError } from '@/api/errors';
import * as api from '@/api/endpoints/identification';
import type { ApiErrorResponse } from '@/api/types';

/**
 * REQ-029 / REQ-029-A — identification slice unit tests.
 *
 * The endpoint module is mocked so the thunks resolve/reject deterministically
 * without HTTP. The focus is the error-mapping matrix in toRejectValue (each
 * errorCode branch) plus the pending/fulfilled/rejected reducers and the
 * reset/clear actions.
 */

vi.mock('@/api/endpoints/identification');

const mockedApi = vi.mocked(api);

function makeStore() {
  return configureStore({ reducer: { identification: reducer } });
}

function apiError(code: string, message = 'boom', status = 400): ApiError {
  const body: ApiErrorResponse = {
    error_id: 'e1',
    error_code: code,
    message,
    details: [],
    timestamp: '',
    path: '/x',
    method: 'POST',
  };
  return new ApiError(body, status);
}

const STATUS_OK = {
  available: true,
  primary_adapter: 'plantnet',
  active_adapter: 'plantnet',
  supports_health: false,
  adapters: {},
};

const RESULT = {
  request_key: 'ident_1',
  is_plant: true,
  message: null,
  suggestions: [],
};

const SELECTION = {
  request_key: 'ident_1',
  selected_rank: 1,
  matched_species_key: 'sp_1',
  scientific_name: 'Monstera deliciosa',
  common_names: [],
  family: 'Araceae',
  genus: 'Monstera',
  gbif_id: null,
  confidence: 0.9,
  species_in_database: true,
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('identificationSlice — reducers', () => {
  it('starts from the empty initial state', () => {
    const state = reducer(undefined, { type: '@@INIT' });
    expect(state).toMatchObject({
      status: null,
      result: null,
      selection: null,
      history: [],
      error: null,
      errorCode: null,
      identifying: false,
    });
  });

  it('resetIdentification clears the in-flight flow', () => {
    const dirty = {
      ...reducer(undefined, { type: '@@INIT' }),
      result: RESULT,
      selection: SELECTION,
      error: 'x',
      errorCode: 'RATE_LIMIT_EXCEEDED',
      identifying: true,
      selecting: true,
    };
    const state = reducer(dirty, resetIdentification());
    expect(state.result).toBeNull();
    expect(state.selection).toBeNull();
    expect(state.error).toBeNull();
    expect(state.errorCode).toBeNull();
    expect(state.identifying).toBe(false);
    expect(state.selecting).toBe(false);
  });

  it('clearIdentificationError clears only the error fields', () => {
    const dirty = {
      ...reducer(undefined, { type: '@@INIT' }),
      error: 'x',
      errorCode: 'CONSENT_REQUIRED',
      result: RESULT,
    };
    const state = reducer(dirty, clearIdentificationError());
    expect(state.error).toBeNull();
    expect(state.errorCode).toBeNull();
    // result is preserved
    expect(state.result).toEqual(RESULT);
  });
});

describe('identificationSlice — status thunk', () => {
  it('stores the payload on fulfilled', async () => {
    mockedApi.getIdentificationStatus.mockResolvedValue(STATUS_OK);
    const store = makeStore();
    await store.dispatch(fetchIdentificationStatus());
    expect(store.getState().identification.status).toEqual(STATUS_OK);
    expect(store.getState().identification.statusLoading).toBe(false);
  });

  it('synthesises an "unavailable" status when the endpoint is unreachable', async () => {
    mockedApi.getIdentificationStatus.mockRejectedValue(new Error('network'));
    const store = makeStore();
    await store.dispatch(fetchIdentificationStatus());
    const { status, statusLoading } = store.getState().identification;
    expect(statusLoading).toBe(false);
    expect(status).toEqual({
      available: false,
      primary_adapter: '',
      active_adapter: null,
      supports_health: false,
      adapters: {},
    });
  });
});

describe('identificationSlice — identify thunk + error mapping', () => {
  it('stores the result on fulfilled and clears prior error', async () => {
    mockedApi.identifyPlant.mockResolvedValue(RESULT);
    const store = makeStore();
    await store.dispatch(
      identifyPlant({ image: new File([], 'p.jpg'), organ: 'auto' }),
    );
    const state = store.getState().identification;
    expect(state.result).toEqual(RESULT);
    expect(state.identifying).toBe(false);
    expect(state.error).toBeNull();
  });

  it.each([
    ['CONSENT_REQUIRED'],
    ['FEATURE_NOT_CONFIGURED'],
    ['RATE_LIMIT_EXCEEDED'],
    ['PAYLOAD_TOO_LARGE'],
    ['UNSUPPORTED_MEDIA_TYPE'],
  ])('maps the %s ApiError to a translated message + code', async (code) => {
    mockedApi.identifyPlant.mockRejectedValue(apiError(code));
    const store = makeStore();
    await store.dispatch(
      identifyPlant({ image: new File([], 'p.jpg'), organ: 'leaf', language: 'de' }),
    );
    const state = store.getState().identification;
    expect(state.errorCode).toBe(code);
    expect(typeof state.error).toBe('string');
    expect(state.error).toBeTruthy();
    // The translated branch never echoes the raw "boom" backend message.
    expect(state.error).not.toBe('boom');
    expect(state.identifying).toBe(false);
  });

  it('falls back to the API message for an unmapped error code', async () => {
    mockedApi.identifyPlant.mockRejectedValue(apiError('SOMETHING_ELSE', 'specific msg'));
    const store = makeStore();
    await store.dispatch(
      identifyPlant({ image: new File([], 'p.jpg'), organ: 'auto' }),
    );
    const state = store.getState().identification;
    expect(state.error).toBe('specific msg');
    expect(state.errorCode).toBe('SOMETHING_ELSE');
  });

  it('falls back to the generic server message when an ApiError carries no message', async () => {
    mockedApi.identifyPlant.mockRejectedValue(apiError('WEIRD', ''));
    const store = makeStore();
    await store.dispatch(
      identifyPlant({ image: new File([], 'p.jpg'), organ: 'auto' }),
    );
    const state = store.getState().identification;
    expect(state.error).toBeTruthy();
    expect(state.errorCode).toBe('WEIRD');
  });

  it('maps a plain Error to its message with a null code', async () => {
    mockedApi.identifyPlant.mockRejectedValue(new Error('canvas exploded'));
    const store = makeStore();
    await store.dispatch(
      identifyPlant({ image: new File([], 'p.jpg'), organ: 'auto' }),
    );
    const state = store.getState().identification;
    expect(state.error).toBe('canvas exploded');
    expect(state.errorCode).toBeNull();
  });

  it('maps a message-less Error to the generic unknown message', async () => {
    mockedApi.identifyPlant.mockRejectedValue(new Error(''));
    const store = makeStore();
    await store.dispatch(
      identifyPlant({ image: new File([], 'p.jpg'), organ: 'auto' }),
    );
    const state = store.getState().identification;
    expect(state.error).toBeTruthy();
    expect(state.errorCode).toBeNull();
  });

  it('maps a non-Error thrown value to the generic unknown message', async () => {
    mockedApi.identifyPlant.mockRejectedValue('a bare string');
    const store = makeStore();
    await store.dispatch(
      identifyPlant({ image: new File([], 'p.jpg'), organ: 'auto' }),
    );
    const state = store.getState().identification;
    expect(state.error).toBeTruthy();
    expect(state.errorCode).toBeNull();
  });

  it('sets identifying=true while pending', () => {
    const state = reducer(undefined, { type: identifyPlant.pending.type });
    expect(state.identifying).toBe(true);
    expect(state.result).toBeNull();
  });

  it('falls back to action.error.message when no rejectWithValue payload is present', () => {
    // Simulate a rejected action that bypassed rejectWithValue (thrown thunk).
    const state = reducer(undefined, {
      type: identifyPlant.rejected.type,
      payload: undefined,
      error: { message: 'thrown thunk failure' },
    });
    expect(state.error).toBe('thrown thunk failure');
    expect(state.errorCode).toBeNull();
    expect(state.identifying).toBe(false);
  });

  it('falls back to the literal message when neither payload nor error message exist', () => {
    const state = reducer(undefined, {
      type: identifyPlant.rejected.type,
      payload: undefined,
      error: {},
    });
    expect(state.error).toBe('Identification failed');
  });
});

describe('identificationSlice — select thunk', () => {
  it('stores the selection on fulfilled', async () => {
    mockedApi.selectIdentificationResult.mockResolvedValue(SELECTION);
    const store = makeStore();
    await store.dispatch(
      selectIdentificationResult({ requestKey: 'ident_1', selectedRank: 1 }),
    );
    const state = store.getState().identification;
    expect(state.selection).toEqual(SELECTION);
    expect(state.selecting).toBe(false);
  });

  it('records the error on a rejected selection', async () => {
    mockedApi.selectIdentificationResult.mockRejectedValue(apiError('RATE_LIMIT_EXCEEDED'));
    const store = makeStore();
    await store.dispatch(
      selectIdentificationResult({ requestKey: 'ident_1', selectedRank: 2 }),
    );
    const state = store.getState().identification;
    expect(state.selecting).toBe(false);
    expect(state.errorCode).toBe('RATE_LIMIT_EXCEEDED');
    expect(state.error).toBeTruthy();
  });

  it('sets selecting=true while pending', () => {
    const state = reducer(undefined, { type: selectIdentificationResult.pending.type });
    expect(state.selecting).toBe(true);
  });

  it('falls back to action.error.message on a thrown select rejection', () => {
    const state = reducer(undefined, {
      type: selectIdentificationResult.rejected.type,
      payload: undefined,
      error: { message: 'select threw' },
    });
    expect(state.error).toBe('select threw');
    expect(state.selecting).toBe(false);
  });

  it('falls back to the literal message on a payload-less select rejection', () => {
    const state = reducer(undefined, {
      type: selectIdentificationResult.rejected.type,
      payload: undefined,
      error: {},
    });
    expect(state.error).toBe('Selection failed');
  });
});

describe('identificationSlice — history thunk', () => {
  it('stores history entries on fulfilled', async () => {
    const history = [
      {
        key: 'h1',
        adapter_key: 'plantnet',
        request_type: 'identify',
        image_organ: 'auto',
        status: 'completed',
        created_at: '2026-06-15T00:00:00Z',
        selected_result_rank: 1,
        results: [],
        plant_instance_key: null,
      },
    ];
    mockedApi.listIdentificationHistory.mockResolvedValue(history);
    const store = makeStore();
    await store.dispatch(fetchIdentificationHistory(20));
    const state = store.getState().identification;
    expect(state.history).toEqual(history);
    expect(state.historyLoading).toBe(false);
  });

  it('clears the loading flag when history loading fails', async () => {
    mockedApi.listIdentificationHistory.mockRejectedValue(new Error('nope'));
    const store = makeStore();
    await store.dispatch(fetchIdentificationHistory(undefined));
    expect(store.getState().identification.historyLoading).toBe(false);
  });

  it('sets historyLoading=true while pending', () => {
    const state = reducer(undefined, { type: fetchIdentificationHistory.pending.type });
    expect(state.historyLoading).toBe(true);
  });
});
