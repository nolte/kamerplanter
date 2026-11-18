import type { PlantInstance } from '@/api/types';
import * as api from '@/api/endpoints/plantInstances';
import { createListSlice } from '@/store/createListSlice';
import type { ListPageArg } from '@/store/createListSlice';

/**
 * Thunk argument of {@link fetchPlantInstances}. `all: true` loads every page
 * (keyset/offset paging until a short page) instead of a single window.
 *
 * The plant list searches and sorts client-side, so a single window silently
 * hides every plant past it — the backend orders by `_key` ascending, so a
 * newly created plant never appeared once a tenant held more than 50 (#3032).
 */
export interface PlantInstanceListArg extends ListPageArg {
  all?: boolean;
}

// `listPlantInstances` returns a plain array (no pagination envelope); the
// factory normalises that into `items` and leaves the pagination fields unused.
const { reducer, fetchList, fetchOne, actions } = createListSlice<PlantInstance, PlantInstanceListArg>({
  name: 'plantInstances',
  list: ({ offset = 0, limit = 50, all = false } = {}) =>
    all ? api.listAllPlantInstances() : api.listPlantInstances(offset, limit),
  getOne: (key) => api.getPlantInstance(key),
});

export const fetchPlantInstances = fetchList;
export const fetchPlantInstance = fetchOne!;
export const { clearCurrent, clearError } = actions;
export default reducer;
