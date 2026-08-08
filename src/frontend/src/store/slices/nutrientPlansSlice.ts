import * as api from '@/api/endpoints/nutrient-plans';
import { createListSlice } from '@/store/createListSlice';

// `fetchAllNutrientPlans` returns a plain array. The slice keeps its
// domain-named state fields (`plans`/`currentPlan`) so page selectors stay
// unchanged (FR-002 §B1).
//
// The slice holds the **complete** catalogue (#995): 38 plans are seeded against
// a single-page default of 50, under it today but not at rest — plus the 12 in
// `nutrient_plans_hydro.yaml` that no seeder loads, which would put the
// catalogue exactly at the limit the day that file is wired up.
const { reducer, fetchList, fetchOne, actions } = createListSlice({
  name: 'nutrientPlans',
  list: ({ isTemplate }: { isTemplate?: boolean } = {}) =>
    api.fetchAllNutrientPlans(
      undefined,
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
