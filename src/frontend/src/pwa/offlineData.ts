/**
 * The app side of the offline data boundary (UI-NFR-012 SR-019, REQ-053 WP 9.1, #2741).
 *
 * Guardrail G-W9 (a)/(b): API data lives only in Cache Storage and IndexedDB under a namespace that
 * carries `user_key` AND `tenant_key`, never in `localStorage`; a logout and a tenant switch empty
 * both completely before the page reloads. The worker learns the namespace from
 * {@link postNamespace} — it never parses a token.
 *
 * Every function here is best-effort and never throws: a browser without Cache Storage, IndexedDB
 * or a service worker simply has nothing to clear, and a logout must never fail on cleanup.
 */
import {
  SW_MESSAGE_CLEAR_DATA,
  SW_MESSAGE_SET_NAMESPACE,
  isPublicCacheName,
} from './cachePolicy';

/** How long one IndexedDB deletion may hold up a reload (a blocked deletion completes later). */
const IDB_DELETE_TIMEOUT_MS = 2000;

interface Namespace {
  userKey: string | null;
  tenantKey: string | null;
}

let lastNamespace: Namespace = { userKey: null, tenantKey: null };

function serviceWorkerContainer(): ServiceWorkerContainer | null {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return null;
  return navigator.serviceWorker ?? null;
}

/** Post a message to the controlling worker, or to the active one of this scope. */
async function postToWorker(message: Record<string, unknown>): Promise<void> {
  const container = serviceWorkerContainer();
  if (!container) return;
  try {
    if (container.controller) {
      container.controller.postMessage(message);
      return;
    }
    // `getRegistration` resolves at once (unlike `ready`, which never settles without a worker).
    const registration = await container.getRegistration();
    registration?.active?.postMessage(message);
  } catch {
    // No worker to tell: nothing is cached by one either.
  }
}

/** Tell the worker which user and tenant its API cache belongs to (`null` = cache nothing). */
export function postNamespace(userKey: string | null, tenantKey: string | null): Promise<void> {
  lastNamespace = { userKey, tenantKey };
  return postToWorker({ type: SW_MESSAGE_SET_NAMESPACE, userKey, tenantKey });
}

/** Re-send the last namespace, e.g. after a new worker took control of the page. */
export function repostNamespace(): Promise<void> {
  return postNamespace(lastNamespace.userKey, lastNamespace.tenantKey);
}

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

async function clearIndexedDb(): Promise<void> {
  if (typeof indexedDB === 'undefined' || typeof indexedDB.databases !== 'function') return;
  try {
    const databases = await indexedDB.databases();
    await Promise.all(
      databases
        .map((database) => database.name)
        .filter((name): name is string => typeof name === 'string' && name.length > 0)
        .map(deleteDatabase),
    );
  } catch {
    // IndexedDB unavailable (private mode): nothing was stored.
  }
}

async function clearCaches(includePublic: boolean): Promise<void> {
  if (typeof caches === 'undefined') return;
  try {
    const names = await caches.keys();
    await Promise.all(
      names.filter((name) => includePublic || !isPublicCacheName(name)).map((name) => caches.delete(name)),
    );
  } catch {
    // Cache Storage unavailable (insecure context): nothing was stored.
  }
}

/**
 * Empty every cache and IndexedDB database that can hold API data — the namespaced API caches, the
 * worker's namespace state and every IndexedDB database. The public build caches (precache, static
 * assets, runtime config) stay so the app shell keeps loading; they hold no personal data.
 *
 * Await this BEFORE `window.location.reload()` on logout and tenant switch (G-W9 b).
 */
export async function clearOfflineData(): Promise<void> {
  lastNamespace = { userKey: null, tenantKey: null };
  await postToWorker({ type: SW_MESSAGE_CLEAR_DATA });
  await Promise.all([clearCaches(false), clearIndexedDb()]);
}

/** Kill switch (G-W9 e): everything goes, the app shell caches included. */
export async function clearAllOfflineStorage(): Promise<void> {
  lastNamespace = { userKey: null, tenantKey: null };
  await Promise.all([clearCaches(true), clearIndexedDb()]);
}
