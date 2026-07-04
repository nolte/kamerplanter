import * as api from '@/api/endpoints/nutrient-plans';
import { createListSlice } from '@/store/createListSlice';

// `fetchNutrientPlans` returns a plain array. The slice keeps its domain-named
// state fields (`plans`/`currentPlan`) so page selectors stay unchanged
// (FR-002 §B1).
const { reducer, fetchList, fetchOne, actions } = createListSlice({
  name: 'nutrientPlans',
  list: ({
    offset,
    limit,
    isTemplate,
  }: { offset?: number; limit?: number; isTemplate?: boolean } = {}) =>
    api.fetchNutrientPlans(
      offset,
      limit,
      isTemplate !== undefined ? { is_template: String(isTemplate) } : undefined,
    ),
  getOne: (key) => api.fetchNutrientPlan(key),
  itemsField: 'plans',
  currentField: 'currentPlan',
  paginated: false,
  singleFetchTogglesStatus: false,
});

export const fetchNutrientPlans = fetchList;
export const fetchNutrientPlan = fetchOne!;
export const clearCurrentPlan = actions.clearCurrent;
export const { clearError } = actions;
export default reducer;
