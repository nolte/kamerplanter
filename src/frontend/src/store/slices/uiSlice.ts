import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface UiState {
  sidebarOpen: boolean;
  breadcrumbs: BreadcrumbItem[];
  globalLoading: boolean;
  showAllFieldsOverride: boolean;
}

const initialState: UiState = {
  sidebarOpen: typeof window !== 'undefined' ? window.innerWidth >= 768 : true,
  breadcrumbs: [],
  globalLoading: false,
  showAllFieldsOverride: false,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar(state) {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen(state, action: PayloadAction<boolean>) {
      state.sidebarOpen = action.payload;
    },
    setBreadcrumbs(state, action: PayloadAction<BreadcrumbItem[]>) {
      state.breadcrumbs = action.payload;
    },
    setGlobalLoading(state, action: PayloadAction<boolean>) {
      state.globalLoading = action.payload;
    },
    toggleShowAllFields(state) {
      state.showAllFieldsOverride = !state.showAllFieldsOverride;
    },
    resetShowAllFields(state) {
      state.showAllFieldsOverride = false;
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  setBreadcrumbs,
  setGlobalLoading,
  toggleShowAllFields,
  resetShowAllFields,
} = uiSlice.actions;
export default uiSlice.reducer;
