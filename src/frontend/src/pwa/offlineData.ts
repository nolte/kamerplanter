/**
 * The app side of the offline data boundary (UI-NFR-012 SR-019, REQ-053 WP 9.1, #2741).
 *
 * Guardrail G-W9 (a)/(b): API data lives only in Cache Storage and IndexedDB under a namespace that
 * carries `user_key` AND `tenant_key`, never in `localStorage`; a logout and a tenant switch empty
 * both completely before the page reloads. The worker learns the namespace of THIS tab from
 * {@link postNamespace} — it never parses a token.
 *
 * Every function here is best-effort and never throws: a browser without Cache Storage, IndexedDB
 * or a service worker simply has nothing to clear, and a logout must never fail on cleanup.
 */
import { SW_MESSAGE_CLEAR_DATA, SW_MESSAGE_SET_NAMESPACE, isPublicCacheName } from './cachePolicy';
import { deleteAllDatabases, deleteCaches } from './storageWipe';

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

/** Tell the worker which user and tenant this tab's API cache belongs to (`null` = cache nothing). */
export function postNamespace(userKey: string | null, tenantKey: string | null): Promise<void> {
  lastNamespace = { userKey, tenantKey };
  return postToWorker({ type: SW_MESSAGE_SET_NAMESPACE, userKey, tenantKey });
}

/** Re-send the last namespace, e.g. after a new worker took control of the page. */
export function repostNamespace(): Promise<void> {
  return postNamespace(lastNamespace.userKey, lastNamespace.tenantKey);
}

/**
 * Empty every cache and IndexedDB database that can hold API data — the namespaced API caches, the
 * worker's namespace state and every IndexedDB database. The public build caches (precache, static
 * assets) stay so the app shell keeps loading; they hold no personal data. The worker is told which
 * user's session ended, so it invalidates that user's namespace in every tab.
 *
 * Await this BEFORE `window.location.reload()` on logout and tenant switch (G-W9 b).
 */
export async function clearOfflineData(): Promise<void> {
  const { userKey } = lastNamespace;
  lastNamespace = { userKey: null, tenantKey: null };
  await postToWorker({ type: SW_MESSAGE_CLEAR_DATA, userKey });
  await Promise.all([deleteCaches((name) => !isPublicCacheName(name)), deleteAllDatabases()]);
}

/** Kill switch (G-W9 e): everything goes, the app shell caches included. */
export async function clearAllOfflineStorage(): Promise<void> {
  lastNamespace = { userKey: null, tenantKey: null };
  await Promise.all([deleteCaches(), deleteAllDatabases()]);
}
