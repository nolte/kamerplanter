import * as api from '@/api/endpoints/fertilizers';
import { createListSlice } from '@/store/createListSlice';

// `fetchFertilizers` returns a plain array. The slice keeps its domain-named
// state fields (`fertilizers`/`currentFertilizer`) so page selectors stay
// unchanged (FR-002 §B1).
const { reducer, fetchList, fetchOne, actions } = createListSlice({
  name: 'fertilizers',
  list: ({
    offset,
    limit,
    fertilizerType,
    brand,
    tankSafe,
    isOrganic,
  }: {
    offset?: number;
    limit?: number;
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
    return api.fetchFertilizers(
      offset,
      limit,
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
