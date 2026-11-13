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
 *   later sign-in may cache again); a clearing in ANOTHER tab for the session this tab holds
 *   (`BroadcastChannel`), or a deletion of the database by another connection that no broadcast
 *   explains, retires the cache in this tab until it starts a new session or reloads — that tab may
 *   still hold the previous account's token (#2789 review S2, verification L1). A write whose read began before any
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
import { offlineDataGeneration, onOfflineDataEvent } from '@/pwa/offlineData';
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

/**
 * Retirement (#2789 reviews S2, verification L1). Set when another tab ended the session this tab holds
 * (`remote`), or the database was deleted by a connection that is neither this tab's own clearing nor a
 * clearing for a session this tab does not hold. It lasts until this tab starts a new complete session
 * (`session`: a sign-in, a tenant switch) or the page reloads — never just until the next read.
 */
let retired = false;
/** When a deletion by another connection retired the cache; a `foreign` broadcast arriving later undoes it. */
let retiredByDeletionAt: number | null = null;
/** This tab is clearing: nothing opens a connection until it is done, and its own deletion retires nothing. */
let localClearing = false;
/** A `foreign` broadcast came in: a deletion seen until then belongs to that other session. */
let foreignDeletionUntil = 0;
/** How far apart the broadcast and the `versionchange` of the same clearing may arrive. */
const SAME_CLEARING_WINDOW_MS = 5000;
/** The loaded `db` module, so a clearing can close the connection synchronously. */
let dbModule: typeof import('./db') | null = null;

function closeConnection(): void {
  dbModule?.forgetPlanCacheConnection();
}

/** `versionchange`: another connection deletes the database (db.ts has already closed ours). */
function deletedElsewhere(): void {
  if (localClearing || Date.now() < foreignDeletionUntil) return;
  retired = true;
  retiredByDeletionAt = Date.now();
}

