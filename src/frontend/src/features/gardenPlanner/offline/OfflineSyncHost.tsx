/**
 * The app-wide host of the offline write buffer (REQ-053 WP 9.4, UI-NFR-012 R-021…R-027, R-052): mounted once in
 * the app bar (`layouts/MainLayout.tsx`, lazy), so a buffered entry is sent wherever the user is when the
 * connection comes back — not only in field mode.
 *
 * - Triggers a FIFO sync (`sync.ts`) when the connection returns (`online`), on app focus, when the worker relays a
 *   Background Sync (where the browser has it), at start and after a new entry while online.
 * - Shows the progress while it runs (R-024, "3/12"), a snackbar when it is done (R-025), and opens the conflict
 *   dialog for every new conflict (R-028). A chip in the app bar names the entries not yet sent and opens the
 *   dialog (failed ones, kept conflicts, "send now").
 * - Mirrors connectivity, counts, progress and the last sync time into `offlineSlice` (R-052).
 *
 * Renders nothing while the buffer is empty.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Chip from '@mui/material/Chip';
import Snackbar from '@mui/material/Snackbar';
import SnackbarContent from '@mui/material/SnackbarContent';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { useNotification } from '@/hooks/useNotification';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { SW_MESSAGE_SYNC_NOW } from '@/pwa/cachePolicy';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  connectivityChanged,
  queueCountsChanged,
  syncProgressed,
  syncSucceeded,
  unsyncedCount,
} from '@/store/slices/offlineSlice';
import ConflictDialog from './ConflictDialog';
import type { CacheScope } from './planCache';
import { countEntries, onQueueChange, takePurgedCount } from './queue';
import { createSyncScheduler, type SyncResult } from './sync';
import { useCacheScope } from './useCacheScope';
import { useWriteQueue } from './useWriteQueue';

export default function OfflineSyncHost() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const online = useOnlineStatus();
  const scope = useCacheScope();
  const queue = useWriteQueue(scope);
  // Optional read: a store without the slice (an isolated test store) shows no progress instead of crashing.
  const progress = useAppSelector((state) => state.offline?.progress ?? null);
  const [manualOpen, setManualOpen] = useState(false);
  const [seenConflicts, setSeenConflicts] = useState<ReadonlySet<string>>(() => new Set());

  const finishRef = useRef<(result: SyncResult) => void>(() => undefined);
  useEffect(() => {
    finishRef.current = (result) => {
      dispatch(syncProgressed(null));
      if (result.sent > 0) {
        dispatch(syncSucceeded(Date.now()));
        notification.success(t('pages.offlineQueue.synced', { count: result.sent }));
      }
      if (result.failed > 0) notification.warning(t('pages.offlineQueue.failedNotice', { count: result.failed }));
    };
  });

  /** "Sync now" of the current scope's scheduler (set by the effect below). */
  const requestRef = useRef<() => void>(() => undefined);
  const scopeKey = scope ? `${scope.userKey}\u0000${scope.tenantKey}` : null;
  const userKey = scope?.userKey ?? null;
  const tenantKey = scope?.tenantKey ?? null;

  // One scheduler per scope: a new user or tenant disposes the old one, and its running sync stops at the next
  // entry (its scope reads `null` from then on).
  useEffect(() => {
    if (userKey === null || tenantKey === null) return undefined;
    let alive = true;
    const own: CacheScope = { userKey, tenantKey };
    const scheduler = createSyncScheduler({
      getScope: () => (alive ? own : null),
      onProgress: (value) => dispatch(syncProgressed(value.total > 0 ? value : null)),
      onFinish: (result) => finishRef.current(result),
    });
    const request = () => {
      if (navigator.onLine !== false) void scheduler.request();
    };
    requestRef.current = request;
    // App focus and the worker's Background Sync relay (R-022).
    const onVisible = () => {
      if (document.visibilityState === 'visible') request();
    };
    const onWorkerMessage = (event: MessageEvent) => {
      if ((event.data as { type?: unknown } | null)?.type === SW_MESSAGE_SYNC_NOW) request();
    };
    window.addEventListener('focus', request);
    document.addEventListener('visibilitychange', onVisible);
    const container = typeof navigator !== 'undefined' ? navigator.serviceWorker : undefined;
    container?.addEventListener('message', onWorkerMessage);
    return () => {
      alive = false;
      scheduler.dispose();
      requestRef.current = () => undefined;
      window.removeEventListener('focus', request);
      document.removeEventListener('visibilitychange', onVisible);
      container?.removeEventListener('message', onWorkerMessage);
    };
  }, [dispatch, userKey, tenantKey]);

  // R-056: entries the retention purge deleted (at app start or before a sync) are named, never dropped silently.
  useEffect(() => {
    if (userKey === null) return undefined;
    const announce = () => {
      const purged = takePurgedCount(userKey);
      if (purged > 0) notification.warning(t('pages.offlineQueue.purged', { count: purged }));
    };
    announce();
    return onQueueChange(announce);
  }, [userKey, notification, t]);

  const counts = useMemo(() => countEntries(queue.entries), [queue.entries]);
  useEffect(() => {
    dispatch(queueCountsChanged({ ...counts, total: queue.total }));
  }, [dispatch, counts, queue.total]);
  useEffect(() => {
    dispatch(connectivityChanged(online));
  }, [dispatch, online]);

  // R-021: back online, a new entry while online, a new scope — send what waits.
  const pending = counts.pending;
  useEffect(() => {
    if (online && pending > 0 && scopeKey !== null) requestRef.current();
  }, [online, pending, scopeKey]);

  const attention = useMemo(
    () => queue.entries.filter((entry) => entry.status === 'conflict' || entry.status === 'failed'),
    [queue.entries],
  );
  // R-028: a new conflict opens the dialog; closing it marks every shown conflict as seen, so a kept or already
  // shown one does not reopen it.
  const freshConflict = attention.some(
    (entry) => entry.status === 'conflict' && !entry.kept && !seenConflicts.has(entry.id),
  );
  const dialogOpen = manualOpen || freshConflict;
  const closeDialog = () => {
    setSeenConflicts((current) => new Set([...current, ...attention.map((entry) => entry.id)]));
    setManualOpen(false);
  };

  const unsynced = unsyncedCount(counts);
  if (scope === null) return null;

  return (
    <>
      {unsynced > 0 && (
        <Chip
          icon={<CloudUploadIcon />}
          label={t('pages.offlineQueue.chip', { count: unsynced })}
          color={counts.failed + counts.conflict > 0 ? 'warning' : 'default'}
          onClick={() => setManualOpen(true)}
          size="small"
          sx={{ mr: 1, fontWeight: 600, bgcolor: counts.failed + counts.conflict > 0 ? undefined : 'background.paper' }}
          data-testid="offline-queue-chip"
        />
      )}
      <Snackbar open={progress !== null} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <SnackbarContent
          role="status"
          aria-live="polite"
          message={progress ? t('pages.offlineQueue.progress', { done: progress.done, total: progress.total }) : ''}
          data-testid="offline-sync-progress"
        />
      </Snackbar>
      {dialogOpen && (
        <ConflictDialog
          scope={scope}
          entries={attention}
          pendingCount={counts.pending}
          online={online}
          onSyncNow={() => requestRef.current()}
          onClose={closeDialog}
        />
      )}
    </>
  );
}
