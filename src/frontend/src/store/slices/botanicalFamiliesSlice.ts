import type { BotanicalFamily } from '@/api/types';
import * as api from '@/api/endpoints/botanicalFamilies';
import { createListSlice } from '@/store/createListSlice';

// `listBotanicalFamilies` returns a plain array (no pagination envelope); the
// factory normalises that into `items` and leaves the pagination fields unused.
const { reducer, fetchList, fetchOne, actions } = createListSlice<BotanicalFamily>({
  name: 'botanicalFamilies',
  list: (offset, limit) => api.listBotanicalFamilies(offset, limit),
  getOne: (key) => api.getBotanicalFamily(key),
});

export const fetchBotanicalFamilies = fetchList;
export const fetchBotanicalFamily = fetchOne!;
export const { clearCurrent, clearError } = actions;
export default reducer;
