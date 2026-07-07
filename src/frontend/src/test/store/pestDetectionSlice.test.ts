import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { setActiveTenantSlug } from '@/api/client';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  detectPestsGlobal,
  detectPests,
  fetchPestDetectionStatus,
  fetchPestDetectionHistory,
  submitPestFeedback,
  createInspectionFromDetection,
  resetPestDetection,
  clearPestDetectionError,
} from '@/store/slices/pestDetectionSlice';

/** REQ-044 §7 — the plant-agnostic detect thunk drives the shared result state. */

function makeStore() {
  return configureStore({ reducer: { pestDetection: reducer } });
}

const DETECT_URL = '/api/v1/t/t1/pests/detect';
const DETECT_PLANT_URL = '/api/v1/t/t1/pests/plants/plant-1/detect';
const STATUS_URL = '/api/v1/t/t1/pests/status';
const HISTORY_URL = '/api/v1/t/t1/pests/plants/plant-1/history';
const FEEDBACK_URL = '/api/v1/t/t1/pests/detections/pestdet_1/feedback';
const INSPECTION_URL = '/api/v1/t/t1/pests/detections/pestdet_1/create-inspection';

/** Full error envelope so the client interceptor builds a typed ApiError. */
function errorEnvelope(code: string, message: string, status: number) {
  return HttpResponse.json(
    {
      error_id: 'e1',
      error_code: code,
      message,
      details: [],
      timestamp: '',
      path: '/x',
      method: 'POST',
    },
    { status },
  );
}

const jpg = () => new File([new Uint8Array([1])], 'p.jpg', { type: 'image/jpeg' });

beforeEach(() => {
  setActiveTenantSlug('t1');
});

const RESULT = {
  key: 'pestdet_1',
  plant_instance_key: null,
  source: 'local_symptom',
  adapter_key: 'local_pest_symptom',
  is_confident: true,
  trigger: 'user_photo',
  findings: [],
  tiles_processed: 4,
  suggested_next_step: 'none' as const,
  image_hash: 'sha256:abc',
  disclaimer: 'Nur eine Einschätzung.',
  created_at: null,
};

describe('pestDetectionSlice — detectPestsGlobal', () => {
  it('posts to the plant-agnostic endpoint and stores the result', async () => {
    let calledUrl = '';
    server.use(
      http.post(DETECT_URL, ({ request }) => {
        calledUrl = new URL(request.url).pathname;
        return HttpResponse.json(RESULT);
      }),
    );
    const store = makeStore();
    const file = new File([new Uint8Array([1])], 'p.jpg', { type: 'image/jpeg' });
    await store.dispatch(detectPestsGlobal({ image: file }));

    expect(calledUrl).toBe(DETECT_URL);
    const state = store.getState().pestDetection;
    expect(state.detecting).toBe(false);
    expect(state.result?.key).toBe('pestdet_1');
    expect(state.result?.plant_instance_key).toBeNull();
  });

  it('sets the detecting flag while in flight and clears a previous result', () => {
    const store = makeStore();
    store.dispatch({ type: detectPestsGlobal.pending.type });
    const state = store.getState().pestDetection;
    expect(state.detecting).toBe(true);
    expect(state.result).toBeNull();
    expect(state.error).toBeNull();
  });

  it('surfaces a translated error message on rejection', async () => {
    server.use(http.post(DETECT_URL, () => HttpResponse.json({ detail: 'boom' }, { status: 500 })));
    const store = makeStore();
    const file = new File([new Uint8Array([1])], 'p.jpg', { type: 'image/jpeg' });
    await store.dispatch(detectPestsGlobal({ image: file }));
    const state = store.getState().pestDetection;
    expect(state.detecting).toBe(false);
    expect(state.error).toBeTruthy();
  });
});

