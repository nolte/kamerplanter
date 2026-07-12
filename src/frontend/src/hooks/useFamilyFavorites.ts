import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import * as favoritesApi from '@/api/endpoints/favorites';

/**
 * Botanical-family favorites, mirroring {@link useSowingFavorites} for the
 * crop-rotation "Von Familie" dropdown filter (#550). Favorites are user-global
 * edges (the backend stores `target_type` as the collection name), so families
 * are filtered by the `botanical_families` entity type. Optimistic toggle with
 * revert-on-error; silently degrades to an empty set when unauthenticated
 * (e.g. light mode).
 */
const FAMILY_ENTITY_TYPE = 'botanical_families';

export function useFamilyFavorites() {
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const loaded = useRef(false);

  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;

    favoritesApi
      .listFavorites(FAMILY_ENTITY_TYPE)
      .then((entries) => {
        setFavorites(new Set(entries.map((e) => e.target_key)));
      })
      .catch(() => {
        // Silently fall back to empty set on error (e.g. not authenticated).
      });
  }, []);

  const toggleFavorite = useCallback((key: string) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
        favoritesApi.removeFavorite(key).catch(() => {
          setFavorites((p) => new Set([...p, key]));
        });
      } else {
        next.add(key);
        favoritesApi.addFavorite(key, 'manual').catch(() => {
          setFavorites((p) => {
            const reverted = new Set(p);
            reverted.delete(key);
            return reverted;
          });
        });
      }
      return next;
    });
  }, []);

  const isFavorite = useCallback((key: string) => favorites.has(key), [favorites]);

  return useMemo(
    () => ({ favorites, toggleFavorite, isFavorite }),
    [favorites, toggleFavorite, isFavorite],
  );
}
