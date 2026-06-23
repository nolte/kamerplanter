import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { setActiveTenantSlug } from '@/api/client';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  detectPestsGlobal,
} from '@/store/slices/pestDetectionSlice';

/** REQ-044 §7 — the plant-agnostic detect thunk drives the shared result state. */

function makeStore() {
  return configureStore({ reducer: { pestDetection: reducer } });
}

const DETECT_URL = '/api/v1/t/t1/pests/detect';

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
  suggested_next_step: 'none',
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
