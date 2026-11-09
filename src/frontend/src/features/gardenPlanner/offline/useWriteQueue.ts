/**
 * The offline write buffer of the signed-in user in the active tenant, as React state (REQ-053 WP 9.4): the
 * entries in capture order and the device total (the R-019 capacity). Re-read after every change in this tab, on
 * app focus, and when `version` moves (a caller that knows another tab wrote).
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { CacheScope } from './planCache';
import {
  QUEUE_CAPACITY,
  listEntries,
  onQueueChange,
  preloadWriteQueue,
  totalEntries,
  writeQueueAvailable,
} from './queue';
import type { QueueEntry } from './queueTypes';

export interface WriteQueueState {
  /** The scope's entries, oldest first. */
  entries: QueueEntry[];
  /** Every entry of the user, in all their tenants (the R-019 capacity counts them; other users' never). */
  total: number;
  /** The buffer holds {@link QUEUE_CAPACITY} entries: nothing more is taken in (R-019). */
  full: boolean;
  /** Buffering is possible in this tab (IndexedDB, kill switch on, not retired). */
  available: boolean;
  reload: () => void;
}

const NO_ENTRIES: QueueEntry[] = [];

export function useWriteQueue(scope: CacheScope | null): WriteQueueState {
  const [snapshot, setSnapshot] = useState<{ key: string; entries: QueueEntry[]; total: number } | null>(null);
  const [tick, setTick] = useState(0);
  const userKey = scope?.userKey ?? null;
  const tenantKey = scope?.tenantKey ?? null;
  const key = userKey !== null && tenantKey !== null ? `${userKey}\u0000${tenantKey}` : null;

  const reload = useCallback(() => setTick((value) => value + 1), []);

  useEffect(() => onQueueChange(reload), [reload]);
  // The first offline capture must not need a chunk download (see `preloadWriteQueue`).
  useEffect(() => {
    if (key !== null) void preloadWriteQueue();
  }, [key]);
  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === 'visible') reload();
    };
    window.addEventListener('focus', reload);
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      window.removeEventListener('focus', reload);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [reload]);

  useEffect(() => {
    if (key === null || userKey === null || tenantKey === null) return undefined;
    let cancelled = false;
    void Promise.all([listEntries({ userKey, tenantKey }), totalEntries(userKey)]).then(([entries, total]) => {
      if (!cancelled) setSnapshot({ key, entries, total });
    });
    return () => {
      cancelled = true;
    };
  }, [key, userKey, tenantKey, tick]);

  // Only the snapshot of the CURRENT scope is ever shown: another account's or tenant's entries never leak in.
  const current = snapshot !== null && snapshot.key === key ? snapshot : null;
  const entries = current?.entries ?? NO_ENTRIES;
  const total = current?.total ?? 0;
  const available = writeQueueAvailable();
  return useMemo(
    () => ({ entries, total, full: total >= QUEUE_CAPACITY, available, reload }),
    [entries, total, available, reload],
  );
}
