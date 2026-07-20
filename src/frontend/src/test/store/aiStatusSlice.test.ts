import { describe, it, expect, beforeEach, vi } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, { fetchAiStatus } from '@/store/slices/aiStatusSlice';
import * as ai from '@/api/endpoints/ai';

/**
 * Issue #685 — aiStatus slice unit tests.
 *
 * The endpoint module is mocked so the thunk resolves/rejects deterministically.
 * Covers the unknown→available/unavailable transitions and the fail-safe: an
 * unreachable probe is treated as "unavailable" (the guarded routes 404 when the
 * operator flag is off).
 */

vi.mock('@/api/endpoints/ai');

const mockedApi = vi.mocked(ai);

function makeStore() {
  return configureStore({ reducer: { aiStatus: reducer } });
}

describe('aiStatusSlice', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('starts with unknown availability', () => {
    const store = makeStore();
    expect(store.getState().aiStatus.available).toBeNull();
    expect(store.getState().aiStatus.loading).toBe(false);
  });

  it('sets available=true when the probe reports the feature on', async () => {
    mockedApi.getAiStatus.mockResolvedValue({ available: true });
    const store = makeStore();
    await store.dispatch(fetchAiStatus());
    expect(store.getState().aiStatus.available).toBe(true);
    expect(store.getState().aiStatus.loading).toBe(false);
  });

  it('sets available=false when the probe reports the feature off', async () => {
    mockedApi.getAiStatus.mockResolvedValue({ available: false });
    const store = makeStore();
    await store.dispatch(fetchAiStatus());
    expect(store.getState().aiStatus.available).toBe(false);
  });

  it('leaves availability unknown on probe failure', async () => {
    // /ai/status is ungated and answers 200 in both flag states, so a rejection
    // is transient (network/timeout/5xx) — it must NOT be read as "feature off".
    mockedApi.getAiStatus.mockRejectedValue(new Error('network'));
    const store = makeStore();
    await store.dispatch(fetchAiStatus());
    expect(store.getState().aiStatus.available).toBeNull();
    expect(store.getState().aiStatus.loading).toBe(false);
  });
});
