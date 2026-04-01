import { describe, it, expect } from 'vitest';
import reducer, {
  toggleSidebar,
  setSidebarOpen,
  setBreadcrumbs,
  setGlobalLoading,
  toggleShowAllFields,
  resetShowAllFields,
} from '@/store/slices/uiSlice';

describe('uiSlice', () => {
  const initialState = { sidebarOpen: true, breadcrumbs: [], globalLoading: false, showAllFieldsOverride: false };

  it('has correct initial state', () => {
    expect(reducer(undefined, { type: 'unknown' })).toEqual(initialState);
  });

  it('toggleSidebar flips state', () => {
    const state = reducer(initialState, toggleSidebar());
    expect(state.sidebarOpen).toBe(false);
    const state2 = reducer(state, toggleSidebar());
    expect(state2.sidebarOpen).toBe(true);
  });

  it('setSidebarOpen sets explicit value', () => {
    const state = reducer(initialState, setSidebarOpen(false));
    expect(state.sidebarOpen).toBe(false);
  });

  it('setBreadcrumbs updates breadcrumbs', () => {
    const crumbs = [{ label: 'Home', path: '/' }, { label: 'Species' }];
    const state = reducer(initialState, setBreadcrumbs(crumbs));
    expect(state.breadcrumbs).toEqual(crumbs);
  });

  it('setGlobalLoading updates loading', () => {
    const state = reducer(initialState, setGlobalLoading(true));
    expect(state.globalLoading).toBe(true);
  });

  it('toggleShowAllFields flips override state', () => {
    const state = reducer(initialState, toggleShowAllFields());
    expect(state.showAllFieldsOverride).toBe(true);
    const state2 = reducer(state, toggleShowAllFields());
    expect(state2.showAllFieldsOverride).toBe(false);
  });

  it('resetShowAllFields resets to false', () => {
    const toggled = reducer(initialState, toggleShowAllFields());
    expect(toggled.showAllFieldsOverride).toBe(true);
    const reset = reducer(toggled, resetShowAllFields());
    expect(reset.showAllFieldsOverride).toBe(false);
  });
});
