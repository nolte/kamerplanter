import { useServerFavorites } from './useServerFavorites';

/**
 * Botanical-family favorites for the crop-rotation "Von Familie" dropdown
 * filter (#550). Delegates to {@link useServerFavorites}; it used to carry its
 * own copy of that logic, identical to `useSowingFavorites` apart from the
 * entity type (#1233).
 */
export function useFamilyFavorites() {
  return useServerFavorites('botanical_families');
}
