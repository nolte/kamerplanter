import { describe, it, expect } from 'vitest';
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

function initial() {
  return reducer(undefined, { type: 'unknown' });
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
    expect(state.error).toBe('Failed to load onboarding state');
  });

  it('fetchStarterKits handles pending, fulfilled and rejected', () => {
    expect(reducer(initial(), { type: fetchStarterKits.pending.type }).loading).toBe(true);
    const fulfilled = reducer(initial(), { type: fetchStarterKits.fulfilled.type, payload: [{ id: 'k1' }] });
    expect(fulfilled.kits).toEqual([{ id: 'k1' }]);
    const rejected = reducer(initial(), { type: fetchStarterKits.rejected.type, error: {} });
    expect(rejected.error).toBe('Failed to load starter kits');
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
