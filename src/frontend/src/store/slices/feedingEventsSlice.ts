import * as api from '@/api/endpoints/feeding-events';
import { createListSlice } from '@/store/createListSlice';

// `listFeedingEvents` returns a plain array. The slice keeps its domain-named
// state fields (`events`/`currentEvent`) so page selectors stay unchanged
// (FR-002 §B1).
const { reducer, fetchList, fetchOne, actions } = createListSlice({
  name: 'feedingEvents',
  list: ({ offset, limit }: { offset?: number; limit?: number } = {}) =>
    api.listFeedingEvents(offset, limit),
  getOne: (key) => api.getFeedingEvent(key),
  itemsField: 'events',
  currentField: 'currentEvent',
  paginated: false,
  singleFetchTogglesStatus: false,
});

export const fetchFeedingEvents = fetchList;
export const fetchFeedingEvent = fetchOne!;
export const clearCurrentEvent = actions.clearCurrent;
export const { clearError } = actions;
export default reducer;
