import type { PlantInstance } from '@/api/types';
import * as api from '@/api/endpoints/plantInstances';
import { createListSlice } from '@/store/createListSlice';

// `listPlantInstances` returns a plain array (no pagination envelope); the
// factory normalises that into `items` and leaves the pagination fields unused.
const { reducer, fetchList, fetchOne, actions } = createListSlice<PlantInstance>({
  name: 'plantInstances',
  list: (offset, limit) => api.listPlantInstances(offset, limit),
  getOne: (key) => api.getPlantInstance(key),
});

export const fetchPlantInstances = fetchList;
export const fetchPlantInstance = fetchOne!;
export const { clearCurrent, clearError } = actions;
export default reducer;
