import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import reducer, {
  clearError,
  setFavoriteSpecies,
  toggleFavoriteSpecies,
  setFavoriteNutrientPlans,
  toggleFavoriteNutrientPlan,
  fetchOnboardingState,
  fetchStarterKits,
  fetchExistingSites,
  completeOnboarding,
  skipOnboarding,
  resetOnboarding,
  saveProgress,
  fetchMatchingNutrientPlans,
  fetchAllSpecies,
  fetchExistingFavorites,
} from '@/store/slices/onboardingSlice';
import * as onboardingApi from '@/api/endpoints/onboarding';
import * as starterKitsApi from '@/api/endpoints/starterKits';
import * as speciesApi from '@/api/endpoints/species';
import * as sitesApi from '@/api/endpoints/sites';
import * as favoritesApi from '@/api/endpoints/favorites';

// Isolated module mocks — no real HTTP, no handlers.ts.
vi.mock('@/api/endpoints/onboarding');
vi.mock('@/api/endpoints/starterKits');
vi.mock('@/api/endpoints/species');
vi.mock('@/api/endpoints/sites');
vi.mock('@/api/endpoints/favorites');

function initial() {
  return reducer(undefined, { type: 'unknown' });
}

function makeOnboardingStore() {
  return configureStore({ reducer: { onboarding: reducer } });
}

