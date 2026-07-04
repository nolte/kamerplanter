import type { Substrate } from '@/api/types';
import * as api from '@/api/endpoints/substrates';
import { createListSlice } from '@/store/createListSlice';

// `listSubstrates` returns a plain array (no pagination envelope); the factory
// normalises that into `items` and leaves the pagination fields unused.
const { reducer, fetchList, fetchOne, actions } = createListSlice<Substrate>({
  name: 'substrates',
  list: (offset, limit) => api.listSubstrates(offset, limit),
  getOne: (key) => api.getSubstrate(key),
});

export const fetchSubstrates = fetchList;
export const fetchSubstrate = fetchOne!;
export const { clearCurrent, clearError } = actions;
export default reducer;
