import { useState, useCallback, useMemo } from 'react';

export function useLocalFavorites(storageKey: string) {
  const [favorites, setFavorites] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem(storageKey);
      return stored ? new Set(JSON.parse(stored) as string[]) : new Set();
    } catch {
      return new Set();
    }
  });

  const toggleFavorite = useCallback((key: string) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      localStorage.setItem(storageKey, JSON.stringify([...next]));
      return next;
    });
  }, [storageKey]);

  const isFavorite = useCallback((key: string) => favorites.has(key), [favorites]);

  return useMemo(
    () => ({ favorites, toggleFavorite, isFavorite, hasFavorites: favorites.size > 0 }),
    [favorites, toggleFavorite, isFavorite],
  );
}