describe('onboardingSlice', () => {
  it('has sensible initial state', () => {
    const state = initial();
    expect(state.state).toBeNull();
    expect(state.kits).toEqual([]);
    expect(state.favoriteSpeciesKeys).toEqual([]);
    expect(state.favoriteNutrientPlanKeys).toEqual([]);
  });

  it('clearError resets the error', () => {
    const state = reducer({ ...initial(), error: 'boom' }, clearError());
    expect(state.error).toBeNull();
  });

  it('setFavoriteSpecies replaces the selection', () => {
    const state = reducer(initial(), setFavoriteSpecies(['a', 'b']));
    expect(state.favoriteSpeciesKeys).toEqual(['a', 'b']);
  });

  it('toggleFavoriteSpecies adds and removes a key', () => {
    const added = reducer(initial(), toggleFavoriteSpecies('a'));
    expect(added.favoriteSpeciesKeys).toEqual(['a']);
    const removed = reducer(added, toggleFavoriteSpecies('a'));
    expect(removed.favoriteSpeciesKeys).toEqual([]);
  });

  it('setFavoriteNutrientPlans replaces the selection', () => {
    const state = reducer(initial(), setFavoriteNutrientPlans(['p1']));
    expect(state.favoriteNutrientPlanKeys).toEqual(['p1']);
  });

  it('toggleFavoriteNutrientPlan adds and removes a key', () => {
    const added = reducer(initial(), toggleFavoriteNutrientPlan('p1'));
    expect(added.favoriteNutrientPlanKeys).toEqual(['p1']);
    const removed = reducer(added, toggleFavoriteNutrientPlan('p1'));
    expect(removed.favoriteNutrientPlanKeys).toEqual([]);
  });

  it('fetchOnboardingState.fulfilled stores the state and restores saved favorites', () => {
    const payload = {
      completed: false,
      favorite_species_keys: ['s1', 's2'],
      favorite_nutrient_plan_keys: ['p1'],
    };
    const state = reducer(initial(), { type: fetchOnboardingState.fulfilled.type, payload });
    expect(state.state).toEqual(payload);
    expect(state.favoriteSpeciesKeys).toEqual(['s1', 's2']);
    expect(state.favoriteNutrientPlanKeys).toEqual(['p1']);
  });

  it('fetchOnboardingState.rejected falls back to a default message', () => {
    const state = reducer(initial(), { type: fetchOnboardingState.rejected.type, error: {} });
    expect(state.error).toBe('errors.onboardingStateLoadFailed');
  });

  it('fetchStarterKits handles pending, fulfilled and rejected', () => {
    expect(reducer(initial(), { type: fetchStarterKits.pending.type }).loading).toBe(true);
    const fulfilled = reducer(initial(), { type: fetchStarterKits.fulfilled.type, payload: [{ id: 'k1' }] });
    expect(fulfilled.kits).toEqual([{ id: 'k1' }]);
    const rejected = reducer(initial(), { type: fetchStarterKits.rejected.type, error: {} });
    expect(rejected.error).toBe('errors.starterKitsLoadFailed');
  });

  it('completeOnboarding.fulfilled marks the existing state completed', () => {
    const start = { ...initial(), state: { completed: false } as never };
    const state = reducer(start, { type: completeOnboarding.fulfilled.type });
    expect(state.state?.completed).toBe(true);
  });

  it('skipOnboarding.fulfilled replaces the state', () => {
    const state = reducer(initial(), { type: skipOnboarding.fulfilled.type, payload: { completed: true } });
    expect(state.state).toEqual({ completed: true });
  });

  it('resetOnboarding.fulfilled clears favorites and matches', () => {
    const start = {
      ...initial(),
      favoriteSpeciesKeys: ['a'],
      favoriteNutrientPlanKeys: ['p'],
      matchingNutrientPlans: [{ key: 'm' }] as never,
      existingSites: [{ key: 's' }] as never,
    };
    const state = reducer(start, { type: resetOnboarding.fulfilled.type, payload: { completed: false } });
    expect(state.favoriteSpeciesKeys).toEqual([]);
    expect(state.favoriteNutrientPlanKeys).toEqual([]);
    expect(state.matchingNutrientPlans).toEqual([]);
    expect(state.existingSites).toEqual([]);
  });

  it('saveProgress.fulfilled replaces the state', () => {
    const state = reducer(initial(), { type: saveProgress.fulfilled.type, payload: { wizard_step: 2 } });
    expect(state.state).toEqual({ wizard_step: 2 });
  });

  it('fetchMatchingNutrientPlans handles pending, fulfilled and rejected', () => {
    expect(reducer(initial(), { type: fetchMatchingNutrientPlans.pending.type }).matchingPlansLoading).toBe(true);
    const fulfilled = reducer(initial(), {
      type: fetchMatchingNutrientPlans.fulfilled.type,
      payload: [{ key: 'm1' }],
    });
    expect(fulfilled.matchingNutrientPlans).toEqual([{ key: 'm1' }]);
    const rejected = reducer(
      { ...initial(), matchingNutrientPlans: [{ key: 'm1' }] as never },
      { type: fetchMatchingNutrientPlans.rejected.type },
    );
    expect(rejected.matchingNutrientPlans).toEqual([]);
  });

  it('fetchAllSpecies handles pending, fulfilled and rejected', () => {
    expect(reducer(initial(), { type: fetchAllSpecies.pending.type }).allSpeciesLoading).toBe(true);
    const fulfilled = reducer(initial(), { type: fetchAllSpecies.fulfilled.type, payload: [{ key: 'sp1' }] });
    expect(fulfilled.allSpecies).toEqual([{ key: 'sp1' }]);
    expect(reducer(initial(), { type: fetchAllSpecies.rejected.type }).allSpeciesLoading).toBe(false);
  });

  it('fetchExistingSites handles pending, fulfilled and rejected', () => {
    expect(reducer(initial(), { type: fetchExistingSites.pending.type }).existingSitesLoading).toBe(true);
    const fulfilled = reducer(initial(), { type: fetchExistingSites.fulfilled.type, payload: [{ key: 'site1' }] });
    expect(fulfilled.existingSites).toEqual([{ key: 'site1' }]);
    expect(reducer(initial(), { type: fetchExistingSites.rejected.type }).existingSitesLoading).toBe(false);
  });

  it('fetchExistingFavorites.fulfilled merges backend favorites without duplicates', () => {
    const start = { ...initial(), favoriteSpeciesKeys: ['a'] };
    const state = reducer(start, { type: fetchExistingFavorites.fulfilled.type, payload: ['a', 'b'] });
    expect(state.existingFavoriteKeys).toEqual(['a', 'b']);
    expect(state.favoriteSpeciesKeys).toEqual(['a', 'b']);
  });
});