onOfflineDataEvent((event) => {
  switch (event) {
    case 'local':
      // Close before the deletion starts; nothing reopens until it is done.
      localClearing = true;
      closeConnection();
      break;
    case 'local-done':
      localClearing = false;
      break;
    case 'remote':
      retired = true;
      retiredByDeletionAt = null;
      closeConnection();
      break;
    case 'foreign':
      foreignDeletionUntil = Date.now() + SAME_CLEARING_WINDOW_MS;
      if (retiredByDeletionAt !== null && Date.now() - retiredByDeletionAt < SAME_CLEARING_WINDOW_MS) {
        retired = false;
        retiredByDeletionAt = null;
      }
      break;
    case 'session':
      retired = false;
      retiredByDeletionAt = null;
      closeConnection();
      break;
  }
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
  if (!cacheUsable() || localClearing) return null;
  try {
    dbModule ??= await import('./db');
    return retired || localClearing ? null : dbModule.planCacheDatabase(deletedElsewhere);
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

/**
 * `{user_key}:{tenant_key}:{location_key}#lang=<language>` — what the field-mode bed sheet shows (tasks and
 * plants). The plants carry a species name the server worded in the request's language (`Accept-Language`,
 * #2902), so the language is part of the key: offline after a language switch the sheet is a cache miss rather
 * than a sheet with the names of the previous language.
 */
export function bedSheetEntry(scope: CacheScope, locationKey: string, language = 'de'): CacheEntry {
  return {
    table: 'bedSheets',
    key: `${siteCacheKey(scope, locationKey)}#lang=${encodeURIComponent(language)}`,
    scope,
  };
}

/** The first page of the site list, per page size (#2789 review C7): `{user_key}:{tenant_key}#limit=<n>`. */
export function siteListEntry(scope: CacheScope, limit: number): CacheEntry {
  return { table: 'siteLists', key: `${scopePrefix(scope)}#limit=${limit}`, scope };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** The plan collections whose items may carry a free-text `notes` / `description` (locations, garden objects, …). */
const PLAN_ITEM_LISTS = ['locations', 'garden_objects', 'slots', 'plants', 'zones'] as const;

/** An item without its free text: `notes` and `description` blanked where present. */
function withoutFreeText(item: unknown): unknown {
  if (!isRecord(item)) return item;
  const out: Record<string, unknown> = { ...item };
  if ('notes' in out) out.notes = null;
  if ('description' in out) out.description = null;
  return out;
}

/** A task of the bed sheet as the cache keeps it: nothing about a person and no completion text. */
function storedTask(task: unknown): unknown {
  if (!isRecord(task)) return task;
  return {
    ...task,
    assigned_to_user_key: null,
    completion_notes: null,
    photo_refs: [],
    difficulty_rating: null,
    quality_rating: null,
    actual_duration_minutes: null,
  };
}

/**
 * What a table keeps of an answer (wave 9 acceptance #2757, review findings GDPR-004 and the follow-up
 * review of PR #2817): nothing about a person and no free text — the offline views show neither. All data
 * minimisation of the plan cache sits HERE, at the one write every caller goes through (`writeCached`,
 * and through it `readThrough`), so no caller can forget it. The answer the caller returns to its view
 * is untouched. `undefined` means: store nothing.
 *
 * - `plans`: `plan.plan_updated_by_name` (a member's display name) and the `notes` / `description` of every
 *   location, garden object, slot, plant and zone.
 * - `bedSummaries`: `notes` and `description` of the bed.
 * - `bedSheets`: only a complete answer (both reads answered, none aborted); tasks without assignee,
 *   completion text, photos, ratings and duration, plants without their cover photo; the `complete` flag
 *   itself is never stored (#2789 review L1, C5).
 */
export function storedProjection(table: PlanCacheTable, data: unknown): unknown {
  if (!isRecord(data)) return data;
  if (table === 'plans') {
    const out: Record<string, unknown> = { ...data };
    if (isRecord(data.plan)) out.plan = { ...data.plan, plan_updated_by_name: null };
    for (const list of PLAN_ITEM_LISTS) {
      const items = data[list];
      if (Array.isArray(items)) out[list] = items.map(withoutFreeText);
    }
    return out;
  }
  if (table === 'bedSummaries') return { ...data, notes: null, description: null };
  if (table === 'bedSheets') {
    if (data.complete !== true || !Array.isArray(data.plants) || !Array.isArray(data.tasks))
      return undefined;
    return {
      tasks: data.tasks.map(storedTask),
      plants: data.plants.map((plant) =>
        isRecord(plant) ? { ...plant, cover_photo_ref: null } : plant,
      ),
    };
  }
  return data;
}

/**
 * Write one answer. `generation` is the clearing generation the read began in (default: now); the
 * write is dropped when a logout, tenant switch or kill switch started since. What is written is the
 * {@link storedProjection} of `data`; nothing is written when the projection is `undefined`.
 */
export async function writeCached(
  entry: CacheEntry,
  data: unknown,
  now: number = Date.now(),
  generation: number | null = currentGeneration(),
): Promise<void> {
  const stored = storedProjection(entry.table, data);
  if (stored === undefined) return;
  return writeRecord(entry.table, entry.key, entry.scope, stored, now, generation);
}

/** The clearing generation a read begins in; pass it to {@link writeCached} when the answer is in. */
export function cacheGeneration(): number | null {
  return currentGeneration();
}

export function readCached<T>(entry: CacheEntry, now: number = Date.now()): Promise<CachedRead<T> | null> {
  return readRecord<T>(entry.table, entry.key, entry.scope, now);
}

/** How {@link readThrough} reads the clock. What it stores is {@link storedProjection}. */
export interface ReadThroughOptions {
  now?: () => number;
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
  { now = Date.now }: ReadThroughOptions = {},
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
    void writeCached(entry, data, now(), generation);
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
  retiredByDeletionAt = null;
  localClearing = false;
  foreignDeletionUntil = 0;
  dbModule?.forgetPlanCacheConnection();
}
