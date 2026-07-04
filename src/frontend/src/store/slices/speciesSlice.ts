import type { Species } from '@/api/types';
import * as api from '@/api/endpoints/species';
import { createListSlice } from '@/store/createListSlice';

const { reducer, fetchList, fetchOne, actions } = createListSlice<Species>({
  name: 'species',
  list: (offset, limit) => api.listSpecies(offset, limit),
  getOne: (key) => api.getSpecies(key),
});

export const fetchSpeciesList = fetchList;
export const fetchSpecies = fetchOne!;
export const { clearCurrent, clearError } = actions;
export default reducer;
