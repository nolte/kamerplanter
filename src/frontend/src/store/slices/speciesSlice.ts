import type { Species } from '@/api/types';
import * as api from '@/api/endpoints/species';
import { createListSlice } from '@/store/createListSlice';

// The slice holds the **complete** catalogue (#995). The list view previously
// asked for a fixed `limit=1000` — the species endpoint's own cap, not the
// shared `le=200` — which held the 207 seeded species with 793 rows of headroom
// and therefore never truncated. It was still a bound on a tenant-extensible
// catalogue, and its failure mode is silent: `DataTable` searches and sorts
// client-side, so rows past the bound are reported as non-existent rather than
// as missing. `offset`/`limit` are gone: there is no page to ask for.
const { reducer, fetchList, fetchOne, actions } = createListSlice<Species>({
  name: 'species',
  list: () => api.listAllSpecies(),
  getOne: (key) => api.getSpecies(key),
});

export const fetchSpeciesList = fetchList;
export const fetchSpecies = fetchOne!;
export const { clearCurrent, clearError } = actions;
export default reducer;
