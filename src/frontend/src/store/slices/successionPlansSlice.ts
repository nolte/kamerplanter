import * as api from '@/api/endpoints/successionPlans';
import { createListSlice } from '@/store/createListSlice';

// `listSuccessionPlans` returns a plain array. The slice keeps its domain-named
// state fields (`plans`/`currentPlan`) so page selectors stay expressive.
const { reducer, fetchList, fetchOne, actions } = createListSlice({
  name: 'successionPlans',
  // Every page (#3015): the list view searches and sorts client-side, one page would hide the rest.
  list: () => api.listAllSuccessionPlans(),
  getOne: (key) => api.getSuccessionPlan(key),
  itemsField: 'plans',
  currentField: 'currentPlan',
  paginated: false,
  singleFetchTogglesStatus: false,
});

export const fetchSuccessionPlans = fetchList;
export const fetchSuccessionPlan = fetchOne!;
export const clearCurrentPlan = actions.clearCurrent;
export const { clearError } = actions;
export default reducer;
