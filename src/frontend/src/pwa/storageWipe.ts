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

/**
 * The offline write buffer (REQ-053 WP 9.4, `features/gardenPlanner/offline/queueDb.ts`): "Done", note and
 * photo captured without a connection. Its own database, not a table of the plan cache: the plan cache drops
 * every record past its 15-minute TTL, the buffer must keep an entry until it is sent or discarded — also across
 * a tenant switch and a session that ended without a logout (UI-NFR-012 R-050/R-051). Listed here so the kill
 * switch deletes it even where the databases cannot be enumerated; an explicit logout and the account erasure
 * delete only the rows of that user (`pwa/writeQueueWipe.ts`).
 */
export const WRITE_QUEUE_DB_NAME = 'kp-write-queue';

/** The IndexedDB databases the app creates; deleted even when the browser cannot enumerate them. */
export const APP_DATABASE_NAMES: readonly string[] = [PLAN_CACHE_DB_NAME, WRITE_QUEUE_DB_NAME];

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

/**
 * Delete every IndexedDB database of this origin, and the app's own ones even if they cannot be listed — except
 * the names in `keep` (the offline write buffer survives a tenant switch and a session that ended without an
 * explicit logout, UI-NFR-012 R-050/R-051; its entries stay bound to their own user and tenant).
 */
export async function deleteAllDatabases(keep: readonly string[] = []): Promise<void> {
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
    const names = [...new Set([...listed, ...APP_DATABASE_NAMES])].filter((name) => !keep.includes(name));
    await Promise.all(names.map(deleteDatabase));
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
