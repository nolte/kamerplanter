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

/** The one connection of this tab; Dexie closes it by itself when a deletion asks (`versionchange`). */
export function planCacheDatabase(): PlanCacheDatabase {
  instance ??= new PlanCacheDatabase();
  return instance;
}
