import * as api from '@/api/endpoints/activities';
import type { ActivityFilters } from '@/api/endpoints/activities';
import { createListSlice } from '@/store/createListSlice';

// `listAllActivities` returns a plain array and takes filter-only args. The
// slice uses the canonical `items`/`current` fields; page selectors
// (`s.activities.items`) stay unchanged (FR-002 §B1).
//
// The slice holds the **complete** catalogue (#995). Sending no paging argument
// did not mean "everything": the endpoint applies the shared backend default of
// 50, and 51 activities are seeded — so one of them was absent from the list
// view, and searching for it answered "no results" because `DataTable` searches
// client-side over the rows already fetched.
const { reducer, fetchList, fetchOne, actions } = createListSlice({
  name: 'activities',
  list: (arg: ActivityFilters = {}) => api.listAllActivities(arg),
  getOne: (key) => api.getActivity(key),
  paginated: false,
  singleFetchTogglesStatus: false,
});

export const fetchActivities = fetchList;
export const fetchActivity = fetchOne!;
export const { clearCurrent, clearError } = actions;
export default reducer;
