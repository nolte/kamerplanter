import { configureStore } from '@reduxjs/toolkit';
import uiReducer from './slices/uiSlice';
import botanicalFamiliesReducer from './slices/botanicalFamiliesSlice';
import speciesReducer from './slices/speciesSlice';
import sitesReducer from './slices/sitesSlice';
import substratesReducer from './slices/substratesSlice';
import plantInstancesReducer from './slices/plantInstancesSlice';

export const store = configureStore({
  reducer: {
    ui: uiReducer,
    botanicalFamilies: botanicalFamiliesReducer,
    species: speciesReducer,
    sites: sitesReducer,
    substrates: substratesReducer,
    plantInstances: plantInstancesReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
