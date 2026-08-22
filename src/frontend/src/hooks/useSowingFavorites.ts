import { useServerFavorites } from './useServerFavorites';

/**
 * Species favorites, used by the species list and detail pages, the calendar
 * and the plant-instance create dialog. Delegates to
 * {@link useServerFavorites}; it used to carry its own copy of that logic
 * (#1233).
 */
export function useSowingFavorites() {
  return useServerFavorites('species');
}
