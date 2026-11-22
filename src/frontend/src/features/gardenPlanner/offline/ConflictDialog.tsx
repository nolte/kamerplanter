/**
 * The conflict dialog of the offline write buffer (REQ-053 WP 9.4, UI-NFR-012 R-027…R-032): every buffered entry
 * the sync could not deliver, with what it was, where and when it was captured, and why it did not go through.
 *
 * - A **conflict** (WP 9.3: the id names another request, the task is closed or gone, or what the entry created
 *   was deleted) offers "Keep" and "Discard" (R-032, the simplified kiosk form — field mode is the phone in the
 *   garden). Resending cannot help with any of the four codes, so "Keep" keeps the entry on this device only,
 *   readable here with its text, until it is discarded or the session ends (`queue.ts` `keepEntry`).
 * - A **failed** entry (five attempts, or refused by the server) offers "Try again" (R-027) — with the SAME
 *   `client_event_id` — and "Discard".
 *
 * Big touch targets on request (`touchTarget`, UI-NFR-019); every list row is labelled for screen readers.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import type { CacheScope } from './planCache';
import { MAX_ATTEMPTS, discardEntry, keepEntry, retryEntry } from './queue';
import type { QueueEntry } from './queueTypes';

interface ConflictDialogProps {
  scope: CacheScope;
  /** The entries to show: conflicts and failed ones, oldest first. */
  entries: readonly QueueEntry[];
  /** Entries still waiting to be sent; with a connection the dialog offers to send them now. */
  pendingCount: number;
  online: boolean;
  onSyncNow: () => void;
  onClose: () => void;
  /** Edge of the buttons in px (64 in field mode, GP-UX-020). */
  touchTarget?: number;
}

/** What the entry was, in one line (the subject of its row). */
function useEntrySubject() {
  const { t } = useTranslation();
  return (entry: QueueEntry): string => {
    const { write } = entry;
    switch (write.kind) {
      case 'complete':
        return t('pages.offlineQueue.kind.complete', { task: write.taskName });
      case 'note':
        return t('pages.offlineQueue.kind.note');
      case 'bedPhoto':
        return t('pages.offlineQueue.kind.bedPhoto');
      case 'plantPhoto':
        return t('pages.offlineQueue.kind.plantPhoto', { plant: write.plantName });
    }
  };
}

/** The entry's own text, so a kept entry stays readable on the device. */
function entryText(entry: QueueEntry): string | null {
  const { write } = entry;
  if (write.kind === 'note') return write.body.summary;
  if (write.kind === 'complete') return write.payload.completion_notes ?? null;
  return null;
}