describe('pestDetectionSlice — reducers & actions', () => {
  it('starts from the empty initial state', () => {
    const state = reducer(undefined, { type: '@@INIT' });
    expect(state).toMatchObject({
      status: null,
      statusLoading: false,
      result: null,
      detecting: false,
      history: [],
      historyLoading: false,
      error: null,
      errorCode: null,
    });
  });

  it('resetPestDetection clears the in-flight detection flow', () => {
    const dirty = {
      ...reducer(undefined, { type: '@@INIT' }),
      result: RESULT,
      error: 'x',
      errorCode: 'CONSENT_REQUIRED',
      detecting: true,
    };
    const state = reducer(dirty, resetPestDetection());
    expect(state.result).toBeNull();
    expect(state.error).toBeNull();
    expect(state.errorCode).toBeNull();
    expect(state.detecting).toBe(false);
  });

  it('clearPestDetectionError clears only the error fields', () => {
    const dirty = {
      ...reducer(undefined, { type: '@@INIT' }),
      result: RESULT,
      error: 'x',
      errorCode: 'FEATURE_NOT_CONFIGURED',
    };
    const state = reducer(dirty, clearPestDetectionError());
    expect(state.error).toBeNull();
    expect(state.errorCode).toBeNull();
    expect(state.result).toEqual(RESULT);
  });

  it('detectPests pending sets detecting and clears prior error/result', () => {
    const state = reducer(
      { ...reducer(undefined, { type: '@@INIT' }), error: 'old', result: RESULT },
      { type: detectPests.pending.type },
    );
    expect(state.detecting).toBe(true);
    expect(state.error).toBeNull();
    expect(state.result).toBeNull();
  });

  it('detectPests rejected falls back to action.error.message when no payload', () => {
    const state = reducer(undefined, {
      type: detectPests.rejected.type,
      payload: undefined,
      error: { message: 'thrown thunk failure' },
    });
    expect(state.error).toBe('thrown thunk failure');
    expect(state.errorCode).toBeNull();
    expect(state.detecting).toBe(false);
  });

  it('detectPests rejected falls back to the literal message when nothing is present', () => {
    const state = reducer(undefined, {
      type: detectPests.rejected.type,
      payload: undefined,
      error: {},
    });
    expect(state.error).toBe('Detection failed');
  });
});

describe('pestDetectionSlice — fetchPestDetectionStatus', () => {
  const STATUS_OK = {
    available: true,
    feature_enabled: true,
    primary_adapter: 'local_pest_symptom',
    active_adapter: 'local_pest_symptom',
    adapters: {},
  };

  it('stores the payload on fulfilled', async () => {
    server.use(http.get(STATUS_URL, () => HttpResponse.json(STATUS_OK)));
    const store = makeStore();
    await store.dispatch(fetchPestDetectionStatus());
    const state = store.getState().pestDetection;
    expect(state.statusLoading).toBe(false);
    expect(state.status).toEqual(STATUS_OK);
  });

  it('synthesises an "unavailable" status when the endpoint is unreachable', async () => {
    server.use(http.get(STATUS_URL, () => HttpResponse.json({ detail: 'nope' }, { status: 500 })));
    const store = makeStore();
    await store.dispatch(fetchPestDetectionStatus());
    const state = store.getState().pestDetection;
    expect(state.statusLoading).toBe(false);
    expect(state.status).toEqual({
      available: false,
      feature_enabled: false,
      primary_adapter: '',
      active_adapter: null,
      adapters: {},
    });
  });

  it('sets statusLoading while pending', () => {
    const state = reducer(undefined, { type: fetchPestDetectionStatus.pending.type });
    expect(state.statusLoading).toBe(true);
  });
});

describe('pestDetectionSlice — detectPests (plant-scoped) + error mapping', () => {
  it('stores the result on fulfilled', async () => {
    server.use(http.post(DETECT_PLANT_URL, () => HttpResponse.json(RESULT)));
    const store = makeStore();
    await store.dispatch(detectPests({ plantKey: 'plant-1', image: jpg() }));
    const state = store.getState().pestDetection;
    expect(state.detecting).toBe(false);
    expect(state.result?.key).toBe('pestdet_1');
  });

  it.each([
    ['CONSENT_REQUIRED', 403],
    ['FEATURE_NOT_CONFIGURED', 404],
    ['PAYLOAD_TOO_LARGE', 413],
    ['UNSUPPORTED_MEDIA_TYPE', 415],
  ])('maps the %s ApiError to a translated message + code', async (code, status) => {
    server.use(http.post(DETECT_PLANT_URL, () => errorEnvelope(code, 'boom', status)));
    const store = makeStore();
    await store.dispatch(detectPests({ plantKey: 'plant-1', image: jpg(), language: 'de' }));
    const state = store.getState().pestDetection;
    expect(state.errorCode).toBe(code);
    expect(state.error).toBeTruthy();
    // Mapped branches never echo the raw backend message.
    expect(state.error).not.toBe('boom');
    expect(state.detecting).toBe(false);
  });

  it('falls back to the API message for an unmapped error code', async () => {
    server.use(http.post(DETECT_PLANT_URL, () => errorEnvelope('SOMETHING_ELSE', 'specific msg', 400)));
    const store = makeStore();
    await store.dispatch(detectPests({ plantKey: 'plant-1', image: jpg() }));
    const state = store.getState().pestDetection;
    expect(state.error).toBe('specific msg');
    expect(state.errorCode).toBe('SOMETHING_ELSE');
  });

  it('falls back to the generic server message when an ApiError carries no message', async () => {
    server.use(http.post(DETECT_PLANT_URL, () => errorEnvelope('WEIRD', '', 400)));
    const store = makeStore();
    await store.dispatch(detectPests({ plantKey: 'plant-1', image: jpg() }));
    const state = store.getState().pestDetection;
    expect(state.error).toBeTruthy();
    expect(state.errorCode).toBe('WEIRD');
  });

  it('maps a non-ApiError network failure to a null code', async () => {
    server.use(http.post(DETECT_PLANT_URL, () => HttpResponse.error()));
    const store = makeStore();
    await store.dispatch(detectPests({ plantKey: 'plant-1', image: jpg() }));
    const state = store.getState().pestDetection;
    expect(state.error).toBeTruthy();
    expect(state.errorCode).toBeNull();
  });
});

