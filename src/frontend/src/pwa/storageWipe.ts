/**
 * Deleting Cache Storage and IndexedDB (REQ-053 WP 9.1, #2741) — shared by the app (logout, tenant
 * switch, kill switch) and the service worker (kill switch `selfDestruct`). Uses only the `caches`
 * and `indexedDB` globals, which a window and a worker both have, so it type-checks in both
 * programs. Best-effort and never throws: a missing API means nothing was stored there.
 */

/**
 * The garden plan cache (REQ-053 WP 9.2, `features/gardenPlanner/offline/db.ts`). Named here so the
 * wipe knows it even where `indexedDB.databases()` is missing (Firefox before 126): every database
 * the app itself creates is listed in {@link APP_DATABASE_NAMES}.
 */
export const PLAN_CACHE_DB_NAME = 'kp-plan-cache';

/** The IndexedDB databases the app creates; deleted even when the browser cannot enumerate them. */
export const APP_DATABASE_NAMES: readonly string[] = [PLAN_CACHE_DB_NAME];

/** How long one IndexedDB deletion may hold up the caller (a blocked deletion completes later). */
export const IDB_DELETE_TIMEOUT_MS = 2000;

function deleteDatabase(name: string): Promise<void> {
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, IDB_DELETE_TIMEOUT_MS);
    const done = () => {
      clearTimeout(timer);
      resolve();
    };
    try {
      const request = indexedDB.deleteDatabase(name);
      request.onsuccess = done;
      request.onerror = done;
      // Another connection is still open: the deletion completes once it closes.
      request.onblocked = done;
    } catch {
      done();
    }
  });
}

/** Delete every IndexedDB database of this origin, and the app's own ones even if they cannot be listed. */
export async function deleteAllDatabases(): Promise<void> {
  if (typeof indexedDB === 'undefined') return;
  let listed: string[] = [];
  if (typeof indexedDB.databases === 'function') {
    try {
      listed = (await indexedDB.databases())
        .map((database) => database.name)
        .filter((name): name is string => typeof name === 'string' && name.length > 0);
    } catch {
      // Enumeration refused: the app's own databases are still deleted by name.
    }
  }
  try {
    await Promise.all([...new Set([...listed, ...APP_DATABASE_NAMES])].map(deleteDatabase));
  } catch {
    // IndexedDB unavailable (private mode): nothing was stored.
  }
}

/** Delete every cache whose name `select` accepts (all caches without a selector). */
export async function deleteCaches(select: (name: string) => boolean = () => true): Promise<void> {
  if (typeof caches === 'undefined') return;
  try {
    const names = await caches.keys();
    await Promise.all(names.filter(select).map((name) => caches.delete(name)));
  } catch {
    // Cache Storage unavailable (insecure context): nothing was stored.
  }
}
