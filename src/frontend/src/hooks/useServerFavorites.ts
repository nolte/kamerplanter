import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import * as favoritesApi from '@/api/endpoints/favorites';
import { mayAdoptLocalData } from '@/lib/localDataOwner';
import { useSignedInUserKey } from '@/hooks/useSignedInUserKey';

/**
 * Server-backed personal favorites for one entity type.
 *
 * Favorites are user-global edges — the backend stores the target's collection
 * name as `target_type`, and REQ-049 §Abgrenzung plus ADR-009 keep them personal
 * across tenants. This hook is the single implementation behind every named
 * favorites hook; before #1233 there were two near-identical copies of it
 * (species, botanical families) and three entity types stored in `localStorage`
 * instead, which is how the fertilizer cascade came to run only inside the
 * onboarding wizard.
 *
 * Optimistic toggle with revert-on-error; degrades silently to an empty set when
 * unauthenticated (light mode), because a favorites filter is a convenience and
 * an error toast for it would interrupt a flow it is not part of.
 *
 * @param entityType Backend collection name, e.g. `species`, `nutrient_plans`.
 * @param legacyStorageKey When given, a one-off carry-over of that
 *   `localStorage` array runs after the first successful load. See
 *   {@link carryOverLegacyFavorites}.
 */
export function useServerFavorites(entityType: string, legacyStorageKey?: string) {
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  // The set the next toggle decides on. A toggle reads it instead of deciding
  // inside a state updater: React may run an updater twice (StrictMode,
  // concurrent rendering), and a request fired from one would be sent twice (#3022).
  const favoritesRef = useRef(favorites);
  // Whose favourites are loaded (`<entityType>|<userKey>`): a sign-out or a switch
  // to another account in the same SPA session loads again instead of keeping the
  // previous user's set (#3022).
  const loadedFor = useRef<string | null>(null);
  const userKey = useSignedInUserKey();

  const replaceFavorites = useCallback((next: Set<string>) => {
    favoritesRef.current = next;
    setFavorites(next);
  }, []);

  useEffect(() => {
    // The carry-over needs to know whose profile it would write into (#2117): with
    // a legacy key, the first load waits for the signed-in account.
    if (legacyStorageKey && !userKey) return;
    const owner = `${entityType}|${userKey ?? ''}`;
    if (loadedFor.current === owner) return;
    if (loadedFor.current !== null) replaceFavorites(new Set());
    loadedFor.current = owner;

    favoritesApi
      .listFavorites(entityType)
      .then(async (entries) => {
        const server = new Set(entries.map((e) => e.target_key));
        const carried = legacyStorageKey
          ? await carryOverLegacyFavorites(legacyStorageKey, server, userKey)
          : new Set<string>();
        // A response for an account that is no longer signed in is dropped.
        if (loadedFor.current !== owner) return;
        replaceFavorites(new Set([...server, ...carried]));
      })
      .catch(() => {
        // Silently fall back to an empty set (e.g. not authenticated).
      });
  }, [entityType, legacyStorageKey, userKey, replaceFavorites]);

  const toggleFavorite = useCallback(
    (key: string) => {
      const removing = favoritesRef.current.has(key);
      const withKey = (present: boolean) => {
        const next = new Set(favoritesRef.current);
        if (present) next.add(key);
        else next.delete(key);
        return next;
      };
      replaceFavorites(withKey(!removing));
      const request = removing
        ? favoritesApi.removeFavorite(key)
        : favoritesApi.addFavorite(key, 'manual');
      request.catch(() => replaceFavorites(withKey(removing)));
    },
    [replaceFavorites],
  );

  const isFavorite = useCallback((key: string) => favorites.has(key), [favorites]);

  return useMemo(
    () => ({ favorites, toggleFavorite, isFavorite, hasFavorites: favorites.size > 0 }),
    [favorites, toggleFavorite, isFavorite],
  );
}

/**
 * Move a pre-#1233 `localStorage` favorites array onto the server, once.
 *
 * The stored array is the local truth — un-favoriting removed the key from it —
 * so every entry in it is something the user still wants. Entries the server
 * already knows are skipped rather than re-posted.
 *
 * The storage key is removed only after **every** post settles successfully, so
 * a failed or partial carry-over is retried on the next mount instead of losing
 * the difference. The removal is what makes this run once per browser; there is
 * no flag to get out of sync with.
 *
 * @returns The keys carried over, so the caller can show them without a reload.
 */
export async function carryOverLegacyFavorites(
  storageKey: string,
  alreadyOnServer: Set<string>,
  userKey?: string | null,
): Promise<Set<string>> {
  let stored: string[];
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return new Set();
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      // Unreadable is not carried over, but it is also not left to be retried
      // forever: nothing here can repair it.
      localStorage.removeItem(storageKey);
      return new Set();
    }
    stored = parsed.filter((k): k is string => typeof k === 'string');
  } catch {
    return new Set();
  }

  // Leftovers another account wrote on this browser stay where they are (#2117):
  // the first account to adopt local data owns it (see `localDataOwner.ts`).
  if (stored.length > 0 && !mayAdoptLocalData(userKey)) return new Set();

  const missing = stored.filter((key) => !alreadyOnServer.has(key));
  if (missing.length === 0) {
    localStorage.removeItem(storageKey);
    return new Set();
  }

  const results = await Promise.allSettled(
    missing.map((key) => favoritesApi.addFavorite(key, 'manual')),
  );
  const carried = new Set(
    missing.filter((_, i) => results[i]?.status === 'fulfilled'),
  );

  if (carried.size === missing.length) {
    localStorage.removeItem(storageKey);
  }
  return carried;
}
