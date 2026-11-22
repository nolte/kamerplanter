/**
 * Delete one user's entries of the offline write buffer (REQ-053 WP 9.4) — an explicit logout (after the user
 * confirmed it) and the account erasure. The rows of other users and the database itself stay: a tenant switch,
 * a refused refresh or another account's logout on the same device never discard someone's unsent entries
 * (UI-NFR-012 R-050/R-051).
 *
 * Plain IndexedDB, no Dexie: this runs from the session listener in the app shell. Best effort, never throws, and
 * never creates the database (an open that would create it is aborted).
 */
import { WRITE_QUEUE_DB_NAME } from './storageWipe';

/** The object store and compound index Dexie created for `entries: '++seq, &id, [userKey+tenantKey], …'`. */
const STORE = 'entries';
/** The per-user retention notices (schema v2): the user's count goes with their entries. */
const NOTICES = 'notices';
const OWNER_INDEX = '[userKey+tenantKey]';
const TIMEOUT_MS = 2000;

export function deleteWriteQueueEntriesOf(userKey: string): Promise<void> {
  if (typeof indexedDB === 'undefined' || !userKey) return Promise.resolve();
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, TIMEOUT_MS);
    const done = () => {
      clearTimeout(timer);
      resolve();
    };
    try {
      const request = indexedDB.open(WRITE_QUEUE_DB_NAME);
      request.onupgradeneeded = () => {
        // It did not exist: do not create it.
        request.transaction?.abort();
      };
      request.onerror = done;
      request.onblocked = done;
      request.onsuccess = () => {
        const db = request.result;
        try {
          if (!db.objectStoreNames.contains(STORE)) {
            db.close();
            done();
            return;
          }
          const stores = db.objectStoreNames.contains(NOTICES) ? [STORE, NOTICES] : [STORE];
          const transaction = db.transaction(stores, 'readwrite');
          const entries = transaction.objectStore(STORE);
          // Every tenant of the user: [userKey] < [userKey, any string] < [userKey, []]. A key cursor: the rows
          // (photo bytes) are never read, each is deleted by its primary key.
          const range = IDBKeyRange.bound([userKey], [userKey, []]);
          const cursor = entries.index(OWNER_INDEX).openKeyCursor(range);
          cursor.onsuccess = () => {
            const current = cursor.result;
            if (current) {
              entries.delete(current.primaryKey);
              current.continue();
            }
          };
          if (stores.length === 2) transaction.objectStore(NOTICES).delete(userKey);
          transaction.oncomplete = () => {
            db.close();
            done();
          };
          transaction.onerror = () => {
            db.close();
            done();
          };
          transaction.onabort = transaction.onerror;
        } catch {
          db.close();
          done();
        }
      };
    } catch {
      done();
    }
  });
}
