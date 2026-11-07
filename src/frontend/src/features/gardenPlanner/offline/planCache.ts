/**
 * Plan cache (REQ-053 WP 9.2, GP-UX-024 part 1, R-020): the last plan loaded per site, the bed list
 * of field mode and the site list, kept in IndexedDB so the garden can be read without a connection.
 *
 * The service worker's API cache stays latent (the backend answers `Cache-Control: no-store`,
 * MT-044, operator default #2759), so THIS cache is the offline read path. The app writes it after
 * every successful online read and reads it only when the network is unavailable:
 *
 * - **Key** `{user_key}:{tenant_key}:{site_key}` (`{user_key}:{tenant_key}` for the site list); each
 *   part is URI-encoded, so a `:` inside a key cannot make two scopes collide. The record repeats
 *   both keys and a read checks them, so a record is only ever returned to its own user and tenant.
 * - **TTL** 15 minutes (R-012, the same constant as the service worker): an older record is never
 *   returned and is deleted on the next write.
 * - **No `localStorage`** (guardrail G-W9 a): only IndexedDB, cleared with every other database on
 *   logout, tenant switch and the kill switch (`pwa/offlineData.ts`). A write whose read began
 *   before a clearing started is dropped (`offlineDataGeneration`), so a late answer cannot refill
 *   the database a logout is emptying.
 *
 * Every function is best-effort and never throws: a browser without IndexedDB (private mode, jsdom)
 * simply has no cache. Dexie loads with the first call (`import('./db')`), never with the route.
 */
import axios from 'axios';
import { API_CACHE_TTL_SECONDS } from '@/pwa/cachePolicy';
import { offlineDataGeneration } from '@/pwa/offlineData';
import type { CachedRecord, PlanCacheDatabase, PlanCacheTable } from './db';

/** R-012: a cached answer older than this is never served. */
export const PLAN_CACHE_TTL_MS = API_CACHE_TTL_SECONDS * 1000;

/** The account and tenant a cached answer belongs to. */
export interface CacheScope {
  userKey: string;
  tenantKey: string;
}

/** What a read returns: the data and, when it came from the cache, the time it was loaded online. */
export interface CachedRead<T> {
  data: T;
  /** Epoch milliseconds of the online read the data comes from; `null` = fresh from the network. */
  cachedAt: number | null;
}

/** Offline and nothing (fresh) in the cache for this scope: the caller shows an empty state, not an error. */
export class OfflineCacheMissError extends Error {
  constructor() {
    super('offline.cache_miss');
    this.name = 'OfflineCacheMissError';
  }
}

export function isOfflineCacheMiss(error: unknown): error is OfflineCacheMissError {
  return error instanceof OfflineCacheMissError;
}

/** The part of the root state the scope is read from (the slices are typed structurally to avoid a cycle). */
export interface ScopeState {
  auth?: { user?: { key?: string | null } | null };
  tenants?: { activeTenant?: { key?: string | null } | null };
}

/** The scope of the signed-in user in the active tenant, or `null` (= nothing is cached or read). */
export function scopeFromState(state: ScopeState): CacheScope | null {
  const userKey = state.auth?.user?.key ?? null;
  const tenantKey = state.tenants?.activeTenant?.key ?? null;
  return userKey && tenantKey ? { userKey, tenantKey } : null;
}

function scopePrefix(scope: CacheScope): string {
  return `${encodeURIComponent(scope.userKey)}:${encodeURIComponent(scope.tenantKey)}`;
}

/** `{user_key}:{tenant_key}:{site_key}` — the key of a site's plan and bed list. */
export function siteCacheKey(scope: CacheScope, siteKey: string): string {
  return `${scopePrefix(scope)}:${encodeURIComponent(siteKey)}`;
}

/** `{user_key}:{tenant_key}` — the key of the site list. */
export function siteListCacheKey(scope: CacheScope): string {
  return scopePrefix(scope);
}

/** Whether the browser says it has no connection. */
export function browserOffline(): boolean {
  return typeof navigator !== 'undefined' && navigator.onLine === false;
}

/** A request that never got an answer (no connection, DNS, timeout) — not a refusal of the server. */
export function isNetworkFailure(error: unknown): boolean {
  return axios.isAxiosError(error) && !error.response && error.code !== 'ERR_CANCELED';
}

async function database(): Promise<PlanCacheDatabase | null> {
  if (typeof indexedDB === 'undefined') return null;
  try {
    const { planCacheDatabase } = await import('./db');
    return planCacheDatabase();
  } catch {
    return null;
  }
}

/** Write one answer and drop every record of the table that is past its TTL. */
function currentGeneration(): number | null {
  try {
    return offlineDataGeneration();
  } catch {
    return null;
  }
}

