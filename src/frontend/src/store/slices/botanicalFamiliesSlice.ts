import type { BotanicalFamily } from '@/api/types';
import * as api from '@/api/endpoints/botanicalFamilies';
import { createListSlice } from '@/store/createListSlice';

// `listAllBotanicalFamilies` returns a plain array (no pagination envelope); the
// factory normalises that into `items` and leaves the pagination fields unused.
//
// The slice holds the **complete** catalogue (#995). It used to ask for one page
// of 50 while 57 families are seeded, so seven of them never reached the list
// view — and, because `DataTable` searches client-side, typing one of the seven
// names answered "no results" instead of showing the family. `offset`/`limit`
// are gone from the thunk argument: there is no page to ask for.
const { reducer, fetchList, fetchOne, actions } = createListSlice<BotanicalFamily>({
  name: 'botanicalFamilies',
  list: () => api.listAllBotanicalFamilies(),
  getOne: (key) => api.getBotanicalFamily(key),
});

export const fetchBotanicalFamilies = fetchList;
export const fetchBotanicalFamily = fetchOne!;
export const { clearCurrent, clearError } = actions;
export default reducer;
