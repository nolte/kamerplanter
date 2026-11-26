/**
 * The IndexedDB database of the plan cache (REQ-053 WP 9.2, GP-UX-024 part 1; UI-NFR-012 R-012/R-020).
 *
 * Dexie is the only module that imports `dexie`; `planCache.ts` loads this module with a dynamic
 * `import()`, so the library is its own chunk and never part of the garden-planner route budget.
 *
 * One record per cached answer. Every record carries `user_key` AND `tenant_key` (guardrail G-W9 a),
 * and its primary key starts with both: `{user_key}:{tenant_key}:{site_key}` for a plan and a bed
 * list, `{user_key}:{tenant_key}:{location_key}` for a bed summary and a field-mode bed sheet,
 * `{user_key}:{tenant_key}` for the site list. Logout, tenant switch and the kill switch delete
 * this database with every other one (`pwa/offlineData.ts`, `pwa/storageWipe.ts`); there is no
 * second clearing mechanism here.
 */
import Dexie, { type DexieOptions, type EntityTable } from 'dexie';
import { PLAN_CACHE_DB_NAME } from '@/pwa/storageWipe';

/** One cached API answer. `data` is the JSON body exactly as the server sent it. */
export interface CachedRecord {
  key: string;
  userKey: string;
  tenantKey: string;
  /** Epoch milliseconds of the successful online read that wrote the record. */
  cachedAt: number;
  data: unknown;
}

export type PlanCacheTable = 'plans' | 'bedLists' | 'siteLists' | 'bedSummaries' | 'bedSheets';

export class PlanCacheDatabase extends Dexie {
  plans!: EntityTable<CachedRecord, 'key'>;
  bedLists!: EntityTable<CachedRecord, 'key'>;
  siteLists!: EntityTable<CachedRecord, 'key'>;
  bedSummaries!: EntityTable<CachedRecord, 'key'>;
  bedSheets!: EntityTable<CachedRecord, 'key'>;

  constructor(options?: DexieOptions) {
    super(PLAN_CACHE_DB_NAME, options);
    this.version(1).stores({
      plans: 'key, cachedAt',
      bedLists: 'key, cachedAt',
      siteLists: 'key, cachedAt',
    });
    // The bed view and the field-mode bed sheet (WP 9.2 follow-up): same database, same clearing.
    this.version(2).stores({
      bedSummaries: 'key, cachedAt',
      bedSheets: 'key, cachedAt',
    });
  }
}

let instance: PlanCacheDatabase | null = null;
/** The native open requests of {@link instance} — what a close must not leave behind (#3082). */
let openRequests = new Set<IDBOpenDBRequest>();

/**
 * The browser's `indexedDB`, with every `open` recorded in `requests`. Dexie keeps its open request to itself, and
 * `close()` cannot reach one still in flight: an upgrade that is running goes on, a queued open still connects
 * later (#3082). With the request at hand, {@link forgetPlanCacheConnection} can end both.
 */
function recordingFactory(native: IDBFactory, requests: Set<IDBOpenDBRequest>): IDBFactory {
  const factory: Pick<IDBFactory, 'open' | 'deleteDatabase' | 'cmp'> & Partial<Pick<IDBFactory, 'databases'>> = {
    open: (name, version) => {
      const request = version === undefined ? native.open(name) : native.open(name, version);
      requests.add(request);
      const settled = () => requests.delete(request);
      request.addEventListener('success', settled);
      request.addEventListener('error', settled);
      return request;
    },
    deleteDatabase: (name) => native.deleteDatabase(name),
    cmp: (first, second) => native.cmp(first, second),
  };
  // Only where the browser has it: without `databases`, Dexie would keep a names database of its own.
  if (typeof native.databases === 'function') factory.databases = () => native.databases();
  return factory as IDBFactory;
}

/**
 * End an open that has not settled (#3082). An upgrade still running is aborted now — a document entering the
 * back/forward cache with its version change transaction would hold every later open of the database, in every
 * document of the origin, until it is evicted. An open still queued cannot be cancelled (IndexedDB has no way),
 * so whatever it brings later is undone at once: an upgrade aborted, a connection closed.
 */
function abandon(request: IDBOpenDBRequest): void {
  const abortUpgrade = () => {
    try {
      request.transaction?.abort();
    } catch (error) {
      // Already committing or finished (InvalidStateError): nothing to abort; the connection is closed below or by
      // Dexie. An expected race, so a debug line and not an error report.
      console.debug('plan cache: upgrade no longer abortable', error);
    }
  };
  if (request.readyState === 'pending') abortUpgrade();
  request.addEventListener('upgradeneeded', abortUpgrade);
  // `close()` never throws; a connection that arrives after the close is let go at once.
  request.addEventListener('success', () => request.result.close());
}

/**
 * The one connection of this tab, or `null` once it was retired.
 *
 * Another connection deleting the database (a logout or tenant switch in this or another tab, the kill
 * switch) fires `versionchange`. Dexie's default closes and REOPENS on the next access, which would let
 * this tab — possibly still holding the previous account's token — write that account's rows into a
 * fresh database (#2789 review S2). So the handler closes for good (`disableAutoOpen: true`), returns
 * `false` to stop the default, and `onDeletedElsewhere` lets the plan cache decide whether to retire.
 */
export function planCacheDatabase(onDeletedElsewhere: () => void): PlanCacheDatabase {
  if (instance === null) {
    const requests = new Set<IDBOpenDBRequest>();
    const db = new PlanCacheDatabase(
      typeof indexedDB === 'undefined' ? undefined : { indexedDB: recordingFactory(indexedDB, requests) },
    );
    db.on('versionchange', () => {
      db.close({ disableAutoOpen: true });
      if (instance === db) instance = null;
      onDeletedElsewhere();
      return false;
    });
    instance = db;
    openRequests = requests;
  }
  return instance;
}

/**
 * Close this tab's connection for good, including an open still in flight; the next {@link planCacheDatabase}
 * call opens a new one.
 */
export function forgetPlanCacheConnection(): void {
  openRequests.forEach(abandon);
  openRequests = new Set();
  instance?.close({ disableAutoOpen: true });
  instance = null;
}
