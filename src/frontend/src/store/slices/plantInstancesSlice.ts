import { createAction, createAsyncThunk } from '@reduxjs/toolkit';
import type { Reducer } from '@reduxjs/toolkit';
import type { PlantInstance } from '@/api/types';
import * as api from '@/api/endpoints/plantInstances';
import { CATALOGUE_PAGE_SIZE } from '@/api/paginate';
import { errorKey as resolveErrorKey } from '@/api/errors';
import { createListSlice } from '@/store/createListSlice';
import type { ListPageArg, ListState } from '@/store/createListSlice';

/**
 * Thunk argument of {@link fetchPlantInstances}. `all: true` loads every page
 * (keyset/offset paging until a short page) instead of a single window.
 *
 * The plant list searches and sorts client-side, so a single window silently
 * hides every plant past it — the backend orders by `_key` ascending, so a
 * newly created plant never appeared once a tenant held more than 50 (#3032).
 * The list page itself uses {@link fetchAllPlantInstances}, which loads the same
 * complete set but publishes it page by page.
 */
export interface PlantInstanceListArg extends ListPageArg {
  all?: boolean;
}

/** One page of a progressive load, tagged with the load it belongs to. */
interface PageLoadedPayload {
  requestId: string;
  items: PlantInstance[];
  first: boolean;
  done: boolean;
}

const pageLoaded = createAction<PageLoadedPayload>('plantInstances/pageLoaded');

/**
 * Loads every plant instance and publishes each page as it arrives (#3032).
 *
 * Waiting for the complete set before rendering kept the list on its skeleton
 * for as long as the slowest tenant took to page through — in the shared CI
 * tenant past every E2E budget. Now the first page replaces the list and ends
 * the loading state, later pages append, and `loadingMore` stays `true` until
 * the last one landed. The fulfilled payload is still the complete set, so the
 * client-side search and sort end up over every plant, as before.
 */
export const fetchAllPlantInstances = createAsyncThunk(
  'plantInstances/fetchAllProgressive',
  (_arg: void, { dispatch, requestId }) =>
    api.listAllPlantInstances(CATALOGUE_PAGE_SIZE, (batch, { pageIndex, done }) => {
      dispatch(pageLoaded({ requestId, items: batch, first: pageIndex === 0, done }));
    }),
);

/** Slice fields the progressive load adds to the shared {@link ListState}. */
export interface PlantInstanceProgressFields {
  /** `true` between the first and the last page of {@link fetchAllPlantInstances}. */
  loadingMore?: boolean;
  /** `requestId` of the progressive load whose pages are applied; older loads are ignored. */
  progressiveRequestId?: string | null;
  /** Incremented when a progressive load completed — a refresh key for dependants. */
  loadedGeneration?: number;
}

type PlantInstancesState = ListState<PlantInstance> & PlantInstanceProgressFields;

// `listPlantInstances` returns a plain array (no pagination envelope); the
// factory normalises that into `items` and leaves the pagination fields unused.
const { reducer, fetchList, fetchOne, actions } = createListSlice<PlantInstance, PlantInstanceListArg>({
  name: 'plantInstances',
  list: ({ offset = 0, limit = 50, all = false } = {}) =>
    all ? api.listAllPlantInstances() : api.listPlantInstances(offset, limit),
  getOne: (key) => api.getPlantInstance(key),
  extraCases: (builder) => {
    builder
      .addCase(fetchAllPlantInstances.pending, (state, action) => {
        const s = state as PlantInstancesState;
        s.progressiveRequestId = action.meta.requestId;
        s.loading = true;
        s.loadingMore = false;
        s.error = null;
      })
      .addCase(pageLoaded, (state, action) => {
        const s = state as PlantInstancesState;
        // Two loads can overlap (mount + refetch after a create); only the
        // latest may write, or its pages would interleave with the stale one.
        if (action.payload.requestId !== s.progressiveRequestId) return;
        if (action.payload.first) {
          s.items = action.payload.items;
        } else {
          s.items.push(...action.payload.items);
        }
        s.loading = false;
        s.loadingMore = !action.payload.done;
      })
      .addCase(fetchAllPlantInstances.fulfilled, (state, action) => {
        const s = state as PlantInstancesState;
        if (action.meta.requestId !== s.progressiveRequestId) return;
        // The pages of this load already hold the complete set. Replacing it with an
        // equal array would hand every `items`-keyed effect a new reference right
        // after the last page and run each enrichment fan-out a second time.
        if (s.items.length !== action.payload.length) s.items = action.payload;
        s.loading = false;
        s.loadingMore = false;
        s.progressiveRequestId = null;
        s.loadedGeneration = (s.loadedGeneration ?? 0) + 1;
      })
      .addCase(fetchAllPlantInstances.rejected, (state, action) => {
        const s = state as PlantInstancesState;
        if (action.meta.requestId !== s.progressiveRequestId) return;
        s.loading = false;
        s.loadingMore = false;
        s.progressiveRequestId = null;
        s.error = resolveErrorKey(action.error, 'errors.loadFailed');
      });
  },
});

export const fetchPlantInstances = fetchList;
export const fetchPlantInstance = fetchOne!;
export const { clearCurrent, clearError } = actions;
export default reducer as unknown as Reducer<PlantInstancesState>;