describe('pestDetectionSlice — history', () => {
  const HISTORY = [{ ...RESULT, key: 'pestdet_hist' }];

  it('stores history entries on fulfilled', async () => {
    server.use(http.get(HISTORY_URL, () => HttpResponse.json(HISTORY)));
    const store = makeStore();
    await store.dispatch(fetchPestDetectionHistory({ plantKey: 'plant-1', limit: 10 }));
    const state = store.getState().pestDetection;
    expect(state.historyLoading).toBe(false);
    expect(state.history).toHaveLength(1);
    expect(state.history[0].key).toBe('pestdet_hist');
  });

  it('clears the loading flag when history loading fails', async () => {
    server.use(http.get(HISTORY_URL, () => HttpResponse.json({ detail: 'x' }, { status: 500 })));
    const store = makeStore();
    await store.dispatch(fetchPestDetectionHistory({ plantKey: 'plant-1' }));
    expect(store.getState().pestDetection.historyLoading).toBe(false);
  });

  it('sets historyLoading while pending', () => {
    const state = reducer(undefined, { type: fetchPestDetectionHistory.pending.type });
    expect(state.historyLoading).toBe(true);
  });
});

describe('pestDetectionSlice — submitPestFeedback', () => {
  it('replaces the current result when the feedback key matches', async () => {
    const updated = { ...RESULT, disclaimer: 'Bestätigt.' };
    server.use(http.post(FEEDBACK_URL, () => HttpResponse.json(updated)));
    const store = makeStore();
    // Seed the in-flight result.
    store.dispatch({ type: detectPests.fulfilled.type, payload: RESULT });
    await store.dispatch(
      submitPestFeedback({ detectionKey: 'pestdet_1', findingLabel: 'aphids', confirmed: true }),
    );
    expect(store.getState().pestDetection.result?.disclaimer).toBe('Bestätigt.');
  });

  it('leaves the result untouched when the feedback key does not match', async () => {
    const other = { ...RESULT, key: 'other', disclaimer: 'Andere.' };
    server.use(http.post(FEEDBACK_URL, () => HttpResponse.json(other)));
    const store = makeStore();
    store.dispatch({ type: detectPests.fulfilled.type, payload: RESULT });
    await store.dispatch(
      submitPestFeedback({
        detectionKey: 'pestdet_1',
        findingLabel: 'aphids',
        confirmed: false,
        actualLabel: 'thrips',
        wasBeneficial: true,
      }),
    );
    // The stored result keeps its original key/disclaimer.
    expect(store.getState().pestDetection.result?.key).toBe('pestdet_1');
    expect(store.getState().pestDetection.result?.disclaimer).toBe(RESULT.disclaimer);
  });
});

describe('pestDetectionSlice — createInspectionFromDetection', () => {
  it('resolves with the created inspection key', async () => {
    server.use(http.post(INSPECTION_URL, () => HttpResponse.json({ inspection_key: 'insp_1' })));
    const store = makeStore();
    const res = await store.dispatch(
      createInspectionFromDetection({ detectionKey: 'pestdet_1', plantKey: 'plant-1' }),
    );
    expect(res.type).toBe(createInspectionFromDetection.fulfilled.type);
    expect(res.payload).toEqual({ inspectionKey: 'insp_1' });
  });

  it('rejects with a translated value on failure', async () => {
    server.use(http.post(INSPECTION_URL, () => errorEnvelope('ENTITY_NOT_FOUND', 'missing', 404)));
    const store = makeStore();
    const res = await store.dispatch(
      createInspectionFromDetection({ detectionKey: 'pestdet_1', plantKey: 'plant-1' }),
    );
    expect(res.type).toBe(createInspectionFromDetection.rejected.type);
  });
});
