/**
 * "N entries are not sent yet" before an explicit logout (REQ-053 WP 9.4, G-W9 b): the logout discards the user's
 * unsent entries in every tenant, so the user decides — send now, discard and log out, or cancel. With a
 * connection the dialog starts a sync of the active tenant at once and logs out by itself when nothing is left.
 * A tenant switch does not ask: it keeps the entries for that tenant (UI-NFR-012 R-050/R-051).
 */
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import LinearProgress from '@mui/material/LinearProgress';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import type { CacheScope } from './planCache';
import { syncThenCount } from './sessionChange';
import type { SyncProgress } from './sync';

interface UnsyncedWritesDialogProps {
  userKey: string;
  /** The active tenant's scope (what can be sent now), or `null` without an active tenant. */
  scope: CacheScope | null;
  /** `null` = could not be counted: the text says so instead of a number. */
  count: number | null;
  /** Continue with the logout (which discards what is left). */
  onProceed: () => void;
  onCancel: () => void;
}

export default function UnsyncedWritesDialog({ userKey, scope, count, onProceed, onCancel }: UnsyncedWritesDialogProps) {
  const { t } = useTranslation();
  const online = useOnlineStatus();
  const [left, setLeft] = useState<number | null>(count);
  const [syncing, setSyncing] = useState(false);
  const [progress, setProgress] = useState<SyncProgress | null>(null);
  const proceedRef = useRef(onProceed);
  const startedRef = useRef(false);

  const syncNow = async () => {
    setSyncing(true);
    try {
      const remaining = await syncThenCount(userKey, scope, setProgress);
      setLeft(remaining);
      if (remaining === 0) proceedRef.current();
    } finally {
      setSyncing(false);
      setProgress(null);
    }
  };

  const syncNowRef = useRef(syncNow);
  useEffect(() => {
    proceedRef.current = onProceed;
    syncNowRef.current = syncNow;
  });

  // With a connection, try first: most entries go through and the user is not asked at all.
  const canSync = scope !== null;
  useEffect(() => {
    if (startedRef.current || !online || !canSync) return;
    startedRef.current = true;
    void syncNowRef.current();
  }, [online, canSync]);

  return (
    <Dialog
      open
      onClose={syncing ? undefined : onCancel}
      maxWidth="xs"
      fullWidth
      aria-labelledby="unsynced-writes-title"
      aria-describedby="unsynced-writes-text"
      data-testid="unsynced-writes-dialog"
    >
      <DialogTitle id="unsynced-writes-title">{t('pages.offlineQueue.sessionChange.title')}</DialogTitle>
      <DialogContent>
        <DialogContentText id="unsynced-writes-text" data-testid="unsynced-writes-count">
          {left === null ? t('pages.offlineQueue.sessionChange.textUnknown') : t('pages.offlineQueue.sessionChange.text', { count: left })}
        </DialogContentText>
        {syncing && (
          <LinearProgress
            sx={{ mt: 2 }}
            variant={progress && progress.total > 0 ? 'determinate' : 'indeterminate'}
            value={progress && progress.total > 0 ? (progress.done / progress.total) * 100 : undefined}
            aria-label={t('pages.offlineQueue.sessionChange.syncing')}
          />
        )}
        {!online && (
          <Alert severity="warning" sx={{ mt: 2 }} data-testid="unsynced-writes-offline">
            {t('pages.offlineQueue.sessionChange.offline')}
          </Alert>
        )}
      </DialogContent>
      <DialogActions sx={{ flexWrap: 'wrap', rowGap: 1 }}>
        <Button onClick={onCancel} disabled={syncing} data-testid="unsynced-writes-cancel">
          {t('common.cancel')}
        </Button>
        <Button color="error" onClick={onProceed} disabled={syncing} data-testid="unsynced-writes-discard">
          {t('pages.offlineQueue.sessionChange.discard')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void syncNow()}
          disabled={!online || syncing || scope === null}
          loading={syncing}
          data-testid="unsynced-writes-sync"
        >
          {t('pages.offlineQueue.sessionChange.syncNow')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
