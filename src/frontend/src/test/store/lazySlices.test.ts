import { afterEach, describe, expect, it, vi } from 'vitest';

/**
 * REQ-053 WP 2.3: the garden-plan slice is not part of the initial bundle. It joins the root reducer
 * when the lazy plan route registers it, so a store built before that carries no plan state.
 * `vi.resetModules()` gives every test a store module that has never seen the route.
 */
afterEach(() => vi.resetModules());

async function freshStore() {
  const { configureStore } = await import('@reduxjs/toolkit');
  const { rootReducer } = await import('@/store/rootReducer');
  return configureStore({ reducer: rootReducer });
}

describe('lazy slice registration', () => {
  it('leaves the plan slice out of the state until the route registers it', async () => {
    const store = await freshStore();
    expect(store.getState().gardenPlan).toBeUndefined();
    expect(Object.keys(store.getState())).toContain('auth');
  });

  it('adds the slice once registered, and keeps what the store already holds', async () => {
    const store = await freshStore();
    const { registerLazySlice } = await import('@/store/lazySlices');
    const { gardenPlanSlice, setTool } = await import('@/features/gardenPlanner/state/gardenPlanSlice');
    registerLazySlice(gardenPlanSlice);
    registerLazySlice(gardenPlanSlice); // idempotent
    store.dispatch(setTool('pan'));
    expect(store.getState().gardenPlan?.tool).toBe('pan');
  });

  it('injects a slice registered before the store module ran', async () => {
    const { registerLazySlice } = await import('@/store/lazySlices');
    const { gardenPlanSlice, setTool } = await import('@/features/gardenPlanner/state/gardenPlanSlice');
    registerLazySlice(gardenPlanSlice);
    const store = await freshStore();
    store.dispatch(setTool('bed'));
    expect(store.getState().gardenPlan?.tool).toBe('bed');
  });

  it('resets the plan state with the session end like every other slice (MT-020)', async () => {
    const store = await freshStore();
    const { registerLazySlice } = await import('@/store/lazySlices');
    const { gardenPlanSlice, setTool } = await import('@/features/gardenPlanner/state/gardenPlanSlice');
    const { clearAuth } = await import('@/store/slices/authSlice');
    registerLazySlice(gardenPlanSlice);
    store.dispatch(setTool('measure'));
    store.dispatch(clearAuth());
    expect(store.getState().gardenPlan?.tool).toBe('select');
  });
});