async function writeRecord(
  table: PlanCacheTable,
  key: string,
  scope: CacheScope,
  data: unknown,
  now: number,
  generation: number | null,
): Promise<void> {
  if (generation === null || currentGeneration() !== generation) return;
  const db = await database();
  if (!db) return;
  try {
    const record: CachedRecord = { key, userKey: scope.userKey, tenantKey: scope.tenantKey, cachedAt: now, data };
    await db.transaction('rw', db[table], async () => {
      await db[table].where('cachedAt').below(now - PLAN_CACHE_TTL_MS).delete();
      // Checked again inside the transaction: a clearing that began meanwhile wins.
      if (currentGeneration() !== generation) return;
      await db[table].put(record);
    });
  } catch {
    // Quota, private mode, a deletion in progress: the cache is an extra, the read already succeeded.
  }
}

async function readRecord<T>(
  table: PlanCacheTable,
  key: string,
  scope: CacheScope,
  now: number,
): Promise<CachedRead<T> | null> {
  const db = await database();
  if (!db) return null;
  try {
    const record = await db[table].get(key);
    if (!record || record.userKey !== scope.userKey || record.tenantKey !== scope.tenantKey) return null;
    const age = now - record.cachedAt;
    if (!Number.isFinite(age) || age < 0 || age > PLAN_CACHE_TTL_MS) return null;
    return { data: record.data as T, cachedAt: record.cachedAt };
  } catch {
    return null;
  }
}

/** One cacheable read: which table and key, in which scope. */
export interface CacheEntry {
  table: PlanCacheTable;
  key: string;
  scope: CacheScope;
}

export function planEntry(scope: CacheScope, siteKey: string): CacheEntry {
  return { table: 'plans', key: siteCacheKey(scope, siteKey), scope };
}

export function bedListEntry(scope: CacheScope, siteKey: string): CacheEntry {
  return { table: 'bedLists', key: siteCacheKey(scope, siteKey), scope };
}

/** `{user_key}:{tenant_key}:{location_key}` — the head data of a bed (`GET /locations/{key}/summary`). */
export function bedSummaryEntry(scope: CacheScope, locationKey: string): CacheEntry {
  return { table: 'bedSummaries', key: siteCacheKey(scope, locationKey), scope };
}

/** `{user_key}:{tenant_key}:{location_key}` — what the field-mode bed sheet shows (tasks and plants). */
export function bedSheetEntry(scope: CacheScope, locationKey: string): CacheEntry {
  return { table: 'bedSheets', key: siteCacheKey(scope, locationKey), scope };
}

export function siteListEntry(scope: CacheScope): CacheEntry {
  return { table: 'siteLists', key: siteListCacheKey(scope), scope };
}

/**
 * Write one answer. `generation` is the clearing generation the read began in (default: now); the
 * write is dropped when a logout, tenant switch or kill switch started since.
 */
export function writeCached(
  entry: CacheEntry,
  data: unknown,
  now: number = Date.now(),
  generation: number | null = currentGeneration(),
): Promise<void> {
  return writeRecord(entry.table, entry.key, entry.scope, data, now, generation);
}

/** The clearing generation a read begins in; pass it to {@link writeCached} when the answer is in. */
export function cacheGeneration(): number | null {
  return currentGeneration();
}

export function readCached<T>(entry: CacheEntry, now: number = Date.now()): Promise<CachedRead<T> | null> {
  return readRecord<T>(entry.table, entry.key, entry.scope, now);
}

/**
 * Network first, cache when there is no connection. Online, the answer is returned at once and
 * written to the cache in the background. Offline (the browser says so, or the request got no
 * answer at all) the cached answer of the same scope is returned with its time; without one the
 * read fails with {@link OfflineCacheMissError} — or, when the browser believed it was online, with
 * the original error. A refusal of the server (4xx/5xx) is never answered from the cache.
 */
export async function readThrough<T>(
  entry: CacheEntry | null,
  fetcher: () => Promise<T>,
  now: () => number = Date.now,
): Promise<CachedRead<T>> {
  if (entry === null) return { data: await fetcher(), cachedAt: null };
  if (browserOffline()) {
    const cached = await readCached<T>(entry, now());
    if (cached) return cached;
    throw new OfflineCacheMissError();
  }
  const generation = currentGeneration();
  try {
    const data = await fetcher();
    void writeCached(entry, data, now(), generation);
    return { data, cachedAt: null };
  } catch (error) {
    if (!isNetworkFailure(error)) throw error;
    const cached = await readCached<T>(entry, now());
    if (cached) return cached;
    throw browserOffline() ? new OfflineCacheMissError() : error;
  }
}