describe('onboardingSlice thunks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchOnboardingState stores the state', async () => {
    vi.mocked(onboardingApi.getState).mockResolvedValue({ completed: false } as never);
    const store = makeOnboardingStore();
    await store.dispatch(fetchOnboardingState());
    expect(onboardingApi.getState).toHaveBeenCalled();
    expect(store.getState().onboarding.state).toEqual({ completed: false });
  });

  it('fetchOnboardingState surfaces a rejection as the slice error', async () => {
    vi.mocked(onboardingApi.getState).mockRejectedValue(new Error('load failed'));
    const store = makeOnboardingStore();
    await store.dispatch(fetchOnboardingState());
    expect(store.getState().onboarding.error).toBe('load failed');
  });

  it('fetchStarterKits uses the global endpoint by default', async () => {
    vi.mocked(starterKitsApi.listKits).mockResolvedValue([{ kit_id: 'k1' }] as never);
    const store = makeOnboardingStore();
    await store.dispatch(fetchStarterKits({ difficulty: 'easy' }));
    expect(starterKitsApi.listKits).toHaveBeenCalledWith('easy');
    expect(store.getState().onboarding.kits).toEqual([{ kit_id: 'k1' }]);
  });

  it('fetchStarterKits uses the tenant endpoint when requested', async () => {
    vi.mocked(starterKitsApi.listKitsForTenant).mockResolvedValue([{ kit_id: 'k2' }] as never);
    const store = makeOnboardingStore();
    await store.dispatch(fetchStarterKits({ difficulty: 'hard', useTenant: true }));
    expect(starterKitsApi.listKitsForTenant).toHaveBeenCalledWith('hard');
  });

  it('fetchExistingSites stores the sites', async () => {
    vi.mocked(sitesApi.listSites).mockResolvedValue([{ key: 's1' }] as never);
    const store = makeOnboardingStore();
    await store.dispatch(fetchExistingSites());
    expect(sitesApi.listSites).toHaveBeenCalledWith(0, 100);
    expect(store.getState().onboarding.existingSites).toEqual([{ key: 's1' }]);
  });

  it('completeOnboarding forwards the payload', async () => {
    vi.mocked(onboardingApi.complete).mockResolvedValue({ completed: true } as never);
    const store = makeOnboardingStore();
    const payload = { kit_id: 'k1', plant_count: 3 };
    await store.dispatch(completeOnboarding(payload));
    expect(onboardingApi.complete).toHaveBeenCalledWith(payload);
  });

  it('skipOnboarding stores the returned state', async () => {
    vi.mocked(onboardingApi.skip).mockResolvedValue({ skipped: true } as never);
    const store = makeOnboardingStore();
    await store.dispatch(skipOnboarding());
    expect(store.getState().onboarding.state).toEqual({ skipped: true });
  });

  it('resetOnboarding stores the returned state', async () => {
    vi.mocked(onboardingApi.reset).mockResolvedValue({ completed: false } as never);
    const store = makeOnboardingStore();
    await store.dispatch(resetOnboarding());
    expect(store.getState().onboarding.state).toEqual({ completed: false });
  });

  it('saveProgress forwards the progress payload', async () => {
    vi.mocked(onboardingApi.updateProgress).mockResolvedValue({ wizard_step: 2 } as never);
    const store = makeOnboardingStore();
    const payload = { wizard_step: 2, selected_kit_id: 'k1' };
    await store.dispatch(saveProgress(payload));
    expect(onboardingApi.updateProgress).toHaveBeenCalledWith(payload);
  });

  it('fetchMatchingNutrientPlans forwards the species keys', async () => {
    vi.mocked(favoritesApi.getMatchingNutrientPlans).mockResolvedValue([{ key: 'np1' }] as never);
    const store = makeOnboardingStore();
    await store.dispatch(fetchMatchingNutrientPlans({ speciesKeys: ['s1', 's2'] }));
    expect(favoritesApi.getMatchingNutrientPlans).toHaveBeenCalledWith(['s1', 's2']);
    expect(store.getState().onboarding.matchingNutrientPlans).toEqual([{ key: 'np1' }]);
  });

  it('fetchAllSpecies extracts the items from the paged response', async () => {
    vi.mocked(speciesApi.listSpecies).mockResolvedValue({ items: [{ key: 'sp1' }], total: 1 } as never);
    const store = makeOnboardingStore();
    await store.dispatch(fetchAllSpecies());
    expect(speciesApi.listSpecies).toHaveBeenCalledWith(0, 500);
    expect(store.getState().onboarding.allSpecies).toEqual([{ key: 'sp1' }]);
  });

  it('fetchExistingFavorites maps entries to their target keys', async () => {
    vi.mocked(favoritesApi.listFavorites).mockResolvedValue([
      { target_key: 'a' }, { target_key: 'b' },
    ] as never);
    const store = makeOnboardingStore();
    await store.dispatch(fetchExistingFavorites());
    expect(favoritesApi.listFavorites).toHaveBeenCalledWith('species');
    expect(store.getState().onboarding.existingFavoriteKeys).toEqual(['a', 'b']);
  });
});
