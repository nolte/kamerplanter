import type { Substrate } from '@/api/types';
import * as api from '@/api/endpoints/substrates';
import { createListSlice } from '@/store/createListSlice';

// `listAllSubstrates` returns a plain array (no pagination envelope); the factory
// normalises that into `items` and leaves the pagination fields unused.
//
// The slice holds the **complete** catalogue (#995): 28 substrates are seeded
// against a single-page default of 50, which is under it today and not a resting
// state — the list view searches and sorts client-side, so crossing the bound
// would drop rows and make the search deny them, with nothing turning red.
const { reducer, fetchList, fetchOne, actions } = createListSlice<Substrate>({
  name: 'substrates',
  list: () => api.listAllSubstrates(),
  getOne: (key) => api.getSubstrate(key),
});

export const fetchSubstrates = fetchList;
export const fetchSubstrate = fetchOne!;
export const { clearCurrent, clearError } = actions;
export default reducer;
