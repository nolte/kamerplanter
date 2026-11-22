/**
 * Which tab's API answers go into which cache (REQ-053 WP 9.1, #2741, review finding 1).
 *
 * The worker serves every tab of the origin. Two tabs can belong to different users (one tab logged
 * out and in as someone else) or to different tenants, so ONE global namespace would let a tab read
 * and write another account's answers. The registry keeps the namespace per client (`Client.id`):
 * a request is answered from, and written into, only the namespace of the client that sent it.
 *
 * A generation counter per cache name closes the logout race (finding 2): a write that started
 * before its namespace was invalidated sees a different generation when it lands and is undone.
 *
 * Pure: no worker API. The worker persists {@link NamespaceRegistry.toJSON} so a restarted worker
 * keeps the mapping, and passes the live client ids to {@link NamespaceRegistry.prune}.
 */
import { API_CACHE_PREFIX } from './cachePolicy';

export interface NamespaceSnapshot {
  clients: Record<string, string>;
}

export class NamespaceRegistry {
  private readonly byClient = new Map<string, string>();
  private readonly generations = new Map<string, number>();

  static fromJSON(value: unknown): NamespaceRegistry {
    const registry = new NamespaceRegistry();
    const clients = (value as NamespaceSnapshot | null)?.clients;
    if (clients && typeof clients === 'object') {
      for (const [clientId, cacheName] of Object.entries(clients)) {
        if (typeof cacheName === 'string' && cacheName.startsWith(API_CACHE_PREFIX)) {
          registry.byClient.set(clientId, cacheName);
        }
      }
    }
    return registry;
  }

  toJSON(): NamespaceSnapshot {
    return { clients: Object.fromEntries(this.byClient) };
  }

  /** The namespace of one client, or `null` (= network only). */
  forClient(clientId: string | null | undefined): string | null {
    if (!clientId) return null;
    return this.byClient.get(clientId) ?? null;
  }

  /** The current generation of a cache name; it moves whenever the name is invalidated. */
  generationOf(cacheName: string): number {
    return this.generations.get(cacheName) ?? 0;
  }

  /**
   * Bind (or with `null` unbind) a client. Returns the cache names no client uses any more — the
   * caller deletes exactly those. A name another client still uses is never returned.
   */
  set(clientId: string, cacheName: string | null): string[] {
    const previous = this.byClient.get(clientId) ?? null;
    if (cacheName) this.byClient.set(clientId, cacheName);
    else this.byClient.delete(clientId);
    if (previous && previous !== cacheName && !this.inUse().has(previous)) {
      this.bump(previous);
      return [previous];
    }
    return [];
  }

  /**
   * A session of `userPrefix` (`kp:{user_key}:`) ended: unbind every client of that user in every
   * tab and invalidate all of the user's namespaces. Returns the names to delete. Without a prefix
   * the ending client's own namespace decides which user it was.
   */
  endSession(userPrefix: string | null, senderClientId: string | null): string[] {
    const senderName = this.forClient(senderClientId);
    const prefix = userPrefix ?? (senderName ? senderName.slice(0, senderName.lastIndexOf(':') + 1) : null);
    const ended = new Set<string>();
    if (senderName) ended.add(senderName);
    for (const [clientId, cacheName] of [...this.byClient]) {
      if (cacheName === senderName || (prefix && cacheName.startsWith(prefix))) {
        ended.add(cacheName);
        this.byClient.delete(clientId);
      }
    }
    if (senderClientId) this.byClient.delete(senderClientId);
    ended.forEach((name) => this.bump(name));
    return [...ended];
  }

  /**
   * Forget clients that are gone (closed tabs, reloaded pages). Returns the names no live client
   * uses any more.
   */
  prune(liveClientIds: ReadonlySet<string>): string[] {
    const before = this.inUse();
    for (const clientId of [...this.byClient.keys()]) {
      if (!liveClientIds.has(clientId)) this.byClient.delete(clientId);
    }
    const after = this.inUse();
    const gone = [...before].filter((name) => !after.has(name));
    gone.forEach((name) => this.bump(name));
    return gone;
  }

  /** Every cache name a registered client uses. */
  inUse(): Set<string> {
    return new Set(this.byClient.values());
  }

  private bump(cacheName: string): void {
    this.generations.set(cacheName, this.generationOf(cacheName) + 1);
  }
}

/**
 * Running byte total per API cache (review finding 9): a write adds its size and subtracts the
 * entry it replaced, so the R-013 ceiling only needs a full scan when the total may exceed it —
 * not one `cache.match` per stored entry on every write. Persisted next to the registry.
 */
export class ByteLedger {
  private readonly totals = new Map<string, number>();

  static fromJSON(value: unknown): ByteLedger {
    const ledger = new ByteLedger();
    if (value && typeof value === 'object') {
      for (const [name, total] of Object.entries(value as Record<string, unknown>)) {
        if (typeof total === 'number' && Number.isFinite(total) && total >= 0) ledger.totals.set(name, total);
      }
    }
    return ledger;
  }

  toJSON(): Record<string, number> {
    return Object.fromEntries(this.totals);
  }

  total(cacheName: string): number {
    return this.totals.get(cacheName) ?? 0;
  }

  /** Record a write (`added` bytes in, `replaced` bytes out); `true` when the ceiling may be exceeded. */
  record(cacheName: string, added: number, replaced: number, maxBytes: number): boolean {
    const next = Math.max(0, this.total(cacheName) + Math.max(0, added) - Math.max(0, replaced));
    this.totals.set(cacheName, next);
    return next > maxBytes;
  }

  /** Replace the estimate with a measured total (after a full scan). */
  set(cacheName: string, total: number): void {
    this.totals.set(cacheName, Math.max(0, total));
  }

  forget(cacheName: string): void {
    this.totals.delete(cacheName);
  }
}
