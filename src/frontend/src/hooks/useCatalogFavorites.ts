import { useServerFavorites } from './useServerFavorites';

/**
 * Named favorites hooks for the three catalogue types that moved off
 * `localStorage` in #1233.
 *
 * Each passes its pre-#1233 storage key so an existing browser's favorites are
 * carried over on first load rather than silently lost — the keys were the only
 * place these lived, so dropping them would have looked like the feature
 * forgetting what the user chose.
 *
 * They are wrappers rather than three copies of the hook: two copies is what
 * `useSowingFavorites` and `useFamilyFavorites` already were, and the split
 * between server-backed and local storage ran exactly through the two entity
 * types the specified fertilizer cascade connects.
 */

export function useNutrientPlanFavorites() {
  return useServerFavorites('nutrient_plans', 'kamerplanter-nutrient-plan-favorites');
}

export function useFertilizerFavorites() {
  return useServerFavorites('fertilizers', 'kamerplanter-fertilizer-favorites');
}

export function useSubstrateFavorites() {
  return useServerFavorites('substrates', 'kamerplanter-substrate-favorites');
}
