import * as api from '@/api/endpoints/tanks';
import { createListSlice } from '@/store/createListSlice';

// `listTanks` returns a plain array (no pagination envelope). The slice keeps
// its domain-named state fields (`tanks`/`currentTank`) so page selectors
// (`s.tanks.tanks`) stay unchanged (FR-002 §B1).
const { reducer, fetchList, fetchOne, actions } = createListSlice({
  name: 'tanks',
  // Every page (#3015): the list view searches and sorts client-side, one page would hide the rest.
  list: ({ tankType }: { tankType?: string } = {}) => api.listAllTanks(tankType),
  getOne: (key) => api.getTank(key),
  itemsField: 'tanks',
  currentField: 'currentTank',
  paginated: false,
  singleFetchTogglesStatus: false,
});

export const fetchTanks = fetchList;
export const fetchTank = fetchOne!;
export const clearCurrentTank = actions.clearCurrent;
export const { clearError } = actions;
export default reducer;
