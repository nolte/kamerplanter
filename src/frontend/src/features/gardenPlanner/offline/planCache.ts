/**
 * Plan cache (REQ-053 WP 9.2, GP-UX-024 part 1, R-020): the last plan loaded per site, the bed list
 * and bed sheets of field mode, the bed summaries and the site list, kept in IndexedDB so the garden
 * can be read without a connection.
 *
 * The service worker's API cache stays latent (the backend answers `Cache-Control: no-store`,
 * MT-044, operator default #2759), so THIS cache is the offline read path. The app writes it after
 * every successful online read and reads it only when the network is unavailable:
 *
 * - **Key** `{user_key}:{tenant_key}:{site_key}` (`…:{location_key}` for a bed, `{user_key}:{tenant_key}`
 *   plus the page size for the site list; a plan read with `include=` carries the include set). Each part
 *   is URI-encoded, so a `:` inside a key cannot make two scopes collide. The record repeats both keys
 *   and a read checks them, so a record is only ever returned to its own user and tenant.
 * - **TTL** 15 minutes (R-012, the same constant as the service worker): an older record is never
 *   returned, and expired records of every table are deleted on app start, on every read and on every
 *   write.
 * - **No `localStorage`** (guardrail G-W9 a): only IndexedDB, cleared with every other database on
 *   logout, tenant switch, account erasure, a dead session and the kill switch (`pwa/offlineData.ts`).
 *   A clearing in this tab first closes this tab's connection (so its own deletion goes through and a
 *   later sign-in may cache again); a clearing in ANOTHER tab (`BroadcastChannel`) or a deletion of the
 *   database by another connection retires the cache in this tab until the page reloads — that tab may
 *   still hold the previous account's token (#2789 review S2). A write whose read began before any
 *   clearing is dropped (`offlineDataGeneration`), so a late answer cannot refill the database.
 * - **Kill switch** (G-W9 e): with `PWA_CACHING_ENABLED=false` nothing is read or written and the
 *   database is never opened.
 *
 * Every function is best-effort and never throws: a browser without IndexedDB (private mode, jsdom)
 * simply has no cache. Dexie loads with the first call (`import('./db')`), never with the route.
 */
import axios from 'axios';
import { runtimeConfig } from '@/config/runtimeConfig';
import { API_CACHE_TTL_SECONDS, isPwaCachingEnabled } from '@/pwa/cachePolicy';
import { offlineDataGeneration, onOfflineDataCleared } from '@/pwa/offlineData';
import { PLAN_CACHE_DB_NAME } from '@/pwa/storageWipe';
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


/** Whether the browser says it has no connection. */
export function browserOffline(): boolean {
  return typeof navigator !== 'undefined' && navigator.onLine === false;
}

/** A request that never got an answer (no connection, DNS, timeout) — not a refusal of the server. */
export function isNetworkFailure(error: unknown): boolean {
  return axios.isAxiosError(error) && !error.response && error.code !== 'ERR_CANCELED';
}

const TABLES: readonly PlanCacheTable[] = ['plans', 'bedLists', 'siteLists', 'bedSummaries', 'bedSheets'];

/** Set once another tab cleared or deleted the database; only a reload starts the cache again. */
let retired = false;
/** The loaded `db` module, so a local clearing can close the connection synchronously. */
let dbModule: typeof import('./db') | null = null;

function retire(): void {
  retired = true;
  dbModule?.forgetPlanCacheConnection();
}

onOfflineDataCleared((origin) => {
  if (origin === 'remote') retire();
  // A local clearing: close this tab's connection before the deletion starts; the next read opens anew.
  else dbModule?.forgetPlanCacheConnection();
});

/** Whether the plan cache may be used in this tab: kill switch on, not retired, IndexedDB present. */
function cacheUsable(): boolean {
  if (retired || typeof indexedDB === 'undefined') return false;
  try {
    return isPwaCachingEnabled(runtimeConfig().PWA_CACHING_ENABLED);
  } catch {
    return false;
  }
}

async function database(): Promise<PlanCacheDatabase | null> {
  if (!cacheUsable()) return null;
  try {
    dbModule ??= await import('./db');
    return retired ? null : dbModule.planCacheDatabase(retire);
  } catch {
    return null;
  }
}

