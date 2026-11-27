import { useEffect, useState, type ComponentType } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import CloudOffIcon from '@mui/icons-material/CloudOff';
import { visuallyHidden } from '@mui/utils';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { captureHandledError } from '@/observability/errorTracking';
import type { ConnectivityNoticesProps } from '@/components/layout/ConnectivityNotices';

type NoticesModule = { default: ComponentType<ConnectivityNoticesProps> };

// #3025 N-39 — the change snackbars (R-036/R-037) are their own chunk; the indicator stays in the first paint.
function loadConnectivityNotices(): Promise<NoticesModule> {
  return import('@/components/layout/ConnectivityNotices');
}

/**
 * Load the notices chunk, and keep trying: a chunk that fails (the app started offline before it was cached,
 * a deploy in between) renders nothing instead of throwing into the shell's error boundary, and is fetched
 * again on the next `online` event. `React.lazy` would memoise the failure for the whole session, so the
 * snackbars — "online again" included — would never appear before a reload. A chunk that arrives with the
 * reconnect announces that reconnect itself (`announceCurrentState`).
 */
function useNoticesChunk(load: () => Promise<NoticesModule>) {
  const [notices, setNotices] = useState<{ Component: NoticesModule['default']; announce: boolean } | null>(null);
  useEffect(() => {
    let alive = true;
    let loaded = false;
    const attempt = (announce: boolean) => {
      load()
        .then((mod) => {
          if (!alive || loaded) return;
          loaded = true;
          window.removeEventListener('online', onOnline);
          setNotices({ Component: mod.default, announce });
        })
        .catch((err: unknown) => {
          // Reported, then retried on the next `online` event.
          captureHandledError(err, { source: 'ConnectivityIndicator.noticesChunk' });
        });
    };
    const onOnline = () => attempt(true);
    window.addEventListener('online', onOnline);
    attempt(false);
    return () => {
      alive = false;
      window.removeEventListener('online', onOnline);
    };
  }, [load]);
  return notices;
}

export interface ConnectivityIndicatorProps {
  /** Test seam: how the notices chunk is fetched. Production uses the dynamic import. */
  loadNotices?: () => Promise<NoticesModule>;
}

/**
 * The permanent connectivity indicator of the app shell (UI-NFR-012 R-033–R-035, REQ-053 WP 9.1):
 * a green dot while online, an orange "Offline" chip while offline.
 *
 * ONE live region that stays mounted; only its content changes. A screen reader announces a change
 * of content inside an existing `role="status"` region — a region that is itself swapped for a new
 * element is a new region, and the change to "Offline" would go unannounced.
 *
 * It also mounts the snackbar on a change of state (R-036/R-037, `ConnectivityNotices`): each shell mounts
 * this indicator exactly once, so it is the one place that sees every change once.
 */
export default function ConnectivityIndicator({
  loadNotices = loadConnectivityNotices,
}: ConnectivityIndicatorProps = {}) {
  const { t } = useTranslation();
  const online = useOnlineStatus();
  const notices = useNoticesChunk(loadNotices);

  return (
    <>
      <Box
        role="status"
        aria-live="polite"
        data-testid="connectivity-indicator"
        data-online={online ? 'true' : 'false'}
        sx={{ display: 'inline-flex', alignItems: 'center', mr: { xs: 0.5, sm: 1 }, flexShrink: 0 }}
      >
        {online ? (
          <Tooltip title={t('common.pwa.onlineHint')}>
            <Box
              tabIndex={0}
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 20,
                height: 20,
                borderRadius: '50%',
                bgcolor: 'background.paper',
              }}
            >
              <Box aria-hidden sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: 'success.main' }} />
              <Box component="span" sx={visuallyHidden}>
                {t('common.pwa.online')}
              </Box>
            </Box>
          </Tooltip>
        ) : (
          <Tooltip title={t('common.pwa.offlineHint')}>
            <Chip
              icon={<CloudOffIcon />}
              label={t('common.pwa.offline')}
              color="warning"
              size="small"
              tabIndex={0}
              // #2815: below sm the chip shows its icon alone; the text is only visually hidden, so the live region
              // still announces "Offline".
              sx={(theme) => ({
                fontWeight: 600,
                '& .MuiChip-label': { [theme.breakpoints.down('sm')]: visuallyHidden },
                '& .MuiChip-icon': { [theme.breakpoints.down('sm')]: { mr: 0.5 } },
              })}
            />
          </Tooltip>
        )}
      </Box>
      {notices && <notices.Component announceCurrentState={notices.announce} />}
    </>
  );
}
