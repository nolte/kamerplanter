import * as api from '@/api/endpoints/plantingRuns';
import { createListSlice } from '@/store/createListSlice';

// `listPlantingRuns` returns a plain array. The slice keeps its domain-named
// state fields (`runs`/`currentRun`) so page selectors stay unchanged
// (FR-002 §B1). The list always loads every page, never one window (#3015).
const { reducer, fetchList, fetchOne, actions } = createListSlice({
  name: 'plantingRuns',
  list: ({ status, runType }: { status?: string; runType?: string } = {}) =>
    api.listAllPlantingRuns(status, runType),
  getOne: (key) => api.getPlantingRun(key),
  itemsField: 'runs',
  currentField: 'currentRun',
  paginated: false,
  singleFetchTogglesStatus: false,
});

export const fetchPlantingRuns = fetchList;
export const fetchPlantingRun = fetchOne!;
export const clearCurrentRun = actions.clearCurrent;
export const { clearError } = actions;
export default reducer;
