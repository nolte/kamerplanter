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
import Dexie, { type EntityTable } from 'dexie';
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

  constructor() {
    super(PLAN_CACHE_DB_NAME);
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
    const db = new PlanCacheDatabase();
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

/** Close this tab's connection for good; the next {@link planCacheDatabase} call opens a new one. */
export function forgetPlanCacheConnection(): void {
  instance?.close({ disableAutoOpen: true });
  instance = null;
}
