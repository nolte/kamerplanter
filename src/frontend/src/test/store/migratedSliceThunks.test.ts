/**
 * Thunk coverage for the FR-002 §B1 list slices migrated to createListSlice.
 *
 * Their reducer tests exercise the reducers but never dispatch the async
 * thunks, so the `list`/`getOne` fetcher closures each slice passes to the
 * factory were uncovered (dropping global function coverage below the gate).
 * These tests dispatch fetchList + fetchOne against a mocked endpoint module,
 * running the fetchers and the itemsField/currentField/paginated branches.
 *
 * `listFn` names the endpoint each slice's fetcher is *expected* to reach. For a
 * global reference catalogue that is the complete-catalogue loader, not the
 * single-page one (#995): this table is the one place the pairing is written
 * down for all of them at once, so a slice quietly reverting to a bounded page
 * fails here.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { configureStore, type Reducer, type UnknownAction } from '@reduxjs/toolkit';

vi.mock('@/api/endpoints/watering-logs');
vi.mock('@/api/endpoints/nutrient-plans');
vi.mock('@/api/endpoints/feeding-events');
vi.mock('@/api/endpoints/substrates');
vi.mock('@/api/endpoints/plantInstances');
vi.mock('@/api/endpoints/tanks');
vi.mock('@/api/endpoints/fertilizers');
vi.mock('@/api/endpoints/plantingRuns');
vi.mock('@/api/endpoints/activities');

import wateringLogsReducer, { fetchWateringLogs, fetchWateringLog } from '@/store/slices/wateringLogsSlice';
import nutrientPlansReducer, { fetchNutrientPlans, fetchNutrientPlan } from '@/store/slices/nutrientPlansSlice';
import feedingEventsReducer, { fetchFeedingEvents, fetchFeedingEvent } from '@/store/slices/feedingEventsSlice';
import substratesReducer, { fetchSubstrates, fetchSubstrate } from '@/store/slices/substratesSlice';
import plantInstancesReducer, { fetchPlantInstances, fetchPlantInstance } from '@/store/slices/plantInstancesSlice';
import tanksReducer, { fetchTanks, fetchTank } from '@/store/slices/tanksSlice';
import fertilizersReducer, { fetchFertilizers, fetchFertilizer } from '@/store/slices/fertilizersSlice';
import plantingRunsReducer, { fetchPlantingRuns, fetchPlantingRun } from '@/store/slices/plantingRunsSlice';
import activitiesReducer, { fetchActivities, fetchActivity } from '@/store/slices/activitiesSlice';

import * as wlApi from '@/api/endpoints/watering-logs';
import * as npApi from '@/api/endpoints/nutrient-plans';
import * as feApi from '@/api/endpoints/feeding-events';
import * as subApi from '@/api/endpoints/substrates';
import * as piApi from '@/api/endpoints/plantInstances';
import * as tankApi from '@/api/endpoints/tanks';
import * as fertApi from '@/api/endpoints/fertilizers';
import * as prApi from '@/api/endpoints/plantingRuns';
import * as actApi from '@/api/endpoints/activities';

// A dispatch that accepts thunk actions without pulling in the store's full
// generic dispatch type (the cases array is heterogeneous). Not `any`.
type ThunkDispatch = (action: unknown) => Promise<unknown>;
type AnyReducer = Reducer<unknown, UnknownAction>;

// Erase the per-slice state type so heterogeneous reducers fit one table.
// The single localized conversion lives here (no `any`, no eslint-disable).
const erase = <S>(r: Reducer<S>): AnyReducer => r as unknown as AnyReducer;

interface SliceCase {
  name: string;
  reducer: AnyReducer;
  list: () => unknown;
  one: (key: string) => unknown;
  listFn: (...args: never[]) => Promise<unknown>;
  oneFn: (...args: never[]) => Promise<unknown>;
}

const cases: SliceCase[] = [
  { name: 'wateringLogs', reducer: erase(wateringLogsReducer), list: fetchWateringLogs, one: fetchWateringLog, listFn: wlApi.listWateringLogs, oneFn: wlApi.getWateringLog },
  { name: 'nutrientPlans', reducer: erase(nutrientPlansReducer), list: fetchNutrientPlans, one: fetchNutrientPlan, listFn: npApi.fetchAllNutrientPlans, oneFn: npApi.fetchNutrientPlan },
  { name: 'feedingEvents', reducer: erase(feedingEventsReducer), list: fetchFeedingEvents, one: fetchFeedingEvent, listFn: feApi.listFeedingEvents, oneFn: feApi.getFeedingEvent },
  { name: 'substrates', reducer: erase(substratesReducer), list: fetchSubstrates, one: fetchSubstrate, listFn: subApi.listAllSubstrates, oneFn: subApi.getSubstrate },
  { name: 'plantInstances', reducer: erase(plantInstancesReducer), list: fetchPlantInstances, one: fetchPlantInstance, listFn: piApi.listPlantInstances, oneFn: piApi.getPlantInstance },
  { name: 'tanks', reducer: erase(tanksReducer), list: fetchTanks, one: fetchTank, listFn: tankApi.listTanks, oneFn: tankApi.getTank },
  { name: 'fertilizers', reducer: erase(fertilizersReducer), list: fetchFertilizers, one: fetchFertilizer, listFn: fertApi.fetchAllFertilizers, oneFn: fertApi.fetchFertilizer },
  { name: 'plantingRuns', reducer: erase(plantingRunsReducer), list: fetchPlantingRuns, one: fetchPlantingRun, listFn: prApi.listPlantingRuns, oneFn: prApi.getPlantingRun },
  { name: 'activities', reducer: erase(activitiesReducer), list: fetchActivities, one: fetchActivity, listFn: actApi.listAllActivities, oneFn: actApi.getActivity },
];

beforeEach(() => {
  vi.clearAllMocks();
});

describe.each(cases)('$name slice thunks (FR-002 B1 fetcher coverage)', (c) => {
  it('fetchList and fetchOne run their fetchers and settle without error', async () => {
    vi.mocked(c.listFn).mockResolvedValue([{ key: 'k1' }]);
    vi.mocked(c.oneFn).mockResolvedValue({ key: 'k1' });

    const store = configureStore({ reducer: { s: c.reducer } });
    const dispatch = store.dispatch as unknown as ThunkDispatch;
    await dispatch(c.list());
    await dispatch(c.one('k1'));

    const state = store.getState().s as { loading: boolean; error: string | null };
    expect(c.listFn).toHaveBeenCalled();
    expect(c.oneFn).toHaveBeenCalled();
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });
});
