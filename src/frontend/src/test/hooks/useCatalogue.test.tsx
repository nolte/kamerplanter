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
import { act, renderHook, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { combineReducers, configureStore } from '@reduxjs/toolkit';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { WAIT_BUDGET } from '../waitBudget';
import { useCatalogue } from '@/hooks/useCatalogue';
import * as speciesApi from '@/api/endpoints/species';
import { setActiveTenantSlug } from '@/api/client';
import speciesReducer from '@/store/slices/speciesSlice';
import botanicalFamiliesReducer from '@/store/slices/botanicalFamiliesSlice';
import activitiesReducer, { fetchActivities } from '@/store/slices/activitiesSlice';

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

function makeActivityRow(index: number) {
  return {
    key: `act-${index}`,
    tenant_key: 't',
    name: `Activity ${index}`,
    name_de: `Aktivität ${index}`,
    description: '',
    description_de: '',
    category: 'pruning',
    stress_level: 'medium',
    skill_level: 'beginner',
    recovery_days_default: 0,
    recovery_days_by_species: {},
    forbidden_phases: [],
    restricted_sub_phases: [],
    tools_required: [],
    estimated_duration_minutes: 1,
    requires_photo: false,
    species_compatible: [],
    is_system: false,
    sort_order: index,
    tags: [],
    created_at: null,
    updated_at: null,
  };
}

function makeWrapper() {
  const store = configureStore({
    reducer: combineReducers({
      botanicalFamilies: botanicalFamiliesReducer,
      activities: activitiesReducer,
      species: speciesReducer,
    }),
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

  it('does not serve a filtered subset another consumer left in the slice', async () => {
    // Found reviewing this hook's own diff, not by the issue. `ActivityListPage`
    // dispatches `fetchActivities({category, scope, species})` into the same
    // slice a picker reads. A cache predicate of "the slice holds rows" would
    // then hand the picker that filtered subset and call it the catalogue —
    // which is the defect this hook exists to close, reintroduced through its
    // own cache. The completeness mark is on the array reference, so the
    // filtered dispatch's replacement array loses it.
    const requested: (string | null)[] = [];
    server.use(
      http.get('/api/v1/activities', ({ request }) => {
        const category = new URL(request.url).searchParams.get('category');
        requested.push(category);
        const rows = [
          { ...makeActivityRow(0), category: 'pruning' },
          { ...makeActivityRow(1), category: 'watering' },
        ];
        return HttpResponse.json(
          category ? rows.filter((row) => row.category === category) : rows,
        );
      }),
    );
    const { store, wrapper } = makeWrapper();

    // A list view narrows the slice to one category, exactly as the real page does.
    await store.dispatch(fetchActivities({ category: 'pruning' }));
    expect(store.getState().activities.items).toHaveLength(1);

    const picker = renderHook(() => useCatalogue('activities'), { wrapper });
    await waitFor(() => expect(picker.result.current.status).toBe('ready'), {
      timeout: WAIT_BUDGET,
    });

    // The assertion that carries the finding: the picker holds both rows, and it
    // reached the server without a filter to get them.
    expect(picker.result.current.items).toHaveLength(2);
    expect(requested).toEqual(['pruning', null]);
  });

  it('drops the cache when the catalogue is written, not only when it is replaced', async () => {
    // SCR-001, and a regression against the state *before* this cache: these
    // dialogs used to reload on every open. None of the six detail pages
    // refreshes its list slice after a write — `SpeciesDetailPage` dispatches
    // `fetchSpecies(key)`, whose `fetchOne.fulfilled` writes only `currentField`
    // — so a mark taken before the write stayed valid and the picker kept
    // offering the old name, or a deleted row, until the tab was reloaded.
    //
    // The acceptance signal, run rather than described: load the catalogue,
    // update a row the way the page does, mount a fresh picker, and require a
    // second request carrying the new name.
    let version = 'Tomate alt';
    let requests = 0;
    server.use(
      http.get('/api/v1/species', () => {
        requests += 1;
        return HttpResponse.json({
          items: [{ key: 'sp-1', scientific_name: version, common_names: [] }],
          total: 1,
          offset: 0,
          limit: 200,
        });
      }),
      http.put('/api/v1/species/sp-1', () => {
        version = 'Tomate neu';
        return HttpResponse.json({ key: 'sp-1', scientific_name: version, common_names: [] });
      }),
    );
    const { wrapper } = makeWrapper();

    const first = renderHook(() => useCatalogue('species'), { wrapper });
    await waitFor(() => expect(first.result.current.status).toBe('ready'), {
      timeout: WAIT_BUDGET,
    });
    expect(requests).toBe(1);
    expect(first.result.current.items[0].scientific_name).toBe('Tomate alt');
    first.unmount();

    // The write goes through the endpoint module, which is the only thing the
    // page and this test have in common — no page calls an invalidation helper.
    await speciesApi.updateSpecies('sp-1', {
      scientific_name: 'Tomate neu',
    } as never);

    const second = renderHook(() => useCatalogue('species'), { wrapper });
    await waitFor(() => expect(second.result.current.status).toBe('ready'), {
      timeout: WAIT_BUDGET,
    });

    // The assertion that carries the finding. Against the array-only mark this
    // was 1 request and 'Tomate alt'.
    expect(requests).toBe(2);
    expect(second.result.current.items[0].scientific_name).toBe('Tomate neu');
  });

  it('drops the cache on a delete, so a removed row stops being offered', async () => {
    // The worse half of SCR-001: every one of the six detail pages only
    // navigates away after a delete, so nothing at all touched the slice.
    let rows = [
      { key: 'sp-1', scientific_name: 'Tomate', common_names: [] },
      { key: 'sp-2', scientific_name: 'Gurke', common_names: [] },
    ];
    server.use(
      http.get('/api/v1/species', () =>
        HttpResponse.json({ items: rows, total: rows.length, offset: 0, limit: 200 }),
      ),
      http.delete('/api/v1/species/sp-2', () => {
        rows = rows.filter((row) => row.key !== 'sp-2');
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const { wrapper } = makeWrapper();

    const first = renderHook(() => useCatalogue('species'), { wrapper });
    await waitFor(() => expect(first.result.current.items).toHaveLength(2), {
      timeout: WAIT_BUDGET,
    });
    first.unmount();

    await speciesApi.deleteSpecies('sp-2');

    const second = renderHook(() => useCatalogue('species'), { wrapper });
    await waitFor(() => expect(second.result.current.status).toBe('ready'), {
      timeout: WAIT_BUDGET,
    });
    expect(second.result.current.items.map((row) => row.key)).toEqual(['sp-1']);
  });

  it('never reports ready over rows that are not the catalogue', async () => {
    // SCR-002. `items` comes from the store and `status` from this hook, so a
    // filtered dispatch landing while a consumer is mounted could produce
    // `ready` over a subset within one render — the pair the contract rules out.
    // One handler for both shapes, so the unfiltered reload stays
    // distinguishable from the subset — an override that answered every request
    // with one row would have made the recovery look like the defect.
    //
    // The *second* unfiltered request is gated. Without that gate the reader
    // recovers inside the same `act()` as the dispatch and the subset is never
    // in the store at a moment this test can read: the first attempt asserted a
    // length of 1 and measured 2, because the repair had already run. A window
    // that closes before the assertion is a green test that checked nothing.
    let releaseReload!: () => void;
    const reloadArrives = new Promise<void>((resolve) => {
      releaseReload = resolve;
    });
    let unfilteredRequests = 0;
    const rows = [
      { ...makeActivityRow(0), category: 'pruning' },
      { ...makeActivityRow(1), category: 'watering' },
    ];
    server.use(
      http.get('/api/v1/activities', async ({ request }) => {
        const category = new URL(request.url).searchParams.get('category');
        if (category) return HttpResponse.json(rows.filter((row) => row.category === category));
        unfilteredRequests += 1;
        if (unfilteredRequests > 1) await reloadArrives;
        return HttpResponse.json(rows);
      }),
    );
    const { store, wrapper } = makeWrapper();

    const reader = renderHook(() => useCatalogue('activities'), { wrapper });
    await waitFor(() => expect(reader.result.current.items).toHaveLength(2), {
      timeout: WAIT_BUDGET,
    });
    expect(reader.result.current.status).toBe('ready');

    // Falsifying order, deliberately the opposite of the sibling case: the
    // consumer is already `ready` when the subset lands underneath it (S3).
    await act(async () => {
      await store.dispatch(fetchActivities({ category: 'pruning' }));
    });

    // The assertion that carries SCR-002, read in the very render the subset is
    // in the store: whatever this reports, `ready` over one row is the pair the
    // contract excludes.
    expect(store.getState().activities.items).toHaveLength(1);
    expect(
      reader.result.current.status === 'ready' && reader.result.current.items.length === 1,
    ).toBe(false);

    // …and it recovers on its own rather than sitting on the subset.
    releaseReload();
    await waitFor(() => expect(reader.result.current.items).toHaveLength(2), {
      timeout: WAIT_BUDGET,
    });
    expect(reader.result.current.status).toBe('ready');
    expect(unfilteredRequests).toBe(2);
  });

  it('does not report ready over a subset while disabled, when no effect can correct it', async () => {
    // The half of SCR-002 that the case above does *not* reach, measured rather
    // than assumed: with the reload gated, the sibling case still passes when
    // the coercion is reverted, because the effect has already set `loading` by
    // the time it asserts. So the coercion was inert there.
    //
    // It is not inert here. A closed dialog has `enabled: false`, the effect
    // returns early (`useCatalogue.ts`, first line of the effect), and nothing
    // can move the internal state off `ready`. Only deriving the reported status
    // from the same fact as the rows keeps the pair honest.
    const rows = [
      { ...makeActivityRow(0), category: 'pruning' },
      { ...makeActivityRow(1), category: 'watering' },
    ];
    server.use(
      http.get('/api/v1/activities', ({ request }) => {
        const category = new URL(request.url).searchParams.get('category');
        return HttpResponse.json(
          category ? rows.filter((row) => row.category === category) : rows,
        );
      }),
    );
    const { store, wrapper } = makeWrapper();

    const reader = renderHook(
      ({ enabled }: { enabled: boolean }) => useCatalogue('activities', { enabled }),
      { wrapper, initialProps: { enabled: true } },
    );
    await waitFor(() => expect(reader.result.current.items).toHaveLength(2), {
      timeout: WAIT_BUDGET,
    });
    expect(reader.result.current.status).toBe('ready');

    // The dialog closes; from here the effect cannot run again.
    reader.rerender({ enabled: false });
    await act(async () => {
      await store.dispatch(fetchActivities({ category: 'pruning' }));
    });

    expect(store.getState().activities.items).toHaveLength(1);
    expect(reader.result.current.items).toHaveLength(1);
    // The assertion the coercion is the only thing that can satisfy.
    expect(reader.result.current.status).not.toBe('ready');
    expect(reader.result.current.isEmpty).toBe(false);
  });

  it('drops the cache when the active tenant changes without a page reload', async () => {
    // SCR-008. `TenantSwitcher` reloads the document, so its caches die with the
    // heap — but the stale-slug recovery path in `store.ts` does not reload: it
    // clears the tenant, reloads the memberships and re-picks a *different* one
    // in place. Measured reachable: it fires on the backend refusing the
    // persisted tenant, which an admin revoking a membership produces.
    //
    // Catalogues are a global/tenant union (#324), so a mark taken under the old
    // tenant would hand its rows to the new one as a complete catalogue.
    let tenantRows = [{ key: 'sp-a', scientific_name: 'Nur in Tenant A', common_names: [] }];
    let requests = 0;
    server.use(
      http.get('/api/v1/species', () => {
        requests += 1;
        return HttpResponse.json({
          items: tenantRows,
          total: tenantRows.length,
          offset: 0,
          limit: 200,
        });
      }),
    );
    const { wrapper } = makeWrapper();

    const underA = renderHook(() => useCatalogue('species'), { wrapper });
    await waitFor(() => expect(underA.result.current.status).toBe('ready'), {
      timeout: WAIT_BUDGET,
    });
    expect(requests).toBe(1);
    underA.unmount();

    // The recovery path's effect on the client, without the reload.
    tenantRows = [{ key: 'sp-b', scientific_name: 'Nur in Tenant B', common_names: [] }];
    setActiveTenantSlug('garten-b');

    const underB = renderHook(() => useCatalogue('species'), { wrapper });
    await waitFor(() => expect(underB.result.current.status).toBe('ready'), {
      timeout: WAIT_BUDGET,
    });

    // The assertion that carries the finding: tenant B must not be served tenant
    // A's rows as its complete catalogue.
    expect(requests).toBe(2);
    expect(underB.result.current.items[0].scientific_name).toBe('Nur in Tenant B');
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
