import * as api from '@/api/endpoints/watering-logs';
import { createListSlice } from '@/store/createListSlice';

// `listWateringLogs` returns a plain array. The slice keeps its domain-named
// state fields (`logs`/`currentLog`) so page selectors stay unchanged
// (FR-002 §B1).
const { reducer, fetchList, fetchOne, actions } = createListSlice({
  name: 'wateringLogs',
  list: ({ offset, limit }: { offset?: number; limit?: number } = {}) =>
    api.listWateringLogs(offset, limit),
  getOne: (key) => api.getWateringLog(key),
  itemsField: 'logs',
  currentField: 'currentLog',
  paginated: false,
  singleFetchTogglesStatus: false,
});

export const fetchWateringLogs = fetchList;
export const fetchWateringLog = fetchOne!;
export const clearCurrentLog = actions.clearCurrent;
export const { clearError } = actions;
export default reducer;
