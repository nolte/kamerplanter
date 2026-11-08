/**
 * The IndexedDB database of the offline write buffer (REQ-053 WP 9.4, GP-UX-024 part 2; UI-NFR-012 R-016/R-018).
 *
 * The only module of the buffer that imports `dexie`; `queue.ts` loads it with a dynamic `import()`, so the
 * library stays its own chunk (shared with the plan cache) and is never part of a route budget.
 *
 * Its own database (`kp-write-queue`), not a table of the plan cache: the plan cache deletes every record past
 * its 15-minute TTL on each access, while a buffered entry must survive until it is sent or discarded (R-018).
 * The name is in `APP_DATABASE_NAMES`, so the kill switch deletes it with every other database; the logout,
 * tenant switch and dead-session clearings skip it (UI-NFR-012 R-050/R-051, `pwa/offlineData.ts`).
 *
 * `seq` is an auto-increment primary key: its order IS the capture order, so FIFO (R-023) needs no clock.
 */
import Dexie, { type EntityTable } from 'dexie';
import { WRITE_QUEUE_DB_NAME } from '@/pwa/storageWipe';
import type { QueueEntry } from './queueTypes';

export class WriteQueueDatabase extends Dexie {
  entries!: EntityTable<QueueEntry, 'seq'>;

  constructor() {
    super(WRITE_QUEUE_DB_NAME);
    this.version(1).stores({
      entries: '++seq, &id, [userKey+tenantKey], status, capturedAt',
    });
  }
}

let instance: WriteQueueDatabase | null = null;

/**
 * The one connection of this tab. Another connection deleting the database (a clearing in this or another
 * tab, the kill switch) fires `versionchange`: the handler closes for good (`disableAutoOpen`) instead of
 * Dexie's default reopen, so a tab that may still hold the previous account's token never writes into a
 * fresh database (the same rule as the plan cache, #2789 review S2). `onDeletedElsewhere` lets the queue decide.
 */
export function writeQueueDatabase(onDeletedElsewhere: () => void): WriteQueueDatabase {
  if (instance === null) {
    const db = new WriteQueueDatabase();
    db.on('versionchange', () => {
      db.close({ disableAutoOpen: true });
      if (instance === db) instance = null;
      onDeletedElsewhere();
      return false;
    });
    instance = db;
  }
  return instance;
}

/** Close this tab's connection for good; the next {@link writeQueueDatabase} call opens a new one. */
export function forgetWriteQueueConnection(): void {
  instance?.close({ disableAutoOpen: true });
  instance = null;
}