export default function ConflictDialog({
  scope,
  entries,
  pendingCount,
  online,
  onSyncNow,
  onClose,
  touchTarget = 48,
}: ConflictDialogProps) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const subject = useEntrySubject();
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionFailed, setActionFailed] = useState(false);
  const captured = new Intl.DateTimeFormat(i18n.language, { dateStyle: 'medium', timeStyle: 'short' });

  const act = async (id: string, action: (scope: CacheScope, id: string) => Promise<boolean>) => {
    setBusyId(id);
    setActionFailed(false);
    try {
      if (!(await action(scope, id))) setActionFailed(true);
    } finally {
      setBusyId(null);
    }
  };

  const reason = (entry: QueueEntry): string => {
    if (entry.status === 'conflict' && entry.conflictCode) {
      return t(`pages.offlineQueue.conflict.${entry.conflictCode.replace('.', '_')}`);
    }
    if (entry.attempts >= MAX_ATTEMPTS) return t('pages.offlineQueue.failed.attempts');
    return t('pages.offlineQueue.failed.refused', { code: entry.lastErrorCode ?? '—' });
  };

  const buttonSx = { minHeight: touchTarget, minWidth: touchTarget };

  return (
    <Dialog
      open
      onClose={onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="offline-conflict-title"
      aria-describedby="offline-conflict-intro"
      data-testid="offline-conflict-dialog"
    >
      <DialogTitle id="offline-conflict-title">{t('pages.offlineQueue.dialog.title')}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Typography id="offline-conflict-intro" variant="body1">
          {t('pages.offlineQueue.dialog.intro')}
        </Typography>
        {actionFailed && (
          <Alert severity="warning" data-testid="offline-conflict-action-failed">
            {t('pages.offlineQueue.dialog.actionFailed')}
          </Alert>
        )}
        {entries.length === 0 && (
          <Typography variant="body1" data-testid="offline-conflict-empty">
            {t('pages.offlineQueue.dialog.empty')}
          </Typography>
        )}
        <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          {entries.map((entry) => {
            const text = entryText(entry);
            const titleId = `offline-entry-${entry.id}`;
            const busy = busyId === entry.id;
            return (
              <Box
                component="li"
                key={entry.id}
                aria-labelledby={titleId}
                data-testid={`offline-entry-${entry.id}`}
                data-status={entry.status}
                sx={{ border: 2, borderColor: entry.status === 'conflict' ? 'warning.main' : 'error.main', borderRadius: 1, p: 1.5 }}
              >
                <Typography id={titleId} variant="subtitle1" component="h3" sx={{ fontWeight: 700, overflowWrap: 'anywhere' }}>
                  {subject(entry)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('pages.offlineQueue.dialog.where', {
                    bed: entry.bedName,
                    time: captured.format(new Date(entry.capturedAt)),
                  })}
                </Typography>
                {text && (
                  <Typography variant="body1" sx={{ mt: 0.5, whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>
                    {text}
                  </Typography>
                )}
                <Typography variant="body2" sx={{ mt: 0.5 }} data-testid={`offline-entry-reason-${entry.id}`}>
                  {reason(entry)}
                </Typography>
                {entry.kept && (
                  <Chip
                    size="small"
                    variant="outlined"
                    label={t('pages.offlineQueue.dialog.keptChip')}
                    sx={{ mt: 1 }}
                    data-testid={`offline-entry-kept-${entry.id}`}
                  />
                )}
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                  {entry.status === 'conflict' && !entry.kept && (
                    <Button
                      variant="contained"
                      onClick={() => void act(entry.id, keepEntry)}
                      disabled={busy}
                      sx={buttonSx}
                      aria-describedby={titleId}
                      data-testid={`offline-entry-keep-${entry.id}`}
                    >
                      {t('pages.offlineQueue.dialog.keep')}
                    </Button>
                  )}
                  {entry.status === 'failed' && (
                    <Button
                      variant="contained"
                      onClick={() => void act(entry.id, retryEntry).then(onSyncNow)}
                      disabled={busy || !online}
                      sx={buttonSx}
                      aria-describedby={titleId}
                      data-testid={`offline-entry-retry-${entry.id}`}
                    >
                      {t('pages.offlineQueue.dialog.retry')}
                    </Button>
                  )}
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() => void act(entry.id, discardEntry)}
                    disabled={busy}
                    sx={buttonSx}
                    aria-describedby={titleId}
                    data-testid={`offline-entry-discard-${entry.id}`}
                  >
                    {t('pages.offlineQueue.dialog.discard')}
                  </Button>
                </Box>
              </Box>
            );
          })}
        </Box>
        <Typography variant="body2" color="text.secondary">
          {t('pages.offlineQueue.dialog.keepHint')}
        </Typography>
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, pb: 2, flexWrap: 'wrap', rowGap: 1 }}>
        {pendingCount > 0 && (
          <Button onClick={onSyncNow} disabled={!online} sx={buttonSx} data-testid="offline-conflict-sync-now">
            {t('pages.offlineQueue.dialog.syncNow', { count: pendingCount })}
          </Button>
        )}
        <Button variant="contained" onClick={onClose} sx={buttonSx} data-testid="offline-conflict-close">
          {t('common.close')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
