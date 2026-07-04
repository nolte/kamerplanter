import * as api from '@/api/endpoints/plantingRuns';
import { createListSlice } from '@/store/createListSlice';

// `listPlantingRuns` returns a plain array. The slice keeps its domain-named
// state fields (`runs`/`currentRun`) so page selectors stay unchanged
// (FR-002 §B1).
const { reducer, fetchList, fetchOne, actions } = createListSlice({
  name: 'plantingRuns',
  list: ({
    offset,
    limit,
    status,
    runType,
  }: { offset?: number; limit?: number; status?: string; runType?: string } = {}) =>
    api.listPlantingRuns(offset, limit, status, runType),
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
