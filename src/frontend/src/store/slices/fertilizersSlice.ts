import * as api from '@/api/endpoints/fertilizers';
import { createListSlice } from '@/store/createListSlice';

// `fetchAllFertilizers` returns a plain array. The slice keeps its domain-named
// state fields (`fertilizers`/`currentFertilizer`) so page selectors stay
// unchanged (FR-002 §B1).
//
// The slice holds the **complete** catalogue, not a page of it (#995). Every
// consumer of `s.fertilizers.fertilizers` — the list view and the "pick any
// fertilizer" selectors alike — treats it as the whole set: the list view
// searches, sorts and paginates it client-side, which is only truthful over a
// complete set, and a selector that offers a subset silently makes products
// unpickable. So `offset`/`limit` are deliberately absent from the thunk
// argument: there is no page to ask for. Callers that genuinely want one page
// call `api.fetchFertilizers()` directly.
const { reducer, fetchList, fetchOne, actions } = createListSlice({
  name: 'fertilizers',
  list: ({
    fertilizerType,
    brand,
    tankSafe,
    isOrganic,
  }: {
    fertilizerType?: string;
    brand?: string;
    tankSafe?: boolean;
    isOrganic?: boolean;
  } = {}) => {
    const filters: Record<string, string> = {};
    if (fertilizerType) filters.fertilizer_type = fertilizerType;
    if (brand) filters.brand = brand;
    if (tankSafe !== undefined) filters.tank_safe = String(tankSafe);
    if (isOrganic !== undefined) filters.is_organic = String(isOrganic);
    return api.fetchAllFertilizers(
      undefined,
      Object.keys(filters).length > 0 ? filters : undefined,
    );
  },
  getOne: (key) => api.fetchFertilizer(key),
  itemsField: 'fertilizers',
  currentField: 'currentFertilizer',
  paginated: false,
  singleFetchTogglesStatus: false,
});

export const fetchFertilizers = fetchList;
export const fetchFertilizer = fetchOne!;
export const clearCurrentFertilizer = actions.clearCurrent;
export const { clearError } = actions;
export default reducer;
