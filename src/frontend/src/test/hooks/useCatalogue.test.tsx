/**
 * The shared catalogue reader's own contract (#1560, #1568).
 *
 * The page-level cases assert what a user sees. What only this file can ask is
 * the part that has no pixels: does a second consumer render from cache instead
 * of re-requesting, do two consumers mounting in the same tick issue one request
 * between them, and does a retry actually reach the network. All three are the
 * behaviour that justifies replacing nineteen local rebuilds with one hook; an
 * untested one would be nineteen rebuilds again, in a single file.
 */
import type { ReactNode } from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { combineReducers, configureStore } from '@reduxjs/toolkit';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { WAIT_BUDGET } from '../waitBudget';
import { useCatalogue } from '@/hooks/useCatalogue';
import botanicalFamiliesReducer from '@/store/slices/botanicalFamiliesSlice';

const FAMILIES_URL = '/api/v1/botanical-families';

function makeFamily(index: number) {
  return {
    key: `fam-${index}`,
    name: `Familie ${index}`,
    typical_nutrient_demand: 'medium',
    common_pests: [],
    rotation_category: 'fruit',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  };
}

function makeWrapper() {
  const store = configureStore({
    reducer: combineReducers({ botanicalFamilies: botanicalFamiliesReducer }),
  });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <Provider store={store}>{children}</Provider>
  );
  return { store, wrapper };
}

describe('useCatalogue', () => {
  let requests: number;

  beforeEach(() => {
    requests = 0;
  });

  function serveFamilies(rows = [makeFamily(0)]) {
    server.use(
      http.get(FAMILIES_URL, () => {
        requests += 1;
        return HttpResponse.json(rows);
      }),
    );
  }

  it('loads the catalogue once and serves the second consumer from the store', async () => {
    serveFamilies();
    const { wrapper } = makeWrapper();

    const first = renderHook(() => useCatalogue('botanicalFamilies'), { wrapper });
    await waitFor(() => expect(first.result.current.status).toBe('ready'), {
      timeout: WAIT_BUDGET,
    });
    expect(requests).toBe(1);

    const second = renderHook(() => useCatalogue('botanicalFamilies'), { wrapper });
    await waitFor(() => expect(second.result.current.status).toBe('ready'), {
      timeout: WAIT_BUDGET,
    });

    // The claim: no second request. A hook that refetched per consumer would
    // reintroduce the per-picker load this replaced, just behind one import.
    expect(requests).toBe(1);
    expect(second.result.current.items).toHaveLength(1);
  });

  it('issues one request for two consumers that mount in the same tick', async () => {
    serveFamilies();
    const { wrapper } = makeWrapper();

    const both = renderHook(
      () => ({
        a: useCatalogue('botanicalFamilies'),
        b: useCatalogue('botanicalFamilies'),
      }),
      { wrapper },
    );

    await waitFor(
      () => {
        expect(both.result.current.a.status).toBe('ready');
        expect(both.result.current.b.status).toBe('ready');
      },
      { timeout: WAIT_BUDGET },
    );
    // Neither sees an empty store when it starts, so without the in-flight
    // registry this would be two.
    expect(requests).toBe(1);
  });

  it('separates a failed load from an empty catalogue', async () => {
    server.use(
      http.get(FAMILIES_URL, () => {
        requests += 1;
        return new HttpResponse(null, { status: 500 });
      }),
    );
    const { wrapper } = makeWrapper();

    const failed = renderHook(() => useCatalogue('botanicalFamilies'), { wrapper });
    await waitFor(() => expect(failed.result.current.status).toBe('failed'), {
      timeout: WAIT_BUDGET,
    });
    // The distinction the whole issue is about: a failure is never `isEmpty`,
    // however empty `items` happens to be.
    expect(failed.result.current.items).toHaveLength(0);
    expect(failed.result.current.isEmpty).toBe(false);
    expect(failed.result.current.error).toBeTruthy();
  });

  it('reports an empty catalogue as ready-and-empty, not as a failure', async () => {
    serveFamilies([]);
    const { wrapper } = makeWrapper();

    const empty = renderHook(() => useCatalogue('botanicalFamilies'), { wrapper });
    await waitFor(() => expect(empty.result.current.status).toBe('ready'), {
      timeout: WAIT_BUDGET,
    });
    expect(empty.result.current.isEmpty).toBe(true);
    expect(empty.result.current.error).toBeNull();
  });

  it('reaches the network again on reload, and stops there', async () => {
    serveFamilies();
    const { wrapper } = makeWrapper();

    const reader = renderHook(() => useCatalogue('botanicalFamilies'), { wrapper });
    await waitFor(() => expect(reader.result.current.status).toBe('ready'), {
      timeout: WAIT_BUDGET,
    });
    expect(requests).toBe(1);

    reader.result.current.reload();
    await waitFor(() => expect(requests).toBe(2), { timeout: WAIT_BUDGET });
    await waitFor(() => expect(reader.result.current.status).toBe('ready'), {
      timeout: WAIT_BUDGET,
    });

    // The counterpart, and the reason this case exists: a reload that leaves the
    // effect thinking a forced attempt is still pending requests forever. Give
    // it room to do so and assert it did not.
    await new Promise((resolve) => setTimeout(resolve, 200));
    expect(requests).toBe(2);
  });

  it('does not request while disabled, and does not claim the catalogue is empty', async () => {
    serveFamilies();
    const { wrapper } = makeWrapper();

    const disabled = renderHook(() => useCatalogue('botanicalFamilies', { enabled: false }), {
      wrapper,
    });
    await new Promise((resolve) => setTimeout(resolve, 200));

    expect(requests).toBe(0);
    // A closed dialog must not render "nothing to pick" for a catalogue nobody
    // asked for yet.
    expect(disabled.result.current.isEmpty).toBe(false);
    expect(disabled.result.current.status).toBe('loading');
  });
});
