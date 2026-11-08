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
import { WRITE_QUEUE_DB_NAME, deleteAllDatabases, deleteCaches } from './storageWipe';
import { deleteWriteQueueEntriesOf } from './writeQueueWipe';

interface Namespace {
  userKey: string | null;
  tenantKey: string | null;
}

let lastNamespace: Namespace = { userKey: null, tenantKey: null };
/**
 * Moves at the START of every clearing. An app-side cache write (the plan cache, REQ-053 WP 9.2)
 * remembers the generation its read began in and is dropped when it has moved: an answer that
 * lands after a logout or tenant switch began never re-fills the database that is being emptied.
 */
let generation = 0;

/** The current clearing generation (see {@link clearOfflineData}). */
export function offlineDataGeneration(): number {
  return generation;
}

/**
 * Every tab of the origin hears a clearing (#2789 review S2): the generation is per tab, so without
 * this a second tab of the same account — its access token still valid for up to 15 minutes — would
 * finish an in-flight write, or start a new one, into the database the first tab just deleted.
 *
 * The message names whose session ended (#2789 verification L1): a tab acts on it only when it holds
 * that user — an anonymous tab's bootstrap clearing, or another account's logout, must not switch off
 * the cache of a tab whose session is alive. The kill switch (`all`) concerns every tab.
 */
export const OFFLINE_CLEAR_CHANNEL = 'kp-offline';
const CLEAR_MESSAGE = 'offline-data-cleared';

/**
 * What the plan cache hears:
 * - `local`: this tab starts a clearing; `local-done`: it has finished (the databases are deleted);
 * - `remote`: another tab cleared the session this tab holds (or the kill switch fired);
 * - `foreign`: another tab cleared a session this tab does NOT hold — its deletion is not about us;
 * - `session`: this tab now has a complete user + tenant namespace (a sign-in, a tenant switch).
 */
export type OfflineDataEvent = 'local' | 'local-done' | 'remote' | 'foreign' | 'session';
type EventListener = (event: OfflineDataEvent) => void;
const listeners = new Set<EventListener>();

/** Subscribe to {@link OfflineDataEvent}s. Returns the unsubscribe. */
export function onOfflineDataEvent(listener: EventListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function emit(event: OfflineDataEvent): void {
  if (event === 'local' || event === 'remote') generation += 1;
  listeners.forEach((listener) => {
    try {
      listener(event);
    } catch {
      // A listener's failure never stops the clearing.
    }
  });
}

interface ClearMessage {
  type: typeof CLEAR_MESSAGE;
  /** The user whose session ended; `null` = none (an anonymous tab); `all` = the kill switch. */
  userKey: string | null;
  all?: boolean;
}

/** Whether a clearing in another tab concerns this tab's session. */
function concernsThisTab(message: ClearMessage): boolean {
  if (message.all) return true;
  return message.userKey !== null && message.userKey === lastNamespace.userKey;
}

let channel: BroadcastChannel | null = null;
if (typeof BroadcastChannel !== 'undefined') {
  try {
    channel = new BroadcastChannel(OFFLINE_CLEAR_CHANNEL);
    // Node (tests) keeps the process alive for an open channel; a browser has no `unref`.
    (channel as BroadcastChannel & { unref?: () => void }).unref?.();
    channel.onmessage = (event: MessageEvent) => {
      const message = event.data as ClearMessage | null;
      if (message?.type !== CLEAR_MESSAGE) return;
      emit(concernsThisTab(message) ? 'remote' : 'foreign');
    };
  } catch {
    channel = null;
  }
}

function announceClearing(userKey: string | null, all = false): void {
  emit('local');
  try {
    const message: ClearMessage = { type: CLEAR_MESSAGE, userKey, all };
    channel?.postMessage(message);
  } catch {
    // No channel (old browser): the other tabs still lose their database connection (`versionchange`).
  }
}

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
  const changed = lastNamespace.userKey !== userKey || lastNamespace.tenantKey !== tenantKey;
  lastNamespace = { userKey, tenantKey };
  if (changed && userKey && tenantKey) emit('session');
  return postToWorker({ type: SW_MESSAGE_SET_NAMESPACE, userKey, tenantKey });
}

/**
 * The confirmation an explicit logout needs before it discards the user's unsent offline entries (REQ-053 WP 9.4,
 * UI-NFR-012 R-056 c). The app bar sets it after the user confirmed (or after it counted none); the session
 * listener takes it. A logout without it — the count could not even be loaded — keeps the entries.
 */
let approvedDiscard: string | null = null;

/** The user confirmed (or nothing was buffered): their logout may discard their unsent entries. */
export function approveWriteQueueDiscard(userKey: string | null): void {
  approvedDiscard = userKey;
}

/** Whether `userKey`'s logout was confirmed; the approval is used up. */
export function takeWriteQueueDiscardApproval(userKey: string | null): boolean {
  const approved = userKey !== null && approvedDiscard === userKey;
  approvedDiscard = null;
  return approved;
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
 *
 * The offline write buffer (REQ-053 WP 9.4) is the one exception (UI-NFR-012 R-050/R-051): unsent entries are
 * not API data but the user's own work, bound to their `user_key` + `tenant_key` and never shown or sent in another
 * scope. A tenant switch, a forced sign-out, a refused refresh keep them. Only `discardWriteQueueOf` — the explicit,
 * confirmed logout and the account erasure — deletes the entries of that user (and no one else's).
 */
export async function clearOfflineData({ discardWriteQueueOf }: { discardWriteQueueOf?: string | null } = {}): Promise<void> {
  const { userKey } = lastNamespace;
  announceClearing(userKey);
  lastNamespace = { userKey: null, tenantKey: null };
  try {
    await postToWorker({ type: SW_MESSAGE_CLEAR_DATA, userKey });
    await Promise.all([
      deleteCaches((name) => !isPublicCacheName(name)),
      deleteAllDatabases([WRITE_QUEUE_DB_NAME]),
      discardWriteQueueOf ? deleteWriteQueueEntriesOf(discardWriteQueueOf) : Promise.resolve(),
    ]);
  } finally {
    emit('local-done');
  }
}

/** Kill switch (G-W9 e): everything goes, the app shell caches and the offline write buffer included. */
export async function clearAllOfflineStorage(): Promise<void> {
  announceClearing(lastNamespace.userKey, true);
  lastNamespace = { userKey: null, tenantKey: null };
  try {
    await Promise.all([deleteCaches(), deleteAllDatabases()]);
  } finally {
    emit('local-done');
  }
}
