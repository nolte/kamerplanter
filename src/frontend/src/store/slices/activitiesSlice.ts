import * as api from '@/api/endpoints/activities';
import { createListSlice } from '@/store/createListSlice';

// `listActivities` returns a plain array and takes filter-only args (no
// paging). The slice uses the canonical `items`/`current` fields; page
// selectors (`s.activities.items`) stay unchanged (FR-002 §B1).
const { reducer, fetchList, fetchOne, actions } = createListSlice({
  name: 'activities',
  list: (arg: { category?: string; scope?: 'universal' | 'restricted'; species?: string } = {}) =>
    api.listActivities(arg),
  getOne: (key) => api.getActivity(key),
  paginated: false,
  singleFetchTogglesStatus: false,
});

export const fetchActivities = fetchList;
export const fetchActivity = fetchOne!;
export const { clearCurrent, clearError } = actions;
export default reducer;