/** Drop the records of every table that are past their TTL. */
async function purgeExpired(db: PlanCacheDatabase, now: number): Promise<void> {
  const limit = now - PLAN_CACHE_TTL_MS;
  await Promise.all(TABLES.map((table) => db[table].where('cachedAt').below(limit).delete()));
}

/**
 * App start (L2): delete what expired while the app was closed. A database that does not exist is not
 * created for it; with the kill switch off nothing is opened at all.
 */
export async function purgeExpiredPlanCache(now: number = Date.now()): Promise<void> {
  if (!cacheUsable()) return;
  try {
    if (typeof indexedDB.databases === 'function') {
      const names = (await indexedDB.databases()).map((database) => database.name);
      if (!names.includes(PLAN_CACHE_DB_NAME)) return;
    }
    const db = await database();
    if (db) await purgeExpired(db, now);
  } catch {
    // Best effort: the next read or write purges as well.
  }
}

function currentGeneration(): number | null {
  try {
    return offlineDataGeneration();
  } catch {
    return null;
  }
}

/** Write one answer and drop every record past its TTL — unless a clearing started since the read began. */
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
    await db.transaction('rw', TABLES.map((name) => db[name]), async () => {
      await purgeExpired(db, now);
      // Checked again inside the transaction: a clearing that began meanwhile wins.
      if (retired || currentGeneration() !== generation) return;
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
    await purgeExpired(db, now);
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

/**
 * A site's plan. The answer depends on `include` (#2789 review C1): a plan read with `plants` is a
 * different record than the plain one, so the include set (sorted) is part of the key.
 */
export function planEntry(scope: CacheScope, siteKey: string, include: readonly string[] = []): CacheEntry {
  const suffix = include.length > 0 ? `#include=${[...include].sort().map(encodeURIComponent).join(',')}` : '';
  return { table: 'plans', key: `${siteCacheKey(scope, siteKey)}${suffix}`, scope };
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

/** The first page of the site list, per page size (#2789 review C7): `{user_key}:{tenant_key}#limit=<n>`. */
export function siteListEntry(scope: CacheScope, limit: number): CacheEntry {
  return { table: 'siteLists', key: `${scopePrefix(scope)}#limit=${limit}`, scope };
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

/** How {@link readThrough} reads the clock and what it stores. */
export interface ReadThroughOptions<T> {
  now?: () => number;
  /**
   * What goes into the cache: the answer reduced to what the offline view needs (person-related fields
   * stripped, #2789 review L1), or `undefined` for an answer that must not be cached at all — a partial
   * or aborted one (C5). Default: the answer as it is.
   */
  toStored?: (data: T) => T | undefined;
}

/**
 * Network first, cache when there is no connection. Online, the answer is returned at once and
 * written to the cache in the background. Offline (the browser says so, or the request got no
 * answer at all) the cached answer of the same scope is returned with its time; without one the
 * read fails with {@link OfflineCacheMissError} — or, when the browser believed it was online, with
 * the original error. A refusal of the server (4xx/5xx) is never answered from the cache. With the
 * kill switch off or the cache retired it is a plain network read.
 */
export async function readThrough<T>(
  entry: CacheEntry | null,
  fetcher: () => Promise<T>,
  { now = Date.now, toStored = (data) => data }: ReadThroughOptions<T> = {},
): Promise<CachedRead<T>> {
  if (entry === null || !cacheUsable()) return { data: await fetcher(), cachedAt: null };
  if (browserOffline()) {
    const cached = await readCached<T>(entry, now());
    if (cached) return cached;
    throw new OfflineCacheMissError();
  }
  const generation = currentGeneration();
  try {
    const data = await fetcher();
    const stored = toStored(data);
    if (stored !== undefined) void writeCached(entry, stored, now(), generation);
    return { data, cachedAt: null };
  } catch (error) {
    if (!isNetworkFailure(error)) throw error;
    const cached = await readCached<T>(entry, now());
    if (cached) return cached;
    throw browserOffline() ? new OfflineCacheMissError() : error;
  }
}

/** Tests only: a fresh page — the cache is usable again and the next call opens a new connection. */
export function resetPlanCacheForTests(): void {
  retired = false;
  dbModule?.forgetPlanCacheConnection();
}
