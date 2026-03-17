import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import * as favoritesApi from '@/api/endpoints/favorites';

export function useSowingFavorites() {
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const loaded = useRef(false);

  // Load favorites from backend on mount
  useEffect(() => {
    if (loaded.current) return;
    loaded.current = true;

    favoritesApi.listFavorites('species').then((entries) => {
      setFavorites(new Set(entries.map((e) => e.target_key)));
    }).catch(() => {
      // Silently fall back to empty set on error (e.g. not authenticated)
    });
  }, []);

  const toggleFavorite = useCallback((key: string) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
        favoritesApi.removeFavorite(key).catch(() => {
          // Revert on error
          setFavorites((p) => new Set([...p, key]));
        });
      } else {
        next.add(key);
        favoritesApi.addFavorite(key, 'manual').catch(() => {
          // Revert on error
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

  return useMemo(() => ({ favorites, toggleFavorite, isFavorite }), [favorites, toggleFavorite, isFavorite]);
}
